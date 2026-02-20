"""Mixin for issue management operations."""

import logging
import re

import httpx
import yaml

from src.models.chat import AgentSource, AvailableAgent

from ._queries import (
    ADD_ISSUE_TO_PROJECT_MUTATION,
    GET_ISSUE_WITH_COMMENTS_QUERY,
)

logger = logging.getLogger(__name__)


class _IssueOpsMixin:
    """Mixin for issue creation, comments, sub-issues, and agent discovery."""

    async def create_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> dict:
        """
        Create a GitHub Issue using REST API (T018).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body (markdown)
            labels: Optional list of label names

        Returns:
            Dict with issue details: id, node_id, number, html_url
        """
        response = await self._client.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            json={
                "title": title,
                "body": body,
                "labels": labels or [],
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        issue = response.json()

        logger.info("Created issue #%d in %s/%s", issue["number"], owner, repo)
        return issue

    async def update_issue_body(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> bool:
        """
        Update a GitHub Issue's body text using REST API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: New issue body (markdown)

        Returns:
            True if update succeeded
        """
        try:
            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
                json={"body": body},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
            response.raise_for_status()
            logger.info("Updated body of issue #%d in %s/%s", issue_number, owner, repo)
            return True
        except Exception as e:
            logger.error("Failed to update issue #%d body: %s", issue_number, e)
            return False

    async def update_issue_state(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        state: str,
        state_reason: str | None = None,
        labels_add: list[str] | None = None,
        labels_remove: list[str] | None = None,
    ) -> bool:
        """
        Update a GitHub Issue's state (open/closed) and optionally manage labels.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            state: "open" or "closed"
            state_reason: Optional reason ("completed", "not_planned", "reopened")
            labels_add: Labels to add
            labels_remove: Labels to remove

        Returns:
            True if update succeeded
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            # Update state
            payload: dict = {"state": state}
            if state_reason:
                payload["state_reason"] = state_reason

            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()

            # Add labels
            if labels_add:
                await self._client.post(
                    f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels",
                    json={"labels": labels_add},
                    headers=headers,
                )

            # Remove labels
            if labels_remove:
                for label in labels_remove:
                    await self._client.delete(
                        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}",
                        headers=headers,
                    )

            logger.info(
                "Updated issue #%d state to '%s' in %s/%s",
                issue_number,
                state,
                owner,
                repo,
            )
            return True
        except Exception as e:
            logger.warning("Failed to update issue #%d state: %s", issue_number, e)
            return False

    async def add_issue_to_project(
        self,
        access_token: str,
        project_id: str,
        issue_node_id: str,
    ) -> str:
        """
        Add an existing issue to a GitHub Project (T020).

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            issue_node_id: GitHub Issue node ID

        Returns:
            Project item ID
        """
        data = await self._graphql(
            access_token,
            ADD_ISSUE_TO_PROJECT_MUTATION,
            {"projectId": project_id, "contentId": issue_node_id},
        )

        item_id = data.get("addProjectV2ItemById", {}).get("item", {}).get("id", "")
        logger.info("Added issue %s to project, item_id: %s", issue_node_id, item_id)
        return item_id

    async def assign_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        assignees: list[str],
    ) -> bool:
        """
        Assign users to a GitHub Issue (T036).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            assignees: List of usernames to assign

        Returns:
            True if assignment succeeded
        """
        response = await self._client.patch(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
            json={"assignees": assignees},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        success = response.status_code == 200
        if success:
            logger.info("Assigned %s to issue #%d", assignees, issue_number)
        else:
            logger.warning(
                "Failed to assign %s to issue #%d: %s",
                assignees,
                issue_number,
                response.text,
            )

        return success

    async def get_issue_with_comments(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict:
        """
        Fetch issue details including title, body, and all comments.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Dict with issue title, body, and comments list
        """
        try:
            data = await self._graphql(
                access_token,
                GET_ISSUE_WITH_COMMENTS_QUERY,
                {"owner": owner, "name": repo, "number": issue_number},
            )

            issue = data.get("repository", {}).get("issue", {})
            comments = issue.get("comments", {}).get("nodes", [])

            return {
                "title": issue.get("title", ""),
                "body": issue.get("body", ""),
                "comments": [
                    {
                        "author": c.get("author", {}).get("login", "unknown"),
                        "body": c.get("body", ""),
                        "created_at": c.get("createdAt", ""),
                    }
                    for c in comments
                ],
            }
        except Exception as e:
            logger.error("Failed to fetch issue #%d with comments: %s", issue_number, e)
            return {"title": "", "body": "", "comments": []}

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
            }
            files = agent_files.get(agent_name, [])

            if files:
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

    async def check_agent_completion_comment(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        agent_name: str,
    ) -> bool:
        """
        Check if an agent has posted a completion comment on the issue.

        Scans issue comments for a comment body containing the pattern:
        ``<agent_name>: Done!``

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: GitHub issue number
            agent_name: Agent name to look for (e.g., 'speckit.specify')

        Returns:
            True if a completion comment from the agent was found
        """
        try:
            issue_data = await self.get_issue_with_comments(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            if not issue_data:
                logger.warning("Could not fetch issue #%d for agent completion check", issue_number)
                return False

            comments = issue_data.get("comments", [])
            marker = f"{agent_name}: Done!"

            # Scan comments in reverse chronological order for the most recent marker
            for comment in reversed(comments):
                body = comment.get("body", "")
                if marker in body:
                    logger.info(
                        "Found completion marker for agent '%s' on issue #%d",
                        agent_name,
                        issue_number,
                    )
                    return True

            return False

        except Exception as e:
            logger.error(
                "Error checking agent completion comment for issue #%d: %s",
                issue_number,
                e,
            )
            return False

    async def create_sub_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        parent_issue_number: int,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> dict:
        """
        Create a GitHub sub-issue attached to a parent issue.

        Uses the GitHub Sub-Issues API to create a new issue and link it
        as a child of the parent issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            parent_issue_number: Parent issue number to attach to
            title: Sub-issue title
            body: Sub-issue body (markdown)
            labels: Optional list of label names

        Returns:
            Dict with sub-issue details: id, node_id, number, html_url
        """
        # Step 1: Create the issue
        sub_issue = await self.create_issue(
            access_token=access_token,
            owner=owner,
            repo=repo,
            title=title,
            body=body,
            labels=labels,
        )

        sub_issue_number = sub_issue["number"]

        # Step 2: Attach as sub-issue using the Sub-Issues API
        try:
            response = await self._client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{parent_issue_number}/sub_issues",
                json={"sub_issue_id": sub_issue["id"]},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code in (200, 201):
                logger.info(
                    "Attached sub-issue #%d to parent issue #%d",
                    sub_issue_number,
                    parent_issue_number,
                )
            else:
                logger.warning(
                    "Failed to attach sub-issue #%d to parent #%d: %d %s",
                    sub_issue_number,
                    parent_issue_number,
                    response.status_code,
                    response.text[:300] if response.text else "",
                )
        except Exception as e:
            logger.warning(
                "Failed to attach sub-issue #%d to parent #%d: %s",
                sub_issue_number,
                parent_issue_number,
                e,
            )

        return sub_issue

    async def get_sub_issues(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Get sub-issues for a parent issue using the GitHub Sub-Issues API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Parent issue number

        Returns:
            List of sub-issue dicts with id, node_id, number, title, state, html_url, assignees, etc.
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 50},
            )

            if response.status_code == 200:
                sub_issues = response.json()
                logger.info(
                    "Found %d sub-issues for issue #%d",
                    len(sub_issues),
                    issue_number,
                )
                return sub_issues
            else:
                logger.debug(
                    "No sub-issues for issue #%d: %d",
                    issue_number,
                    response.status_code,
                )
                return []

        except Exception as e:
            logger.debug("Failed to get sub-issues for issue #%d: %s", issue_number, e)
            return []

    async def create_issue_comment(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        body: str,
    ) -> dict | None:
        """
        Create a comment on a GitHub Issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: Comment body (markdown)

        Returns:
            Dict with comment details if successful, None otherwise
        """
        try:
            response = await self._client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
                json={"body": body},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code in (200, 201):
                result = response.json()
                logger.info(
                    "Created comment on issue #%d (id=%s)",
                    issue_number,
                    result.get("id"),
                )
                return result
            else:
                logger.error(
                    "Failed to create comment on issue #%d: %s %s",
                    issue_number,
                    response.status_code,
                    response.text[:300] if response.text else "",
                )
                return None

        except Exception as e:
            logger.error("Error creating comment on issue #%d: %s", issue_number, e)
            return None

    async def set_issue_metadata(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        metadata: dict,
    ) -> dict[str, bool]:
        """
        Set multiple metadata fields on a project item.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            metadata: Dict with keys like priority, size, estimate_hours, start_date, target_date

        Returns:
            Dict mapping field names to success status
        """
        results = {}

        # Standard field mappings (project field name -> metadata key)
        field_mappings = {
            "Priority": ("priority", "select"),
            "Size": ("size", "select"),
            "Estimate": ("estimate_hours", "number"),
            "Start date": ("start_date", "date"),
            "Target date": ("target_date", "date"),
        }

        for field_name, (meta_key, field_type) in field_mappings.items():
            value = metadata.get(meta_key)
            if value:
                success = await self.update_project_item_field(
                    access_token=access_token,
                    project_id=project_id,
                    item_id=item_id,
                    field_name=field_name,
                    value=value,
                    field_type=field_type,
                )
                results[field_name] = success

        logger.info("Set metadata fields: %s", results)
        return results

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
            "copilot": "Implement the requested changes. Write production-quality code with tests.",
        }

        agent_desc = agent_descriptions.get(
            agent_name,
            f"Complete the work assigned to the `{agent_name}` agent.",
        )

        # Strip the tracking table from the parent body (it belongs to the parent)
        clean_body = re.sub(
            r"\n---\s*\n\s*##\s*🤖\s*Agent Pipeline.*",
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

    # ──────────────────────────────────────────────────────────────────
    # Agent Discovery (004-agent-workflow-config-ui, T016)
    # ──────────────────────────────────────────────────────────────────

    # Built-in agents that are always available
    BUILTIN_AGENTS: list[AvailableAgent] = [
        AvailableAgent(
            slug="copilot",
            display_name="GitHub Copilot",
            description="Default GitHub Copilot coding agent",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="copilot-review",
            display_name="Copilot Review",
            description="GitHub Copilot code review agent",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.specify",
            display_name="Spec Kit - Specify",
            description="Generates a detailed specification from a GitHub issue",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.plan",
            display_name="Spec Kit - Plan",
            description="Creates an implementation plan from a specification",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.tasks",
            display_name="Spec Kit - Tasks",
            description="Breaks an implementation plan into granular tasks",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
        AvailableAgent(
            slug="speckit.implement",
            display_name="Spec Kit - Implement",
            description="Implements code changes based on the task list",
            avatar_url=None,
            source=AgentSource.BUILTIN,
        ),
    ]

    _FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)

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

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # List .github/agents/ directory via Contents API
        try:
            response = await self._request_with_retry(
                "GET",
                f"https://api.github.com/repos/{owner}/{repo}/contents/.github/agents",
                headers=headers,
            )
            contents = response.json()
        except httpx.HTTPStatusError as exc:
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
            display_name = slug
            description: str | None = None

            # Fetch raw content and parse YAML frontmatter
            if download_url:
                try:
                    raw_resp = await self._request_with_retry("GET", download_url, headers=headers)
                    raw_content = raw_resp.text
                    fm_match = self._FRONTMATTER_RE.match(raw_content)
                    if fm_match:
                        try:
                            fm = yaml.safe_load(fm_match.group(1))
                            if isinstance(fm, dict):
                                display_name = fm.get("name", slug)
                                description = fm.get("description")
                        except yaml.YAMLError:
                            logger.debug("Invalid YAML frontmatter in %s", file_info["name"])
                except httpx.HTTPStatusError:
                    logger.debug("Could not fetch content for %s", file_info["name"])

            agents.append(
                AvailableAgent(
                    slug=slug,
                    display_name=display_name,
                    description=description,
                    avatar_url=None,
                    source=AgentSource.REPOSITORY,
                )
            )

        return agents
