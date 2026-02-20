"""Mixin for Copilot assignment and repository lookup operations."""

import asyncio
import json as json_mod
import logging

from ._queries import (
    ASSIGN_COPILOT_MUTATION,
    GET_PROJECT_REPOSITORY_QUERY,
    GET_SUGGESTED_ACTORS_QUERY,
)

logger = logging.getLogger(__name__)


class _CopilotOpsMixin:
    """Mixin for Copilot bot discovery, assignment, and repository helpers."""

    async def get_copilot_bot_id(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> tuple[str | None, str | None]:
        """
        Get the Copilot bot actor ID for a repository using suggestedActors API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name

        Returns:
            Tuple of (Copilot bot node ID, repository node ID) or (None, None) if not available
        """
        try:
            data = await self._graphql(
                access_token,
                GET_SUGGESTED_ACTORS_QUERY,
                {"owner": owner, "name": repo},
                extra_headers={
                    "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"
                },
            )

            repository = data.get("repository", {})
            repo_id = repository.get("id")
            actors = repository.get("suggestedActors", {}).get("nodes", [])

            # Look for the Copilot SWE agent bot
            for actor in actors:
                login = actor.get("login", "")
                typename = actor.get("__typename", "")
                if login == "copilot-swe-agent" and typename == "Bot":
                    bot_id = actor.get("id")
                    logger.info("Found Copilot bot: %s (ID: %s)", login, bot_id)
                    return bot_id, repo_id

            logger.warning(
                "Copilot bot not available for %s/%s (actors: %s)",
                owner,
                repo,
                [a.get("login") for a in actors],
            )
            return None, repo_id
        except Exception as e:
            logger.warning("Failed to get Copilot bot ID: %s", e)
            return None, None

    async def assign_copilot_to_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_node_id: str,
        issue_number: int | None = None,
        base_ref: str = "main",
        custom_agent: str = "",
        custom_instructions: str = "",
    ) -> bool:
        """
        Assign GitHub Copilot to an issue using GraphQL API with agent assignment.

        Uses the GraphQL ``addAssigneesToAssignable`` mutation with the
        ``agentAssignment`` input which explicitly supports ``customAgent``.
        Falls back to the REST API if GraphQL fails.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_node_id: Issue node ID (for GraphQL approach)
            issue_number: Issue number (used for REST fallback and logging)
            base_ref: Branch to base the PR on (default: main)
            custom_agent: Custom agent name (e.g., 'speckit.specify')
            custom_instructions: Custom instructions/prompt for the agent

        Returns:
            True if assignment succeeded
        """
        logger.info(
            "Assigning Copilot to issue #%s (node=%s) with custom_agent='%s'",
            issue_number,
            issue_node_id,
            custom_agent,
        )

        # If this is a custom agent assignment, unassign Copilot first — but
        # ONLY if Copilot is currently assigned. Skipping this for new issues
        # avoids a race condition where the recovery loop sees "Copilot NOT
        # assigned" between the unassign and re-assign steps.
        if custom_agent and issue_number:
            is_assigned = await self.is_copilot_assigned_to_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if is_assigned:
                await self.unassign_copilot_from_issue(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )

        # Prefer GraphQL — it explicitly supports customAgent in the schema
        graphql_success = await self._assign_copilot_graphql(
            access_token,
            owner,
            repo,
            issue_node_id,
            base_ref,
            custom_agent,
            custom_instructions,
        )

        if graphql_success:
            return True

        # Fall back to REST API if GraphQL failed
        if not issue_number:
            logger.warning("GraphQL assignment failed and no issue_number for REST fallback")
            return False

        return await self._assign_copilot_rest(
            access_token,
            owner,
            repo,
            issue_number,
            base_ref,
            custom_agent,
            custom_instructions,
        )

    async def _assign_copilot_rest(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        base_ref: str = "main",
        custom_agent: str = "",
        custom_instructions: str = "",
    ) -> bool:
        """
        Fallback: Assign GitHub Copilot using REST API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            base_ref: Branch to base the PR on
            custom_agent: Custom agent name
            custom_instructions: Custom instructions for the agent

        Returns:
            True if assignment succeeded
        """
        try:
            payload = {
                "assignees": ["copilot-swe-agent[bot]"],
                "agent_assignment": {
                    "target_repo": f"{owner}/{repo}",
                    "base_branch": base_ref,
                    "custom_instructions": custom_instructions,
                    "custom_agent": custom_agent,
                    "model": "claude-opus-4.6",
                },
            }

            logger.info(
                "REST fallback: Assigning Copilot to issue #%d with custom_agent='%s'",
                issue_number,
                custom_agent,
            )

            response = await self._client.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/assignees",
                json=payload,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code in (200, 201):
                result = response.json()
                assignees = [a.get("login", "") for a in result.get("assignees", [])]
                logger.info(
                    "REST: Assigned Copilot to issue #%d with custom agent '%s', assignees: %s",
                    issue_number,
                    custom_agent,
                    assignees,
                )
                return True
            else:
                logger.error(
                    "REST API failed to assign Copilot to issue #%d - Status: %s, Response: %s",
                    issue_number,
                    response.status_code,
                    response.text[:500] if response.text else "empty",
                )
                return False

        except Exception as e:
            logger.error("REST fallback failed for issue #%d: %s", issue_number, e)
            return False

    async def _assign_copilot_graphql(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_node_id: str,
        base_ref: str = "main",
        custom_agent: str = "",
        custom_instructions: str = "",
    ) -> bool:
        """
        Primary: Assign GitHub Copilot using GraphQL API.

        Uses the ``addAssigneesToAssignable`` mutation with ``agentAssignment``
        input which explicitly supports the ``customAgent`` field in the schema.
        This is preferred over the REST API to ensure custom agent routing.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_node_id: Issue node ID
            base_ref: Branch to base the PR on
            custom_agent: Custom agent name
            custom_instructions: Custom instructions for the agent

        Returns:
            True if assignment succeeded
        """
        # Get Copilot bot ID and repo ID
        copilot_id, repo_id = await self.get_copilot_bot_id(access_token, owner, repo)
        if not copilot_id:
            logger.warning("Cannot assign Copilot - bot not available for %s/%s", owner, repo)
            return False
        if not repo_id:
            logger.warning("Cannot assign Copilot - repository ID not found for %s/%s", owner, repo)
            return False

        try:
            # Use GraphQL mutation with special headers for Copilot assignment
            data = await self._graphql(
                access_token,
                ASSIGN_COPILOT_MUTATION,
                {
                    "issueId": issue_node_id,
                    "assigneeIds": [copilot_id],
                    "repoId": repo_id,
                    "baseRef": base_ref,
                    "customInstructions": custom_instructions,
                    "customAgent": custom_agent,
                },
                extra_headers={
                    "GraphQL-Features": "issues_copilot_assignment_api_support,coding_agent_model_selection"
                },
            )

            assignees = (
                data.get("addAssigneesToAssignable", {})
                .get("assignable", {})
                .get("assignees", {})
                .get("nodes", [])
            )
            assigned_logins = [a.get("login", "") for a in assignees]

            if custom_agent:
                logger.info(
                    "GraphQL: Assigned Copilot with custom agent '%s', assignees: %s",
                    custom_agent,
                    assigned_logins,
                )
            else:
                logger.info("GraphQL: Assigned Copilot to issue, assignees: %s", assigned_logins)

            return True

        except Exception as e:
            logger.error("GraphQL failed to assign Copilot to issue: %s", e)
            return False

    async def is_copilot_assigned_to_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> bool:
        """
        Check if GitHub Copilot is currently assigned to an issue.

        When Copilot finishes its work, it unassigns itself from the issue.
        This can be used as a completion signal for agents working on existing branches.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            True if Copilot is currently assigned
        """
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            response = await self._client.get(url, headers=headers)
            if response.status_code != 200:
                logger.warning(
                    "Failed to check assignees for issue #%d: status %d",
                    issue_number,
                    response.status_code,
                )
                return True  # Assume still assigned on error (conservative)

            issue_data = response.json()
            assignees = issue_data.get("assignees", [])
            for assignee in assignees:
                login = (assignee.get("login") or "").lower()
                if "copilot" in login:
                    return True

            return False

        except Exception as e:
            logger.warning("Error checking Copilot assignment for issue #%d: %s", issue_number, e)
            return True  # Assume still assigned on error (conservative)

    async def unassign_copilot_from_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> bool:
        """
        Unassign GitHub Copilot from an issue.

        This is needed before re-assigning Copilot with a different custom agent,
        as the API may fail if Copilot is already assigned.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            True if unassignment succeeded or Copilot was not assigned
        """
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/assignees"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "X-GitHub-Api-Version": "2022-11-28",
            }

            # Use REST API to remove Copilot assignee
            # The assignee login for Copilot is "copilot-swe-agent[bot]"
            # httpx's delete() doesn't support json= param, so use request()
            response = await self._client.request(
                "DELETE",
                url,
                content=json_mod.dumps({"assignees": ["copilot-swe-agent[bot]"]}),
                headers=headers,
            )

            if response.status_code == 200:
                # Verify Copilot was actually removed from assignees
                result = response.json()
                remaining = [a.get("login", "") for a in result.get("assignees", [])]
                copilot_gone = not any("copilot" in a.lower() for a in remaining)
                logger.info(
                    "Unassigned Copilot from issue #%d (remaining assignees: %s, copilot_removed: %s)",
                    issue_number,
                    remaining,
                    copilot_gone,
                )
                # Give GitHub a moment to propagate the unassignment
                await asyncio.sleep(2)
                return copilot_gone
            elif response.status_code == 404:
                # Copilot was not assigned
                logger.debug(
                    "Copilot was not assigned to issue #%d, nothing to unassign",
                    issue_number,
                )
                return True
            else:
                logger.warning(
                    "Failed to unassign Copilot from issue #%d - Status: %s, Response: %s",
                    issue_number,
                    response.status_code,
                    response.text[:500] if response.text else "empty",
                )
                # Don't fail - we'll try to assign anyway
                return True

        except Exception as e:
            logger.error("Error unassigning Copilot from issue #%d: %s", issue_number, e)
            # Don't fail - we'll try to assign anyway
            return True

    async def validate_assignee(
        self,
        access_token: str,
        owner: str,
        repo: str,
        username: str,
    ) -> bool:
        """
        Check if a user can be assigned to issues in a repository (T037).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            username: Username to validate

        Returns:
            True if user can be assigned
        """
        response = await self._client.get(
            f"https://api.github.com/repos/{owner}/{repo}/assignees/{username}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        # 204 means user can be assigned
        return response.status_code == 204

    async def get_repository_owner(
        self,
        access_token: str,
        owner: str,
        repo: str,
    ) -> str:
        """
        Get the repository owner username (T043).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner (may be org)
            repo: Repository name

        Returns:
            Owner username
        """
        response = await self._client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        response.raise_for_status()
        repo_data = response.json()

        # Return the owner login
        return repo_data.get("owner", {}).get("login", owner)

    async def get_project_repository(
        self,
        access_token: str,
        project_id: str,
    ) -> tuple[str, str] | None:
        """
        Get the repository associated with a project by examining project items.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID

        Returns:
            Tuple of (owner, repo_name) or None if no repository found
        """
        data = await self._graphql(
            access_token,
            GET_PROJECT_REPOSITORY_QUERY,
            {"projectId": project_id},
        )

        items = data.get("node", {}).get("items", {}).get("nodes", [])

        for item in items:
            content = item.get("content")
            if content and "repository" in content:
                repo_info = content["repository"]
                owner = repo_info.get("owner", {}).get("login", "")
                name = repo_info.get("name", "")
                if owner and name:
                    logger.info("Found repository %s/%s from project items", owner, name)
                    return owner, name

        logger.warning("No repository found in project %s items", project_id)
        return None
