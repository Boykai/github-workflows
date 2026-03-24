from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
import re
from typing import ClassVar

import yaml
from githubkit.exception import RequestFailed

from src.logging_utils import get_logger
from src.models.agent import AgentSource, AvailableAgent

logger = get_logger(__name__)


class AgentsMixin:
    """Agent discovery, body tailoring, and prompt formatting."""

    # ──────────────────────────────────────────────────────────────────
    # Agent Discovery (004-agent-workflow-config-ui, T016)
    # ──────────────────────────────────────────────────────────────────

    # Built-in agents that are always available
    BUILTIN_AGENTS: ClassVar[list[AvailableAgent]] = [
        AvailableAgent(
            slug="copilot",
            display_name="GitHub Copilot",
            description="Default GitHub Copilot coding agent",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="copilot-review",
            display_name="Copilot Review",
            description="GitHub Copilot code review agent",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.specify",
            display_name="Spec Kit - Specify",
            description="Generates a detailed specification from a GitHub issue",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.plan",
            display_name="Spec Kit - Plan",
            description="Creates an implementation plan from a specification",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.tasks",
            display_name="Spec Kit - Tasks",
            description="Breaks an implementation plan into granular tasks",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.implement",
            display_name="Spec Kit - Implement",
            description="Implements code changes based on the task list",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.analyze",
            display_name="Spec Kit - Analyze",
            description="Performs a read-only consistency analysis across spec artifacts",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="human",
            display_name="Human",
            description="Manual human task — creates a sub-issue assigned to the issue creator",
            avatar_url=None,
            icon_name=None,
            source=AgentSource.BUILTIN,
        ),
    ]

    _FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)

    def format_issue_context_as_prompt(
        self,
        issue_data: dict,
        agent_name: str = "",
        existing_pr: dict | None = None,
    ) -> str:
        """
        Format issue details (title, body, comments) as a prompt for the custom agent.

        When ``existing_pr`` is provided, instructions tell the agent to push
        commits to the existing PR branch instead of creating a new PR.
        The existing PR instructions are placed FIRST so the agent prioritises
        branch reuse over creating a new pull request.

        Args:
            issue_data: Dict with title, body, and comments from get_issue_with_comments
            agent_name: Name of the custom agent (e.g., 'speckit.specify')
            existing_pr: Optional dict with ``number``, ``head_ref``, ``url``
                         of an existing PR to reuse

        Returns:
            Formatted string suitable as custom instructions for the agent
        """
        parts = []

        # ── Existing PR context (for agents working on an existing branch) ───
        if existing_pr:
            branch = existing_pr.get("head_ref", "")
            pr_num = existing_pr.get("number", "")
            pr_url = existing_pr.get("url", "")
            is_draft = existing_pr.get("is_draft", True)
            draft_label = " (Draft / Work In Progress)" if is_draft else ""
            parts.append(
                "## Related Pull Request\n\n"
                f"A pull request{draft_label} already exists for this issue.\n"
                f"- **PR:** #{pr_num} — {pr_url}\n"
                f"- **Branch:** `{branch}`\n\n"
                "Previous agent work exists on this branch. Your work will be "
                "created as a child branch and automatically merged back.\n\n"
                "---"
            )

        # ── Issue context ────────────────────────────────────────────────
        # Add title
        title = issue_data.get("title", "")
        if title:
            parts.append(f"## Issue Title\n{title}")

        # Add description/body
        body = issue_data.get("body", "")
        if body:
            parts.append(f"## Issue Description\n{body}")

        # Add comments/discussions
        comments = issue_data.get("comments", [])
        if comments:
            parts.append("## Comments and Discussion")
            for idx, comment in enumerate(comments, 1):
                author = comment.get("author", "unknown")
                comment_body = comment.get("body", "")
                created_at = comment.get("created_at", "")
                parts.append(f"### Comment {idx} by @{author} ({created_at})\n{comment_body}")

        # ── Output instructions ──────────────────────────────────────────
        if agent_name:
            # Map each agent to the specific .md file(s) it produces.
            # All agents are listed; implement has no .md outputs.
            agent_files = {
                "speckit.specify": ["spec.md"],
                "speckit.plan": ["plan.md"],
                "speckit.tasks": ["tasks.md"],
                "speckit.implement": [],
                "speckit.analyze": [],
            }
            files = agent_files.get(agent_name, [])

            if agent_name == "speckit.analyze":
                parts.append(
                    "## Output Instructions\n"
                    "IMPORTANT: This agent is read-only. Do NOT commit files or modify the PR "
                    "branch.\n\n"
                    "Produce the analysis report in the agent response only. If remediation is "
                    "needed, request explicit user approval before any follow-up editing work is "
                    "started."
                )
            elif files:
                file_list = ", ".join(f"`{f}`" for f in files)
                branch_note = f" on branch `{existing_pr['head_ref']}`" if existing_pr else ""
                parts.append(
                    "## Output Instructions\n"
                    "IMPORTANT: When you are done generating your output, ensure the following "
                    f"file(s) are committed to the PR branch{branch_note}: {file_list}.\n\n"
                    "The system will automatically detect your PR completion, extract the "
                    "markdown file content, and post it as an issue comment. You do NOT need to "
                    "post comments yourself — just commit the files and complete your PR work."
                )
            else:
                branch_note = f" (`{existing_pr['head_ref']}`)" if existing_pr else ""
                parts.append(
                    "## Output Instructions\n"
                    f"IMPORTANT: Complete your work and commit all changes to the PR branch{branch_note}.\n\n"
                    "The system will automatically detect your PR completion and advance "
                    "the workflow. You do NOT need to post any completion comments."
                )

        return "\n\n".join(parts)

    def tailor_body_for_agent(
        self,
        parent_body: str,
        agent_name: str,
        parent_issue_number: int,
        parent_title: str,
    ) -> str:
        """
        Tailor a parent issue's body for a specific agent sub-issue.

        Creates a focused body that references the parent issue and includes
        agent-specific guidance.

        Args:
            parent_body: The parent issue's body text
            agent_name: The agent slug (e.g., "speckit.specify")
            parent_issue_number: Parent issue number for cross-referencing
            parent_title: Parent issue title

        Returns:
            Tailored markdown body for the sub-issue
        """
        # Map agent slugs to human-readable task descriptions
        agent_descriptions = {
            "speckit.specify": "Write a detailed specification for this feature. Analyze requirements, define acceptance criteria, and document the technical approach.",
            "speckit.plan": "Create a detailed implementation plan. Break down the specification into actionable steps, identify dependencies, and define the order of execution.",
            "speckit.tasks": "Generate granular implementation tasks from the plan. Each task should be a well-defined unit of work with clear inputs, outputs, and acceptance criteria.",
            "speckit.implement": "Implement the feature based on the specification, plan, and tasks. Write production-quality code with tests.",
            "speckit.analyze": "Analyze the generated specification artifacts for consistency, coverage, ambiguity, and constitution compliance. This task is strictly read-only and should return an analysis report without modifying files.",
            "copilot": "Implement the requested changes. Write production-quality code with tests.",
            "human": "This is a manual human task. Complete the work described below, then close this issue or comment 'Done!' on the parent issue to continue the pipeline.",
            "copilot-review": (
                "A Copilot code review has been requested on the main PR for this feature "
                "(the branch created by `speckit.specify` that contains all merged agent work).\n\n"
                "**Note:** This sub-issue is a pipeline tracking issue — Copilot reviews the PR "
                "directly, not through this issue. This sub-issue will be closed once the "
                "Copilot review is complete."
            ),
        }

        agent_desc = agent_descriptions.get(
            agent_name,
            f"Complete the work assigned to the `{agent_name}` agent.",
        )

        # Strip the tracking table from the parent body (it belongs to the parent)
        import re

        clean_body = re.sub(
            r"\n---\s*\n\s*##\s*🤖\s*(?:Agent Pipeline|Agents Pipelines).*",
            "",
            parent_body,
            flags=re.DOTALL,
        ).rstrip()

        # Also strip the "Generated by AI" footer
        clean_body = re.sub(
            r"\n---\s*\n\*Generated by AI.*?\*\s*$",
            "",
            clean_body,
            flags=re.DOTALL,
        ).rstrip()

        body = f"""> **Parent Issue:** #{parent_issue_number} — {parent_title}

## 🤖 Agent Task: `{agent_name}`

{agent_desc}

---

## Parent Issue Context

{clean_body}

---
*Sub-issue created for agent `{agent_name}` — see parent issue #{parent_issue_number} for full context*
"""
        return body

    async def list_available_agents(
        self,
        owner: str,
        repo: str,
        access_token: str,
    ) -> list[AvailableAgent]:
        """
        Discover agents available for assignment.

        Combines hardcoded built-in agents with custom agents found in
        the repository's `.github/agents/*.agent.md` files.

        Args:
            owner: Repository owner.
            repo: Repository name.
            access_token: GitHub OAuth access token.

        Returns:
            Combined list of built-in + repository agents.
        """
        agents: list[AvailableAgent] = list(self.BUILTIN_AGENTS)

        if not owner or not repo:
            return agents

        # List .github/agents/ directory via Contents API
        try:
            contents = await self._rest(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/contents/.github/agents",
            )
        except RequestFailed as exc:
            if exc.response.status_code == 404:
                logger.debug("No .github/agents/ directory in %s/%s", owner, repo)
                return agents
            logger.warning(
                "Failed to list .github/agents/ in %s/%s: %s",
                owner,
                repo,
                exc,
            )
            return agents

        if not isinstance(contents, list):
            return agents

        # Filter for *.agent.md files
        agent_files = [
            f
            for f in contents
            if isinstance(f, dict)
            and f.get("name", "").endswith(".agent.md")
            and f.get("type") == "file"
        ]

        for file_info in agent_files:
            slug = file_info["name"].removesuffix(".agent.md")
            download_url = file_info.get("download_url")
            # Default: title-case the slug as a readable fallback (e.g. "quality-assurance" → "Quality Assurance")
            display_name = " ".join(p.capitalize() for p in slug.replace(".", "-").split("-") if p)
            description: str | None = None
            icon_name: str | None = None

            # Fetch raw content and parse YAML frontmatter
            if download_url:
                try:
                    raw_resp = await self._rest_response(
                        access_token,
                        "GET",
                        download_url,
                    )
                    raw_content = raw_resp.text
                    fm_match = self._FRONTMATTER_RE.match(raw_content)
                    if fm_match:
                        try:
                            fm = yaml.safe_load(fm_match.group(1))
                            if isinstance(fm, dict):
                                display_name = fm.get("name", slug)
                                description = fm.get("description")
                                raw_icon_name = fm.get("icon") or fm.get("icon_name")
                                if raw_icon_name is not None:
                                    icon_name = str(raw_icon_name)
                        except yaml.YAMLError:
                            logger.debug("Invalid YAML frontmatter in %s", file_info["name"])
                except RequestFailed:
                    logger.debug("Could not fetch content for %s", file_info["name"])

            agents.append(
                AvailableAgent(
                    slug=slug,
                    display_name=display_name,
                    description=description,
                    avatar_url=None,
                    icon_name=icon_name,
                    source=AgentSource.REPOSITORY,
                )
            )

        return agents


# TODO(018-codebase-audit-refactor): Module-level singleton should be removed
# in favor of exclusive app.state registration. Deferred because 17+ files
# import this directly in non-request contexts (background tasks, signal bridge,
# orchestrator) where Request.app.state is not available.
#
# FR-008 (001-code-quality-tech-debt) explicitly defers this to a follow-up PR.
# Required scope for that PR:
#   1. Audit all 17+ consuming files (background tasks, signal bridge,
#      orchestrator, polling loops).
#   2. Introduce a get_github_service() accessor pattern that returns the
#      singleton from app.state in request contexts and falls back to the
#      module-level instance in non-request contexts.
#   3. Update all affected test mocks to use the accessor.
# Global service instance
