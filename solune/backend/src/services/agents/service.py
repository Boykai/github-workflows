"""Agents section service — CRUD for Custom GitHub Agent configurations.

Available agents are sourced from the GitHub repository default branch under
``.github/agents/*.agent.md``. SQLite stores only local workflow metadata for
unmerged PRs and deletion bookkeeping.
"""

from __future__ import annotations

import json
import re
import time
import uuid

import aiosqlite
import yaml

from src.logging_utils import get_logger
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
    BulkModelUpdateRequest,
    BulkModelUpdateResult,
)
from src.services.agent_creator import generate_config_files, generate_issue_body
from src.services.cache import cache, get_repo_agents_cache_key
from src.services.github_commit_workflow import commit_files_workflow
from src.services.github_projects import github_projects_service
from src.utils import utcnow

logger = get_logger(__name__)

# ── YAML frontmatter regex ──────────────────────────────────────────────
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)
_TOOL_METADATA_KEY = "solune-tool-ids"

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
        cache_key = get_repo_agents_cache_key(owner, repo)

        async def _overlay_runtime_preferences(repo_agents: list[Agent]) -> list[Agent]:
            local_agents = await self._list_local_agents(project_id)
            local_by_slug = {
                local_agent.slug: local_agent
                for local_agent in local_agents
                if local_agent.status == AgentStatus.ACTIVE
                and (
                    local_agent.default_model_id
                    or local_agent.default_model_name
                    or local_agent.icon_name
                )
            }
            return [
                repo_agent.model_copy(
                    update={
                        "default_model_id": local_by_slug[repo_agent.slug].default_model_id,
                        "default_model_name": local_by_slug[repo_agent.slug].default_model_name,
                        "icon_name": local_by_slug[repo_agent.slug].icon_name,
                    }
                )
                if repo_agent.slug in local_by_slug
                else repo_agent
                for repo_agent in repo_agents
            ]

        cached_agents = cache.get(cache_key)
        if isinstance(cached_agents, list):
            await self._cleanup_resolved_pending_agents(
                project_id=project_id,
                repo_agents=cached_agents,
            )
            hydrated_agents = await _overlay_runtime_preferences(cached_agents)
            return sorted(hydrated_agents, key=lambda a: a.name.lower())

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
            hydrated_agents = await _overlay_runtime_preferences(repo_agents)
            return sorted(hydrated_agents, key=lambda a: a.name.lower())

        stale_agents = cache.get_stale(cache_key)
        if isinstance(stale_agents, list):
            hydrated_agents = await _overlay_runtime_preferences(stale_agents)
            return sorted(hydrated_agents, key=lambda a: a.name.lower())

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

    async def bulk_update_models(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        github_user_id: str,
        body: BulkModelUpdateRequest,
        access_token: str,
    ) -> BulkModelUpdateResult:
        """Update the default model for all editable agent configurations in a project."""
        visible_agents = await self.list_agents(
            project_id=project_id,
            owner=owner,
            repo=repo,
            access_token=access_token,
        )
        pending_agents = await self.list_pending_agents(
            project_id=project_id,
            owner=owner,
            repo=repo,
            access_token=access_token,
        )

        agents = [
            *visible_agents,
            *(agent for agent in pending_agents if agent.status != AgentStatus.PENDING_DELETION),
        ]

        updated_agents: list[str] = []
        failed_agents: list[str] = []

        for agent in agents:
            try:
                await self._save_runtime_preferences(
                    project_id=project_id,
                    owner=owner,
                    repo=repo,
                    github_user_id=github_user_id,
                    agent=agent,
                    default_model_id=body.target_model_id,
                    default_model_name=body.target_model_name,
                    icon_name=agent.icon_name,
                )
                updated_agents.append(agent.slug)
            except Exception as e:
                logger.exception("Failed to update model for agent %s: %s", agent.slug, e)
                failed_agents.append(agent.slug)

        return BulkModelUpdateResult(
            success=len(failed_agents) == 0,
            updated_count=len(updated_agents),
            failed_count=len(failed_agents),
            updated_agents=updated_agents,
            failed_agents=failed_agents,
            target_model_id=body.target_model_id,
            target_model_name=body.target_model_name,
        )

    async def get_agent_preferences(self, project_id: str) -> dict[str, dict[str, str]]:
        """Return slug → saved runtime preferences from local SQLite only."""
        cursor = await self._db.execute(
            "SELECT slug, default_model_id, default_model_name, icon_name FROM agent_configs WHERE project_id = ?",
            (project_id,),
        )
        rows = await cursor.fetchall()
        result: dict[str, dict[str, str]] = {}
        for row in rows:
            r = (
                dict(row)
                if isinstance(row, dict)
                else dict(zip([d[0] for d in cursor.description], row, strict=False))
            )
            model_id = r.get("default_model_id", "") or ""
            model_name = r.get("default_model_name", "") or ""
            icon_name = r.get("icon_name", "") or ""
            if model_id or model_name or icon_name:
                result[r["slug"]] = {
                    "default_model_id": model_id,
                    "default_model_name": model_name,
                    "icon_name": icon_name,
                }
        return result

    async def get_model_preferences(self, project_id: str) -> dict[str, dict[str, str]]:
        """Backwards-compatible alias for callers still using the old preference name."""
        return await self.get_agent_preferences(project_id)

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
                    icon_name=r.get("icon_name") or None,
                    system_prompt=r.get("system_prompt", ""),
                    default_model_id=r.get("default_model_id", "") or "",
                    default_model_name=r.get("default_model_name", "") or "",
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

    @staticmethod
    def _normalize_mcp_server_config(server_config: object) -> dict[str, object] | None:
        """Normalize uploaded MCP JSON into GitHub custom-agent YAML shape."""
        if not isinstance(server_config, dict):
            return None

        normalized = dict(server_config)
        server_type = normalized.get("type")
        if not server_type:
            if normalized.get("command"):
                server_type = "local"
            elif normalized.get("url"):
                server_type = "http"

        if server_type == "stdio":
            server_type = "local"

        if server_type:
            normalized["type"] = server_type

        tools = normalized.get("tools")
        if not isinstance(tools, list) or len(tools) == 0:
            normalized["tools"] = ["*"]

        return normalized

    async def _resolve_agent_tool_selection(
        self,
        *,
        project_id: str,
        github_user_id: str,
        requested_tools: list[str],
    ) -> tuple[list[str], list[str], list[str], dict[str, object]]:
        """Split raw agent tool selections into display tools, allowlist items, stored IDs, and MCP servers."""
        if not requested_tools:
            return [], [], [], {}

        requested_ids = [tool for tool in requested_tools if tool]
        tool_rows_by_id: dict[str, aiosqlite.Row] = {}

        if requested_ids:
            placeholders = ",".join("?" for _ in requested_ids)
            cursor = await self._db.execute(
                f"SELECT id, name, config_content FROM mcp_configurations WHERE project_id = ? AND github_user_id = ? AND id IN ({placeholders})",
                (project_id, github_user_id, *requested_ids),
            )
            rows = await cursor.fetchall()
            tool_rows_by_id = {row["id"]: row for row in rows}

        display_tools: list[str] = []
        explicit_allowlist: list[str] = []
        selected_tool_ids: list[str] = []
        mcp_servers: dict[str, object] = {}
        seen_display: set[str] = set()
        seen_allowlist: set[str] = set()

        for tool in requested_tools:
            row = tool_rows_by_id.get(tool)
            if row is None:
                if tool not in seen_display:
                    display_tools.append(tool)
                    seen_display.add(tool)
                if tool not in seen_allowlist:
                    explicit_allowlist.append(tool)
                    seen_allowlist.add(tool)
                continue

            selected_tool_ids.append(row["id"])
            if row["name"] not in seen_display:
                display_tools.append(row["name"])
                seen_display.add(row["name"])

            try:
                config_data = json.loads(row["config_content"] or "{}")
            except json.JSONDecodeError:
                continue

            raw_servers = config_data.get("mcpServers", {})
            if not isinstance(raw_servers, dict):
                continue

            for server_name, server_config in raw_servers.items():
                normalized = self._normalize_mcp_server_config(server_config)
                if normalized is not None:
                    mcp_servers[str(server_name)] = normalized

        if explicit_allowlist:
            allowlist = [*explicit_allowlist, *(f"{name}/*" for name in mcp_servers)]
        else:
            allowlist = []

        return display_tools, allowlist, selected_tool_ids, mcp_servers

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
        except Exception as e:
            logger.debug("Could not read .github/agents/ from %s/%s: %s", owner, repo, e)
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
            icon_name: str | None = None

            match = _FRONTMATTER_RE.match(content)
            if match:
                try:
                    fm = yaml.safe_load(match.group(1))
                    if isinstance(fm, dict):
                        description = fm.get("description", "")
                        agent_name = fm.get("name")
                        raw_icon_name = fm.get("icon") or fm.get("icon_name")
                        if raw_icon_name is not None:
                            icon_name = str(raw_icon_name)
                        metadata = fm.get("metadata")
                        metadata_tool_ids: list[str] = []
                        if isinstance(metadata, dict):
                            metadata_value = metadata.get(_TOOL_METADATA_KEY)
                            if isinstance(metadata_value, str) and metadata_value.strip():
                                metadata_tool_ids = [
                                    value.strip()
                                    for value in metadata_value.split(",")
                                    if value.strip()
                                ]
                        raw_tools = fm.get("tools", [])
                        if metadata_tool_ids:
                            tools = metadata_tool_ids
                        elif isinstance(raw_tools, list):
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
                    icon_name=icon_name,
                    system_prompt=system_prompt,
                    default_model_id="",
                    default_model_name="",
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
        except Exception as exc:
            logger.debug(
                "Skipping existing agent file lookup due to repository read failure",
                exc_info=exc,
            )

        description = body.description
        requested_tools = list(body.tools)
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
                if not requested_tools:
                    requested_tools = enhanced.get("tools", [])
            except Exception as exc:
                logger.warning("AI content enhancement failed, using original input: %s", exc)
                system_prompt = body.system_prompt
                if not description:
                    description = body.name
                if not requested_tools:
                    requested_tools = []
        else:
            # Raw mode — use content exactly as provided
            if not description:
                description = body.name

        # Ensure description is never empty for the file
        if not description:
            description = body.name

        (
            display_tools,
            tool_allowlist,
            selected_tool_ids,
            mcp_servers,
        ) = await self._resolve_agent_tool_selection(
            project_id=project_id,
            github_user_id=github_user_id,
            requested_tools=requested_tools,
        )

        # Build preview
        preview = AgentPreview(
            name=body.name,
            slug=slug,
            description=description,
            icon_name=body.icon_name,
            system_prompt=system_prompt,
            status_column=body.status_column,
            tools=display_tools,
            tool_allowlist=tool_allowlist,
            tool_ids=selected_tool_ids,
            mcp_servers=mcp_servers,
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
                    tools=display_tools,
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
        tools_json = json.dumps(requested_tools)
        now = utcnow().isoformat()

        await self._db.execute(
            """INSERT INTO agent_configs
               (id, name, slug, description, system_prompt, status_column,
                tools, icon_name, default_model_id, default_model_name, project_id, owner, repo, created_by,
                github_issue_number, github_pr_number, branch_name, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_id,
                body.name,
                slug,
                description,
                system_prompt,
                body.status_column,
                tools_json,
                body.icon_name,
                body.default_model_id,
                body.default_model_name,
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
            icon_name=body.icon_name,
            system_prompt=system_prompt,
            default_model_id=body.default_model_id,
            default_model_name=body.default_model_name,
            status=AgentStatus.PENDING_PR,
            tools=requested_tools,
            status_column=body.status_column or None,
            github_issue_number=result.issue_number,
            github_pr_number=result.pr_number,
            branch_name=branch_name,
            source=AgentSource.LOCAL,
            created_at=now,
        )

        # Trigger agent MCP sync to ensure new agent file has correct MCPs (FR-008).
        # Skip when a PR was created — sync operates on the default branch and
        # would create out-of-band commits bypassing the PR.
        if not result.pr_number:
            try:
                from src.services.agents.agent_mcp_sync import sync_agent_mcps

                await sync_agent_mcps(
                    owner=owner,
                    repo=repo,
                    project_id=project_id,
                    access_token=access_token,
                    trigger="agent_create",
                    db=self._db,
                )
            except Exception as sync_exc:
                logger.warning("Agent MCP sync after create failed (non-fatal): %s", sync_exc)

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
        agent = await self._resolve_listed_agent(
            project_id=project_id,
            owner=owner,
            repo=repo,
            access_token=access_token,
            agent_id=agent_id,
        )
        if not agent:
            raise LookupError(f"Agent '{agent_id}' not found")

        only_runtime_preference_update = (
            (
                body.default_model_id is not None
                or body.default_model_name is not None
                or body.icon_name is not None
            )
            and body.name is None
            and body.description is None
            and body.system_prompt is None
            and body.tools is None
        )

        if agent.status == AgentStatus.PENDING_DELETION:
            raise ValueError(
                "Agents pending deletion cannot be updated until the deletion PR is resolved."
            )

        if only_runtime_preference_update:
            updated_agent = await self._save_runtime_preferences(
                project_id=project_id,
                owner=owner,
                repo=repo,
                github_user_id=github_user_id,
                agent=agent,
                default_model_id=body.default_model_id,
                default_model_name=body.default_model_name,
                icon_name=body.icon_name,
            )
            return AgentCreateResult(
                agent=updated_agent,
                pr_url="",
                pr_number=0,
                issue_number=updated_agent.github_issue_number,
                branch_name=updated_agent.branch_name or "",
            )

        # Apply updates
        name = body.name or agent.name
        description = body.description or agent.description
        system_prompt = body.system_prompt or agent.system_prompt
        requested_tools = body.tools if body.tools is not None else agent.tools
        icon_name = body.icon_name if body.icon_name is not None else agent.icon_name
        default_model_id = (
            body.default_model_id if body.default_model_id is not None else agent.default_model_id
        )
        default_model_name = (
            body.default_model_name
            if body.default_model_name is not None
            else agent.default_model_name
        )

        slug = AgentPreview.name_to_slug(name)
        current_local_agent = await self._resolve_agent(project_id, agent.slug)

        # Validate slug: non-empty and filename-safe
        if not slug or not re.match(r"^[a-z0-9][a-z0-9._-]*$", slug):
            raise ValueError(f"Invalid agent slug derived from name '{name}': '{slug}'")

        # Ensure no other agent in SQLite uses this slug (conflict check)
        async with self._db.execute(
            "SELECT id FROM agent_configs WHERE project_id = ? AND slug = ?",
            (project_id, slug),
        ) as cursor:
            conflict_row = await cursor.fetchone()
            conflict_id = conflict_row["id"] if conflict_row else None
            allowed_ids = {agent.id}
            if current_local_agent:
                allowed_ids.add(current_local_agent.id)
            if conflict_id and conflict_id not in allowed_ids:
                raise ValueError(f"An agent with slug '{slug}' already exists for this project.")

        (
            display_tools,
            tool_allowlist,
            selected_tool_ids,
            mcp_servers,
        ) = await self._resolve_agent_tool_selection(
            project_id=project_id,
            github_user_id=github_user_id,
            requested_tools=list(requested_tools),
        )

        preview = AgentPreview(
            name=name,
            slug=slug,
            description=description,
            icon_name=icon_name,
            system_prompt=system_prompt,
            status_column=agent.status_column or "",
            tools=display_tools,
            tool_allowlist=tool_allowlist,
            tool_ids=selected_tool_ids,
            mcp_servers=mcp_servers,
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

        persisted_id = agent.id
        created_at = agent.created_at

        # Persist pending PR state locally so the updated definition is visible before merge.
        if not agent.id.startswith("repo:"):
            tools_json = json.dumps(list(requested_tools))
            await self._db.execute(
                """UPDATE agent_configs
                   SET name = ?, slug = ?, description = ?, system_prompt = ?,
                       tools = ?, icon_name = ?, default_model_id = ?, default_model_name = ?, github_pr_number = ?, branch_name = ?
                   WHERE id = ?""",
                (
                    name,
                    slug,
                    description,
                    system_prompt,
                    tools_json,
                    icon_name,
                    default_model_id,
                    default_model_name,
                    result.pr_number,
                    branch_name,
                    agent.id,
                ),
            )
            await self._db.commit()
        else:
            existing_local_agent = current_local_agent
            tools_json = json.dumps(list(requested_tools))
            now = utcnow().isoformat()

            if existing_local_agent and not existing_local_agent.id.startswith("repo:"):
                persisted_id = existing_local_agent.id
                created_at = existing_local_agent.created_at
                await self._db.execute(
                    """UPDATE agent_configs
                       SET name = ?, slug = ?, description = ?, system_prompt = ?,
                           tools = ?, icon_name = ?, default_model_id = ?, default_model_name = ?, github_pr_number = ?, branch_name = ?,
                           owner = ?, repo = ?, created_by = ?, lifecycle_status = ?
                       WHERE id = ?""",
                    (
                        name,
                        slug,
                        description,
                        system_prompt,
                        tools_json,
                        icon_name,
                        default_model_id,
                        default_model_name,
                        result.pr_number,
                        branch_name,
                        owner,
                        repo,
                        github_user_id,
                        AgentStatus.PENDING_PR.value,
                        existing_local_agent.id,
                    ),
                )
            else:
                persisted_id = str(uuid.uuid4())
                created_at = now
                await self._db.execute(
                    """INSERT INTO agent_configs
                       (id, name, slug, description, system_prompt, status_column,
                        tools, icon_name, default_model_id, default_model_name, project_id, owner, repo, created_by,
                        github_issue_number, github_pr_number, branch_name, created_at, lifecycle_status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        persisted_id,
                        name,
                        slug,
                        description,
                        system_prompt,
                        agent.status_column or "",
                        tools_json,
                        icon_name,
                        default_model_id,
                        default_model_name,
                        project_id,
                        owner,
                        repo,
                        github_user_id,
                        agent.github_issue_number,
                        result.pr_number,
                        branch_name,
                        now,
                        AgentStatus.PENDING_PR.value,
                    ),
                )

            await self._db.commit()

        updated_agent = Agent(
            id=agent.id if not agent.id.startswith("repo:") else persisted_id,
            name=name,
            slug=slug,
            description=description,
            icon_name=icon_name,
            system_prompt=system_prompt,
            default_model_id=default_model_id,
            default_model_name=default_model_name,
            status=agent.status if not agent.id.startswith("repo:") else AgentStatus.PENDING_PR,
            tools=list(requested_tools),
            status_column=agent.status_column,
            github_issue_number=agent.github_issue_number,
            github_pr_number=result.pr_number,
            branch_name=branch_name,
            source=agent.source if not agent.id.startswith("repo:") else AgentSource.LOCAL,
            created_at=agent.created_at if not agent.id.startswith("repo:") else created_at,
        )

        # Trigger agent MCP sync to re-enforce MCPs after agent update (FR-003).
        # Skip when a PR was created — sync operates on the default branch and
        # would create out-of-band commits bypassing the PR.
        if not result.pr_number:
            try:
                from src.services.agents.agent_mcp_sync import sync_agent_mcps

                await sync_agent_mcps(
                    owner=owner,
                    repo=repo,
                    project_id=project_id,
                    access_token=access_token,
                    trigger="agent_update",
                    db=self._db,
                )
            except Exception as sync_exc:
                logger.warning("Agent MCP sync after update failed (non-fatal): %s", sync_exc)

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
            # NOTE(001-code-quality-tech-debt): This is a bare re-raise
            # (the original exception type must propagate). Cannot use
            # handle_service_error() because that function always constructs
            # a *new* exception (defaulting to GitHubAPIError), which would
            # silently change the exception type seen by callers.
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
            except Exception as exc:
                logger.debug(
                    "Skipping example agent file %s after read failure", name, exc_info=exc
                )
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
            icon_name=r.get("icon_name") or None,
            system_prompt=r.get("system_prompt", ""),
            default_model_id=r.get("default_model_id", "") or "",
            default_model_name=r.get("default_model_name", "") or "",
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
                    tools, icon_name, default_model_id, default_model_name, project_id, owner, repo, created_by,
                    github_issue_number, github_pr_number, branch_name, created_at, lifecycle_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    agent.name,
                    agent.slug,
                    agent.description,
                    agent.system_prompt,
                    agent.status_column or "",
                    tools_json,
                    agent.icon_name,
                    agent.default_model_id,
                    agent.default_model_name,
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

    async def _save_runtime_preferences(
        self,
        *,
        project_id: str,
        owner: str,
        repo: str,
        github_user_id: str,
        agent: Agent,
        default_model_id: str | None,
        default_model_name: str | None,
        icon_name: str | None,
    ) -> Agent:
        """Persist per-project runtime preferences without creating repo content changes."""
        resolved_model_id = (
            default_model_id if default_model_id is not None else agent.default_model_id
        )
        resolved_model_name = (
            default_model_name if default_model_name is not None else agent.default_model_name
        )
        resolved_icon_name = icon_name if icon_name is not None else agent.icon_name
        existing_local_agent = await self._resolve_agent(project_id, agent.slug)
        tools_json = json.dumps(agent.tools)
        now = utcnow().isoformat()

        if existing_local_agent and not existing_local_agent.id.startswith("repo:"):
            await self._db.execute(
                """UPDATE agent_configs
                   SET name = ?, description = ?, system_prompt = ?, status_column = ?,
                       tools = ?, owner = ?, repo = ?, created_by = ?, icon_name = ?, default_model_id = ?,
                       default_model_name = ?
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
                    resolved_icon_name,
                    resolved_model_id,
                    resolved_model_name,
                    existing_local_agent.id,
                ),
            )
            persisted_status = existing_local_agent.status
            persisted_id = existing_local_agent.id
            created_at = existing_local_agent.created_at
        else:
            persisted_id = str(uuid.uuid4())
            await self._db.execute(
                """INSERT INTO agent_configs
                   (id, name, slug, description, system_prompt, status_column,
                    tools, icon_name, default_model_id, default_model_name, project_id, owner, repo,
                    created_by, github_issue_number, github_pr_number, branch_name, created_at,
                    lifecycle_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    persisted_id,
                    agent.name,
                    agent.slug,
                    agent.description,
                    agent.system_prompt,
                    agent.status_column or "",
                    tools_json,
                    resolved_icon_name,
                    resolved_model_id,
                    resolved_model_name,
                    project_id,
                    owner,
                    repo,
                    github_user_id,
                    agent.github_issue_number,
                    agent.github_pr_number,
                    agent.branch_name,
                    now,
                    AgentStatus.ACTIVE.value,
                ),
            )
            persisted_status = AgentStatus.ACTIVE
            created_at = now

        await self._db.commit()

        return agent.model_copy(
            update={
                "icon_name": resolved_icon_name,
                "default_model_id": resolved_model_id,
                "default_model_name": resolved_model_name,
                "status": persisted_status,
                "created_at": created_at,
                "id": persisted_id if not agent.id.startswith("repo:") else agent.id,
            }
        )
