"""Agents section service — CRUD for Custom GitHub Agent configurations.

Available agents are sourced from the GitHub repository default branch under
``.github/agents/*.agent.md``. SQLite stores only local workflow metadata for
unmerged PRs and deletion bookkeeping.
"""

from __future__ import annotations

import json
import logging
import re
import time
import uuid

import aiosqlite
import yaml

from src.constants import CACHE_PREFIX_REPO_AGENTS
from src.models.agent_creator import AgentPreview
from src.models.agents import (
    Agent,
    AgentChatResponse,
    AgentCreate,
    AgentCreateResult,
    AgentDeleteResult,
    AgentPendingCleanupResult,
    AgentPreviewResponse,
    AgentSource,
    AgentStatus,
    AgentUpdate,
)
from src.services.agent_creator import generate_config_files, generate_issue_body
from src.services.cache import cache, get_cache_key
from src.services.github_commit_workflow import commit_files_workflow
from src.services.github_projects import github_projects_service
from src.utils import utcnow

logger = logging.getLogger(__name__)

# ── YAML frontmatter regex ──────────────────────────────────────────────
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)

# ── Chat sessions (bounded) ─────────────────────────────────────────────
_MAX_CHAT_SESSIONS = 200
_SESSION_TTL_SECONDS = 30 * 60  # 30 minutes
_chat_sessions: dict[str, list[dict]] = {}
_chat_session_timestamps: dict[str, float] = {}


def _prune_expired_sessions() -> None:
    """Remove chat sessions that have exceeded the TTL."""
    now = time.monotonic()
    expired = [
        sid for sid, ts in _chat_session_timestamps.items() if now - ts > _SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _chat_sessions.pop(sid, None)
        _chat_session_timestamps.pop(sid, None)


class AgentsService:
    """Business logic for the Agents section."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    # ── List ──────────────────────────────────────────────────────────────

    async def list_agents(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        access_token: str,
    ) -> list[Agent]:
        """List agents from the repo default branch, with a long-lived cache."""
        cache_key = get_cache_key(CACHE_PREFIX_REPO_AGENTS, f"{owner}/{repo}")

        cached_agents = cache.get(cache_key)
        if isinstance(cached_agents, list):
            await self._cleanup_resolved_pending_agents(
                project_id=project_id,
                repo_agents=cached_agents,
            )
            return sorted(cached_agents, key=lambda a: a.name.lower())

        repo_agents, repo_available = await self._list_repo_agents(
            owner=owner,
            repo=repo,
            access_token=access_token,
        )

        if repo_available:
            cache.set(cache_key, repo_agents, ttl_seconds=900)
            await self._cleanup_resolved_pending_agents(
                project_id=project_id,
                repo_agents=repo_agents,
            )
            return sorted(repo_agents, key=lambda a: a.name.lower())

        stale_agents = cache.get_stale(cache_key)
        if isinstance(stale_agents, list):
            await self._cleanup_resolved_pending_agents(
                project_id=project_id,
                repo_agents=stale_agents,
            )
            return sorted(stale_agents, key=lambda a: a.name.lower())

        return []

    async def list_pending_agents(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        access_token: str,
    ) -> list[Agent]:
        """List local agent PR work that has not yet been reconciled with main."""
        repo_agents = await self.list_agents(
            project_id=project_id,
            owner=owner,
            repo=repo,
            access_token=access_token,
        )
        await self._cleanup_resolved_pending_agents(
            project_id=project_id,
            repo_agents=repo_agents,
        )

        local_agents = await self._list_local_agents(project_id)
        pending_agents = [agent for agent in local_agents if agent.status != AgentStatus.ACTIVE]
        return sorted(
            pending_agents,
            key=lambda agent: (agent.created_at or "", agent.name.lower()),
            reverse=True,
        )

    async def purge_pending_agents(self, *, project_id: str) -> AgentPendingCleanupResult:
        """Delete all non-active local agent workflow rows for a project."""
        local_agents = await self._list_local_agents(project_id)
        deleted_ids = [agent.id for agent in local_agents if agent.status != AgentStatus.ACTIVE]

        if deleted_ids:
            await self._db.executemany(
                "DELETE FROM agent_configs WHERE id = ?",
                [(agent_id,) for agent_id in deleted_ids],
            )
            await self._db.commit()

        return AgentPendingCleanupResult(deleted_count=len(deleted_ids))

    async def _list_local_agents(self, project_id: str) -> list[Agent]:
        """Query agents from SQLite ``agent_configs`` table."""
        cursor = await self._db.execute(
            "SELECT * FROM agent_configs WHERE project_id = ? ORDER BY name",
            (project_id,),
        )
        rows = await cursor.fetchall()
        agents: list[Agent] = []
        for row in rows:
            r = (
                dict(row)
                if isinstance(row, dict)
                else dict(zip([d[0] for d in cursor.description], row, strict=False))
            )
            tools = []
            try:
                tools = json.loads(r.get("tools", "[]"))
            except (json.JSONDecodeError, TypeError):
                pass

            status = self._coerce_agent_status(r.get("lifecycle_status"))

            agents.append(
                Agent(
                    id=r["id"],
                    name=r["name"],
                    slug=r["slug"],
                    description=r["description"],
                    system_prompt=r.get("system_prompt", ""),
                    status=status,
                    tools=tools,
                    status_column=r.get("status_column") or None,
                    github_issue_number=r.get("github_issue_number"),
                    github_pr_number=r.get("github_pr_number"),
                    branch_name=r.get("branch_name"),
                    source=AgentSource.LOCAL,
                    created_at=r.get("created_at"),
                )
            )
        return agents

    async def _list_repo_agents(
        self,
        *,
        owner: str,
        repo: str,
        access_token: str,
    ) -> tuple[list[Agent], bool]:
        """Read ``.github/agents/*.agent.md`` from the GitHub repo."""
        try:
            tree_entries = await github_projects_service.get_directory_contents(
                access_token=access_token,
                owner=owner,
                repo=repo,
                path=".github/agents",
            )
        except Exception:
            logger.debug("Could not read .github/agents/ from %s/%s", owner, repo)
            return [], False

        agents: list[Agent] = []
        for entry in tree_entries:
            name = entry.get("name", "")
            if not name.endswith(".agent.md"):
                continue

            slug = name.removesuffix(".agent.md")
            content = entry.get("content", "")
            if not content:
                # Fetch content individually
                try:
                    file_data = await github_projects_service.get_file_content(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        path=f".github/agents/{name}",
                    )
                    content = file_data.get("content", "") if file_data else ""
                except Exception:
                    content = ""

            # Parse YAML frontmatter
            description = ""
            tools: list[str] = []
            system_prompt = ""
            agent_name: str | None = None

            match = _FRONTMATTER_RE.match(content)
            if match:
                try:
                    fm = yaml.safe_load(match.group(1))
                    if isinstance(fm, dict):
                        description = fm.get("description", "")
                        agent_name = fm.get("name")
                        raw_tools = fm.get("tools", [])
                        if isinstance(raw_tools, list):
                            tools = [str(t) for t in raw_tools]
                except yaml.YAMLError:
                    pass
                system_prompt = match.group(2).strip()
            else:
                system_prompt = content.strip()

            display_name = slug.replace("-", " ").replace("_", " ").title()

            agents.append(
                Agent(
                    id=f"repo:{slug}",
                    name=agent_name or display_name,
                    slug=slug,
                    description=description,
                    system_prompt=system_prompt,
                    status=AgentStatus.ACTIVE,
                    tools=tools,
                    status_column=None,
                    github_issue_number=None,
                    github_pr_number=None,
                    branch_name=None,
                    source=AgentSource.REPO,
                    created_at=None,
                )
            )

        return agents, True

    # ── Create ────────────────────────────────────────────────────────────

    async def create_agent(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        body: AgentCreate,
        access_token: str,
        github_user_id: str,
    ) -> AgentCreateResult:
        """Create a new agent — validate, commit files, open PR, save to DB."""
        # Validate name & generate slug
        slug = AgentPreview.name_to_slug(body.name)
        if not slug:
            raise ValueError("Agent name produces an empty slug")

        # Validate filename characters
        if not re.match(r"^[a-z0-9][a-z0-9._-]*$", slug):
            raise ValueError(f"Invalid agent slug '{slug}'. Only a-z, 0-9, '.', '-', '_' allowed.")

        # Check for duplicates (SQLite)
        cursor = await self._db.execute(
            "SELECT id FROM agent_configs WHERE slug = ? AND project_id = ?",
            (slug, project_id),
        )
        if await cursor.fetchone():
            raise ValueError(f"An agent with slug '{slug}' already exists in this project.")

        # Check for duplicates in the repo (.github/agents/<slug>.agent.md)
        try:
            existing_file = await github_projects_service.get_file_content(
                access_token=access_token,
                owner=owner,
                repo=repo,
                path=f".github/agents/{slug}.agent.md",
            )
            if existing_file:
                raise ValueError(
                    f"An agent file '.github/agents/{slug}.agent.md' already exists in the repository."
                )
        except ValueError:
            raise  # Re-raise our own validation error
        except Exception:
            pass  # File not found or API error — safe to proceed

        description = body.description
        tools = list(body.tools)
        system_prompt = body.system_prompt

        # When raw mode is OFF, use AI to:
        # 1. Enhance the system prompt into a robust, well-structured agent definition
        # 2. Auto-generate description and tools from the enhanced prompt
        if not body.raw:
            try:
                enhanced = await self._enhance_agent_content(
                    name=body.name,
                    system_prompt=body.system_prompt,
                    owner=owner,
                    repo=repo,
                    access_token=access_token,
                )
                system_prompt = enhanced.get("system_prompt", body.system_prompt)
                if not description:
                    description = enhanced.get("description", body.name)
                if not tools:
                    tools = enhanced.get("tools", [])
            except Exception as exc:
                logger.warning("AI content enhancement failed, using original input: %s", exc)
                system_prompt = body.system_prompt
                if not description:
                    description = body.name
                if not tools:
                    tools = []
        else:
            # Raw mode — use content exactly as provided
            if not description:
                description = body.name

        # Ensure description is never empty for the file
        if not description:
            description = body.name

        # Build preview
        preview = AgentPreview(
            name=body.name,
            slug=slug,
            description=description,
            system_prompt=system_prompt,
            status_column=body.status_column,
            tools=tools,
        )

        # Generate files
        files = generate_config_files(preview)

        # Generate rich AI descriptions for Issue and PR (unless raw mode)
        if not body.raw:
            try:
                rich = await self._generate_rich_descriptions(
                    name=body.name,
                    slug=slug,
                    description=description,
                    system_prompt=system_prompt,
                    tools=tools,
                    access_token=access_token,
                )
                issue_body_md = rich["issue_body"]
                pr_body = rich["pr_body"]
            except Exception as exc:
                logger.warning("AI description generation failed, using defaults: %s", exc)
                issue_body_md = generate_issue_body(preview)
                pr_body = self._default_pr_body(preview, slug)
        else:
            issue_body_md = generate_issue_body(preview)
            pr_body = self._default_pr_body(preview, slug)

        branch_name = f"agent/{slug}"

        # Execute commit workflow
        result = await commit_files_workflow(
            access_token=access_token,
            owner=owner,
            repo=repo,
            branch_name=branch_name,
            files=files,
            commit_message=f"Add agent: {preview.name}",
            pr_title=f"Add agent: {preview.name}",
            pr_body=pr_body,
            issue_title=f"Agent Config: {preview.name}",
            issue_body=issue_body_md,
            issue_labels=["agent-config"],
            project_id=project_id,
            target_status="In Review",
        )

        if not result.success:
            raise RuntimeError(f"Agent creation pipeline failed: {'; '.join(result.errors)}")

        # Save to SQLite
        agent_id = str(uuid.uuid4())
        tools_json = json.dumps(tools)
        now = utcnow().isoformat()

        await self._db.execute(
            """INSERT INTO agent_configs
               (id, name, slug, description, system_prompt, status_column,
                tools, project_id, owner, repo, created_by,
                github_issue_number, github_pr_number, branch_name, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_id,
                body.name,
                slug,
                description,
                system_prompt,
                body.status_column,
                tools_json,
                project_id,
                owner,
                repo,
                github_user_id,
                result.issue_number,
                result.pr_number,
                branch_name,
                now,
            ),
        )
        await self._db.commit()

        agent = Agent(
            id=agent_id,
            name=body.name,
            slug=slug,
            description=description,
            system_prompt=system_prompt,
            status=AgentStatus.PENDING_PR,
            tools=tools,
            status_column=body.status_column or None,
            github_issue_number=result.issue_number,
            github_pr_number=result.pr_number,
            branch_name=branch_name,
            source=AgentSource.LOCAL,
            created_at=now,
        )

        return AgentCreateResult(
            agent=agent,
            pr_url=result.pr_url or "",
            pr_number=result.pr_number or 0,
            issue_number=result.issue_number,
            branch_name=branch_name,
        )

    # ── Delete ────────────────────────────────────────────────────────────

    async def delete_agent(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        agent_id: str,
        access_token: str,
        github_user_id: str,
    ) -> AgentDeleteResult:
        """Delete agent — open PR to remove repo files and mark pending deletion."""
        # Resolve the agent
        agent = await self._resolve_listed_agent(
            project_id=project_id,
            owner=owner,
            repo=repo,
            access_token=access_token,
            agent_id=agent_id,
        )
        if not agent:
            raise LookupError(f"Agent '{agent_id}' not found")

        if agent.status == AgentStatus.PENDING_DELETION:
            raise ValueError(f"Agent '{agent.name}' is already pending deletion")

        slug = agent.slug
        branch_name = f"agent/delete-{slug}"

        pr_body = (
            f"## Remove Agent: {agent.name}\n\n"
            f"Removes the agent configuration files:\n"
            f"- `.github/agents/{slug}.agent.md`\n"
            f"- `.github/prompts/{slug}.prompt.md`\n"
        )

        issue_body_md = (
            f"# Remove Agent: {agent.name}\n\n"
            f"**Slug:** `{slug}`\n"
            f"**Description:** {agent.description}\n\n"
            "---\n"
            "*This issue was automatically generated by the Agents section.*"
        )

        # For deletion, we create a commit that removes the files.
        # The commit_files_workflow adds files — for deletion we need
        # to create a commit with empty files (the GitHubProjectsService
        # handles deletions via its createCommitOnBranch mutation).
        # We'll create the files with empty content as a signal, but
        # actually we should just commit an empty set and use
        # the deletion mechanism. For simplicity, let's use the commit
        # workflow with the PR and handle file deletion differently.

        # Create branch + PR with deletion commit
        result = await commit_files_workflow(
            access_token=access_token,
            owner=owner,
            repo=repo,
            branch_name=branch_name,
            files=[],
            delete_files=[
                f".github/agents/{slug}.agent.md",
                f".github/prompts/{slug}.prompt.md",
            ],
            commit_message=f"Remove agent: {agent.name}",
            pr_title=f"Remove agent: {agent.name}",
            pr_body=pr_body,
            issue_title=f"Remove Agent: {agent.name}",
            issue_body=issue_body_md,
            issue_labels=["agent-config"],
        )

        if not result.success:
            raise RuntimeError(f"Agent deletion pipeline failed: {'; '.join(result.errors)}")

        await self._mark_agent_pending_deletion(
            project_id=project_id,
            owner=owner,
            repo=repo,
            github_user_id=github_user_id,
            agent=agent,
            pr_number=result.pr_number,
            issue_number=result.issue_number,
            branch_name=branch_name,
        )

        return AgentDeleteResult(
            success=True,
            pr_url=result.pr_url or "",
            pr_number=result.pr_number or 0,
            issue_number=result.issue_number,
        )

    # ── Update (P3) ──────────────────────────────────────────────────────

    async def update_agent(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        agent_id: str,
        body: AgentUpdate,
        access_token: str,
        github_user_id: str,
    ) -> AgentCreateResult:
        """Update agent config — open PR with updated files."""
        agent = await self._resolve_agent(project_id, agent_id)
        if not agent:
            raise LookupError(f"Agent '{agent_id}' not found")

        # Repo-only agents cannot be updated via the API
        if agent.id.startswith("repo:"):
            raise ValueError(
                "Repo-only agents cannot be updated through the API. "
                "Edit the .agent.md file directly in the repository."
            )

        if agent.status == AgentStatus.PENDING_DELETION:
            raise ValueError(
                "Agents pending deletion cannot be updated until the deletion PR is resolved."
            )

        # Apply updates
        name = body.name or agent.name
        description = body.description or agent.description
        system_prompt = body.system_prompt or agent.system_prompt
        tools = body.tools if body.tools is not None else agent.tools

        slug = AgentPreview.name_to_slug(name)

        # Validate slug: non-empty and filename-safe
        if not slug or not re.match(r"^[a-z0-9][a-z0-9._-]*$", slug):
            raise ValueError(f"Invalid agent slug derived from name '{name}': '{slug}'")

        # Ensure no other agent in SQLite uses this slug (conflict check)
        async with self._db.execute(
            "SELECT id FROM agent_configs WHERE project_id = ? AND slug = ? AND id != ?",
            (project_id, slug, agent.id),
        ) as cursor:
            if await cursor.fetchone():
                raise ValueError(f"An agent with slug '{slug}' already exists for this project.")

        preview = AgentPreview(
            name=name,
            slug=slug,
            description=description,
            system_prompt=system_prompt,
            status_column=agent.status_column or "",
            tools=tools,
        )

        files = generate_config_files(preview)
        branch_name = f"agent/update-{slug}"

        pr_body = (
            f"## Update Agent: {name}\n\n"
            f"{description}\n\n"
            f"**Files:**\n"
            f"- `.github/agents/{slug}.agent.md`\n"
            f"- `.github/prompts/{slug}.prompt.md`\n"
        )

        result = await commit_files_workflow(
            access_token=access_token,
            owner=owner,
            repo=repo,
            branch_name=branch_name,
            files=files,
            commit_message=f"Update agent: {name}",
            pr_title=f"Update agent: {name}",
            pr_body=pr_body,
        )

        if not result.success:
            raise RuntimeError(f"Agent update pipeline failed: {'; '.join(result.errors)}")

        # Update SQLite if exists
        if not agent.id.startswith("repo:"):
            tools_json = json.dumps(tools)
            await self._db.execute(
                """UPDATE agent_configs
                   SET name = ?, slug = ?, description = ?, system_prompt = ?,
                       tools = ?, github_pr_number = ?, branch_name = ?
                   WHERE id = ?""",
                (
                    name,
                    slug,
                    description,
                    system_prompt,
                    tools_json,
                    result.pr_number,
                    branch_name,
                    agent.id,
                ),
            )
            await self._db.commit()

        updated_agent = Agent(
            id=agent.id,
            name=name,
            slug=slug,
            description=description,
            system_prompt=system_prompt,
            status=agent.status,
            tools=tools,
            status_column=agent.status_column,
            github_issue_number=agent.github_issue_number,
            github_pr_number=result.pr_number,
            branch_name=branch_name,
            source=agent.source,
            created_at=agent.created_at,
        )

        return AgentCreateResult(
            agent=updated_agent,
            pr_url=result.pr_url or "",
            pr_number=result.pr_number or 0,
            issue_number=result.issue_number,
            branch_name=branch_name,
        )

    # ── Chat ──────────────────────────────────────────────────────────────

    async def chat(
        self,
        *,
        project_id: str,
        message: str,
        session_id: str | None,
        access_token: str,
    ) -> AgentChatResponse:
        """Multi-turn chat for sparse-to-rich agent content refinement."""
        from src.services.ai_agent import get_ai_agent_service

        ai_service = get_ai_agent_service()

        # Prune expired sessions before accessing
        _prune_expired_sessions()

        # Enforce max session limit
        sid = session_id or str(uuid.uuid4())
        if sid not in _chat_sessions and len(_chat_sessions) >= _MAX_CHAT_SESSIONS:
            # Evict the oldest session
            oldest = min(_chat_session_timestamps, key=_chat_session_timestamps.get)  # type: ignore[arg-type]
            _chat_sessions.pop(oldest, None)
            _chat_session_timestamps.pop(oldest, None)

        history = _chat_sessions.get(sid, [])

        if not history:
            # First message — system prompt for agent creation guidance
            history.append(
                {
                    "role": "system",
                    "content": (
                        "You are an assistant helping create a Custom GitHub Agent configuration. "
                        "The user will provide a brief description. Ask clarifying questions to "
                        "understand: 1) What the agent should do, 2) What tools it needs, "
                        "3) Any specific instructions for the system prompt. "
                        "After gathering enough information (usually 2-3 questions), generate a "
                        "complete agent configuration with fields: name, description, tools, "
                        "and system_prompt. Return the configuration as a JSON block marked with "
                        "```agent-config``` fences when ready."
                    ),
                }
            )

        history.append({"role": "user", "content": message})

        try:
            response = await ai_service._call_completion(
                messages=history,
                github_token=access_token,
                max_tokens=2000,
            )
        except Exception as exc:
            logger.error("Agent chat completion failed: %s", exc)
            raise

        reply = response if isinstance(response, str) else str(response)
        history.append({"role": "assistant", "content": reply})
        _chat_sessions[sid] = history
        _chat_session_timestamps[sid] = time.monotonic()

        # Check if the response contains a complete agent config
        preview = self._extract_agent_preview(reply)
        is_complete = preview is not None

        # Clean up session if complete
        if is_complete:
            _chat_sessions.pop(sid, None)
            _chat_session_timestamps.pop(sid, None)

        return AgentChatResponse(
            reply=reply,
            session_id=sid,
            is_complete=is_complete,
            preview=AgentPreviewResponse(
                name=preview.name,
                slug=preview.slug,
                description=preview.description,
                system_prompt=preview.system_prompt,
                status_column=preview.status_column,
                tools=preview.tools,
            )
            if preview
            else None,
        )

    @staticmethod
    def _extract_agent_preview(text: str) -> AgentPreview | None:
        """Try to extract an agent config JSON from the AI response."""
        pattern = re.compile(r"```agent-config\s*\n(.*?)```", re.DOTALL)
        match = pattern.search(text)
        if not match:
            return None

        try:
            config = json.loads(match.group(1))
            name = config.get("name", "")
            if not name:
                return None
            slug = AgentPreview.name_to_slug(name)
            return AgentPreview(
                name=name,
                slug=slug,
                description=config.get("description", ""),
                system_prompt=config.get("system_prompt", ""),
                status_column=config.get("status_column", ""),
                tools=config.get("tools", []),
            )
        except (json.JSONDecodeError, KeyError):
            return None

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _enhance_agent_content(
        self,
        *,
        name: str,
        system_prompt: str,
        owner: str,
        repo: str,
        access_token: str,
    ) -> dict:
        """Use AI to enhance user input into a robust, well-structured agent definition.

        Reads existing agents from the repo as style references. Generates an enhanced
        system prompt, a description, and a tools list.

        Returns ``{"system_prompt": str, "description": str, "tools": list[str]}``.
        """
        from src.services.ai_agent import get_ai_agent_service

        ai_service = get_ai_agent_service()

        # Gather examples from existing agents in the repo
        examples = await self._gather_agent_examples(owner, repo, access_token)

        examples_section = ""
        if examples:
            examples_section = (
                "\n\n## Reference — existing agents in this repository (use as style guide):\n\n"
                + "\n---\n".join(examples[:3])  # Include up to 3 examples
            )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert at writing Custom GitHub Agent definitions. "
                    "The user will provide a name and a rough system prompt. Your job is to "
                    "transform their input into a professional, comprehensive agent definition.\n\n"
                    "Respond with ONLY a JSON object (no markdown fences, no explanation) with exactly three keys:\n\n"
                    '  "system_prompt": The enhanced, well-structured system prompt (markdown). Guidelines:\n'
                    "    - Start with a clear role statement: 'You are a [role] specializing in [domain].'\n"
                    "    - Add a structured workflow with numbered steps using ## headings\n"
                    "    - Include specific responsibilities as bullet points\n"
                    "    - Define clear boundaries (what the agent should and should NOT do)\n"
                    "    - Add output format guidelines where relevant\n"
                    "    - Keep the user's original intent and content — enhance, don't replace\n"
                    "    - Use markdown formatting (headings, lists, bold, code blocks)\n"
                    "    - Max ~2000 words — be thorough but not bloated\n\n"
                    '  "description": A concise one-line summary (max 100 chars)\n\n'
                    '  "tools": Array of GitHub Copilot tool aliases the agent needs '
                    '(choose from: "read", "edit", "search", "execute", "web", "agent", '
                    '"github/*", "playwright/*"; empty array if no specific tools needed)'
                    + examples_section
                ),
            },
            {
                "role": "user",
                "content": f"Agent name: {name}\n\nUser's system prompt:\n{system_prompt}",
            },
        ]

        response = await ai_service._call_completion(
            messages=messages,
            github_token=access_token,
            temperature=0.5,
            max_tokens=4000,
        )

        text = response.strip()
        # Strip markdown JSON fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            result = json.loads(text)
            enhanced_prompt = str(result.get("system_prompt", system_prompt))
            desc = str(result.get("description", name))[:500]
            raw_tools = result.get("tools", [])
            tools = [str(t) for t in raw_tools] if isinstance(raw_tools, list) else []
            return {
                "system_prompt": enhanced_prompt,
                "description": desc,
                "tools": tools,
            }
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Could not parse AI enhancement response, falling back")
            raise

    async def _gather_agent_examples(
        self,
        owner: str,
        repo: str,
        access_token: str,
    ) -> list[str]:
        """Read up to 3 existing .agent.md files from the repo as style references."""
        try:
            entries = await github_projects_service.get_directory_contents(
                access_token=access_token,
                owner=owner,
                repo=repo,
                path=".github/agents",
            )
        except Exception:
            return []

        examples: list[str] = []
        for entry in entries:
            name = entry.get("name", "")
            if not name.endswith(".agent.md") or name == "copilot-instructions.md":
                continue
            if len(examples) >= 3:
                break
            try:
                file_data = await github_projects_service.get_file_content(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    path=f".github/agents/{name}",
                )
                if file_data and file_data.get("content"):
                    content = file_data["content"]
                    # Trim to first 1500 chars to avoid token overload
                    examples.append(f"### {name}\n```\n{content[:1500]}\n```")
            except Exception:
                continue
        return examples

    async def _auto_generate_metadata(
        self,
        *,
        name: str,
        system_prompt: str,
        access_token: str,
    ) -> dict:
        """Use AI to generate a description and tools list from the system prompt.

        Returns ``{"description": str, "tools": list[str]}``.
        """
        from src.services.ai_agent import get_ai_agent_service

        ai_service = get_ai_agent_service()

        messages = [
            {
                "role": "system",
                "content": (
                    "You generate metadata for a Custom GitHub Agent. "
                    "Given the agent name and system prompt, respond with ONLY a JSON object "
                    "(no markdown fences, no explanation) with exactly two keys:\n"
                    '  "description": a concise one-line summary (max 100 chars) of what the agent does\n'
                    '  "tools": an array of GitHub Copilot tool aliases the agent needs '
                    '(choose from: "read", "edit", "search", "execute", "web", "agent", "github/*", "playwright/*"; '
                    "use an empty array if no specific tools are needed)\n"
                    "Example response:\n"
                    '{"description": "Reviews PRs for security vulnerabilities", "tools": ["read", "search", "github/*"]}'
                ),
            },
            {
                "role": "user",
                "content": f"Agent name: {name}\n\nSystem prompt:\n{system_prompt[:3000]}",
            },
        ]

        response = await ai_service._call_completion(
            messages=messages,
            github_token=access_token,
            temperature=0.3,
            max_tokens=200,
        )

        # Parse JSON from response (strip markdown fences if present)
        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            result = json.loads(text)
            desc = str(result.get("description", name))[:500]
            raw_tools = result.get("tools", [])
            tools = [str(t) for t in raw_tools] if isinstance(raw_tools, list) else []
            return {"description": desc, "tools": tools}
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Could not parse AI metadata response: %s", text[:200])
            return {"description": name, "tools": []}

    async def _generate_rich_descriptions(
        self,
        *,
        name: str,
        slug: str,
        description: str,
        system_prompt: str,
        tools: list[str],
        access_token: str,
    ) -> dict:
        """Use AI to generate detailed GitHub Issue body and PR body.

        Returns ``{"issue_body": str, "pr_body": str}``.
        """
        from src.services.ai_agent import get_ai_agent_service

        ai_service = get_ai_agent_service()
        tools_display = ", ".join(f"`{t}`" for t in tools) if tools else "all (default)"

        messages = [
            {
                "role": "system",
                "content": (
                    "You generate detailed GitHub Issue and Pull Request descriptions for a new "
                    "Custom GitHub Agent being added to a repository. Write professional, clear markdown.\n\n"
                    "Respond with ONLY a JSON object (no markdown fences) with exactly two keys:\n"
                    '  "issue_body": A detailed GitHub Issue body (markdown) that describes:\n'
                    "    - What the agent does and its purpose\n"
                    "    - The agent's capabilities and tools\n"
                    "    - Key behaviors from the system prompt\n"
                    "    - The files being created (.agent.md and .prompt.md)\n"
                    "    - A note that this was auto-generated by the Agents section\n\n"
                    '  "pr_body": A detailed PR description (markdown) that describes:\n'
                    "    - Summary of what's being added\n"
                    "    - The two files being committed with their paths\n"
                    "    - How to use the agent (invoke with @agent-name)\n"
                    "    - A checklist: [ ] Review agent configuration, [ ] Verify tools are appropriate, [ ] Test agent behavior\n"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Agent name: {name}\n"
                    f"Slug: {slug}\n"
                    f"Description: {description}\n"
                    f"Tools: {tools_display}\n\n"
                    f"System prompt (first 2000 chars):\n{system_prompt[:2000]}"
                ),
            },
        ]

        response = await ai_service._call_completion(
            messages=messages,
            github_token=access_token,
            temperature=0.4,
            max_tokens=1500,
        )

        text = response.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        try:
            result = json.loads(text)
            return {
                "issue_body": str(result.get("issue_body", "")),
                "pr_body": str(result.get("pr_body", "")),
            }
        except (json.JSONDecodeError, AttributeError):
            logger.warning("Could not parse AI descriptions response, using defaults")
            raise

    @staticmethod
    def _default_pr_body(preview: AgentPreview, slug: str) -> str:
        """Fallback PR body when AI generation is skipped or fails."""
        return (
            f"## Agent: {preview.name}\n\n"
            f"{preview.description}\n\n"
            f"**Files:**\n"
            f"- `.github/agents/{slug}.agent.md`\n"
            f"- `.github/prompts/{slug}.prompt.md`\n"
        )

    async def _resolve_agent(
        self,
        project_id: str,
        agent_id: str,
    ) -> Agent | None:
        """Find an agent by UUID or slug in SQLite."""
        # Try by ID first
        cursor = await self._db.execute(
            "SELECT * FROM agent_configs WHERE id = ? AND project_id = ?",
            (agent_id, project_id),
        )
        row = await cursor.fetchone()

        if not row:
            # Try by slug
            cursor = await self._db.execute(
                "SELECT * FROM agent_configs WHERE slug = ? AND project_id = ?",
                (agent_id, project_id),
            )
            row = await cursor.fetchone()

        if not row:
            return None

        r = (
            dict(row)
            if isinstance(row, dict)
            else dict(zip([d[0] for d in cursor.description], row, strict=False))
        )
        tools = []
        try:
            tools = json.loads(r.get("tools", "[]"))
        except (json.JSONDecodeError, TypeError):
            pass

        status = self._coerce_agent_status(r.get("lifecycle_status"))

        return Agent(
            id=r["id"],
            name=r["name"],
            slug=r["slug"],
            description=r["description"],
            system_prompt=r.get("system_prompt", ""),
            status=status,
            tools=tools,
            status_column=r.get("status_column") or None,
            github_issue_number=r.get("github_issue_number"),
            github_pr_number=r.get("github_pr_number"),
            branch_name=r.get("branch_name"),
            source=AgentSource.LOCAL,
            created_at=r.get("created_at"),
        )

    def _coerce_agent_status(self, raw_status: str | None) -> AgentStatus:
        """Parse persisted lifecycle state, falling back to pending PR."""
        if not raw_status:
            return AgentStatus.PENDING_PR

        try:
            return AgentStatus(raw_status)
        except ValueError:
            logger.warning(
                "Unknown agent lifecycle status '%s'; defaulting to pending_pr", raw_status
            )
            return AgentStatus.PENDING_PR

    async def _cleanup_resolved_pending_agents(
        self,
        *,
        project_id: str,
        repo_agents: list[Agent],
    ) -> None:
        """Remove local pending rows once main reflects the intended repo state."""
        local_agents = await self._list_local_agents(project_id=project_id)
        repo_slugs = {agent.slug for agent in repo_agents}
        deleted_ids: list[str] = []

        for agent in local_agents:
            if agent.status == AgentStatus.PENDING_PR and agent.slug in repo_slugs:
                deleted_ids.append(agent.id)
            elif agent.status == AgentStatus.PENDING_DELETION and agent.slug not in repo_slugs:
                deleted_ids.append(agent.id)

        if deleted_ids:
            await self._db.executemany(
                "DELETE FROM agent_configs WHERE id = ?",
                [(agent_id,) for agent_id in deleted_ids],
            )
            await self._db.commit()

    async def _resolve_listed_agent(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        access_token: str,
        agent_id: str,
    ) -> Agent | None:
        """Resolve an agent from the merged visible list by id or slug."""
        local_agent = await self._resolve_agent(project_id, agent_id)
        if local_agent:
            return local_agent

        visible_agents = await self.list_agents(
            project_id=project_id,
            owner=owner,
            repo=repo,
            access_token=access_token,
        )
        for agent in visible_agents:
            if agent.id == agent_id or agent.slug == agent_id:
                return agent

        return None

    async def _mark_agent_pending_deletion(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        github_user_id: str,
        agent: Agent,
        pr_number: int | None,
        issue_number: int | None,
        branch_name: str,
    ) -> None:
        """Persist deletion state so repo-backed agents do not reappear after delete."""
        existing_local_agent = await self._resolve_agent(project_id, agent.slug)
        tools_json = json.dumps(agent.tools)
        now = utcnow().isoformat()

        if existing_local_agent and not existing_local_agent.id.startswith("repo:"):
            await self._db.execute(
                """UPDATE agent_configs
                   SET name = ?, description = ?, system_prompt = ?, status_column = ?,
                       tools = ?, owner = ?, repo = ?, created_by = ?, github_issue_number = ?,
                       github_pr_number = ?, branch_name = ?, lifecycle_status = ?
                   WHERE id = ?""",
                (
                    agent.name,
                    agent.description,
                    agent.system_prompt,
                    agent.status_column or "",
                    tools_json,
                    owner,
                    repo,
                    github_user_id,
                    issue_number,
                    pr_number,
                    branch_name,
                    AgentStatus.PENDING_DELETION.value,
                    existing_local_agent.id,
                ),
            )
        else:
            await self._db.execute(
                """INSERT INTO agent_configs
                   (id, name, slug, description, system_prompt, status_column,
                    tools, project_id, owner, repo, created_by,
                    github_issue_number, github_pr_number, branch_name, created_at, lifecycle_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    agent.name,
                    agent.slug,
                    agent.description,
                    agent.system_prompt,
                    agent.status_column or "",
                    tools_json,
                    project_id,
                    owner,
                    repo,
                    github_user_id,
                    issue_number,
                    pr_number,
                    branch_name,
                    now,
                    AgentStatus.PENDING_DELETION.value,
                ),
            )

        await self._db.commit()
