"""Issue and task management operations."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from .graphql_queries import (
    ADD_ISSUE_TO_PROJECT_MUTATION,
    CREATE_DRAFT_ITEM_MUTATION,
    GET_ISSUE_WITH_COMMENTS_QUERY,
    UPDATE_ITEM_STATUS_MUTATION,
)

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class IssuesMixin:
    """Issue creation, updates, and task management."""

    _client: httpx.AsyncClient

    async def create_draft_item(
        self,
        access_token: str,
        project_id: str,
        title: str,
        description: str | None = None,
    ) -> str:
        """
        Create a draft issue item in a project.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            title: Task title
            description: Task description/body

        Returns:
            Created item ID
        """
        data = await self._graphql(
            access_token,
            CREATE_DRAFT_ITEM_MUTATION,
            {"projectId": project_id, "title": title, "body": description},
        )

        item_data = data.get("addProjectV2DraftIssue", {}).get("projectItem", {})
        return item_data.get("id", "")

    async def update_item_status(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        field_id: str,
        option_id: str,
    ) -> bool:
        """
        Update an item's status field.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            field_id: Status field node ID
            option_id: Status option ID

        Returns:
            True if update succeeded
        """
        # Add 2 second delay before status update (rate limiting / UX improvement)
        await asyncio.sleep(2)

        data = await self._graphql(
            access_token,
            UPDATE_ITEM_STATUS_MUTATION,
            {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "optionId": option_id,
            },
        )

        return bool(data.get("updateProjectV2ItemFieldValue", {}).get("projectV2Item"))

    # ──────────────────────────────────────────────────────────────────
    # Issue Creation and Project Attachment (T018-T020, T036-T037, T043)
    # ──────────────────────────────────────────────────────────────────

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
