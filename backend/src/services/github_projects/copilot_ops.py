"""Copilot and agent operations."""

from __future__ import annotations

import asyncio
import json as json_mod
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
import yaml

from src.models.chat import AgentSource, AvailableAgent

from .graphql_queries import (
    ASSIGN_COPILOT_MUTATION,
    GET_PULL_REQUEST_QUERY,
    GET_SUGGESTED_ACTORS_QUERY,
    REQUEST_COPILOT_REVIEW_MUTATION,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class CopilotOpsMixin:
    """Copilot assignment, completion detection, and agent discovery."""

    _client: httpx.AsyncClient

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

    async def request_copilot_review(
        self,
        access_token: str,
        pr_node_id: str,
        pr_number: int | None = None,
    ) -> bool:
        """
        Request a code review from GitHub Copilot on a pull request.

        Args:
            access_token: GitHub OAuth access token
            pr_node_id: Pull request node ID (GraphQL ID)
            pr_number: Optional PR number for logging

        Returns:
            True if review was successfully requested
        """
        try:
            data = await self._graphql(
                access_token,
                REQUEST_COPILOT_REVIEW_MUTATION,
                {"pullRequestId": pr_node_id},
                # Include Copilot code review feature flag
                extra_headers={"GraphQL-Features": "copilot_code_review"},
            )

            pr = data.get("requestReviewsByLogin", {}).get("pullRequest", {})
            if pr:
                logger.info(
                    "Successfully requested Copilot review for PR #%d: %s",
                    pr.get("number") or pr_number,
                    pr.get("url", ""),
                )
                return True
            else:
                logger.warning("Copilot review request may have failed: %s", data)
                return False

        except Exception as e:
            logger.error("Failed to request Copilot review for PR #%d: %s", pr_number or 0, e)
            return False

    async def has_copilot_reviewed_pr(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> bool:
        """
        Check if GitHub Copilot has already reviewed a pull request.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            True if Copilot has submitted a review
        """
        try:
            data = await self._graphql(
                access_token,
                GET_PULL_REQUEST_QUERY,
                {"owner": owner, "name": repo, "number": pr_number},
            )

            pr = data.get("repository", {}).get("pullRequest", {})
            if not pr:
                return False

            reviews = pr.get("reviews", {}).get("nodes", [])

            # Check if any review was submitted by copilot
            for review in reviews:
                author = review.get("author", {})
                if author and author.get("login", "").lower() == "copilot":
                    logger.info(
                        "Found existing Copilot review on PR #%d (state: %s)",
                        pr_number,
                        review.get("state"),
                    )
                    return True

            return False

        except Exception as e:
            logger.error("Failed to check Copilot review status for PR #%d: %s", pr_number, e)
            return False

    async def get_pr_timeline_events(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Get timeline events for a PR/issue using the GitHub REST API.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue/PR number

        Returns:
            List of timeline events
        """
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/timeline"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(
                "Failed to get timeline events for issue #%d: %s",
                issue_number,
                e,
            )
            return []

    def _check_copilot_finished_events(self, events: list[dict]) -> bool:
        """
        Check if Copilot has finished work based on timeline events.

        Copilot is considered finished when one of these events exists:
        - 'copilot_work_finished' event
        - 'review_requested' event where review_requester is Copilot

        Args:
            events: List of timeline events

        Returns:
            True if Copilot has finished work
        """
        for event in events:
            event_type = event.get("event", "")

            # Check for copilot_work_finished event
            if event_type == "copilot_work_finished":
                logger.info("Found 'copilot_work_finished' timeline event")
                return True

            # Check for review_requested event from Copilot
            if event_type == "review_requested":
                review_requester = event.get("review_requester", {})
                requester_login = review_requester.get("login", "").lower()
                if requester_login == "copilot":
                    logger.info(
                        "Found 'review_requested' event from Copilot for reviewer: %s",
                        event.get("requested_reviewer", {}).get("login"),
                    )
                    return True

        return False

    async def check_copilot_pr_completion(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        pipeline_started_at: datetime | None = None,
    ) -> dict | None:
        """
        Check if GitHub Copilot has finished work on a PR for an issue.

        Copilot completion is detected when:
        - A linked PR exists created by copilot-swe-agent[bot]
        - The PR state is OPEN (not CLOSED or MERGED)
        - The PR timeline has one of these events:
          - 'copilot_work_finished' event
          - 'review_requested' event where review_requester is Copilot

        When ``pipeline_started_at`` is provided, timeline events that
        occurred before this timestamp are ignored. This prevents stale
        events from earlier agents (e.g., speckit.specify) from being
        misattributed to the current agent (e.g., speckit.implement).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            pipeline_started_at: If provided, only consider timeline events
                after this time (filters stale events from earlier agents).

        Returns:
            Dict with PR details if Copilot has finished work, None otherwise
        """
        try:
            linked_prs = await self.get_linked_pull_requests(
                access_token, owner, repo, issue_number
            )

            for pr in linked_prs:
                author = pr.get("author", "").lower()
                state = pr.get("state", "")
                is_draft = pr.get("is_draft", True)
                raw_pr_number = pr.get("number")
                if raw_pr_number is None:
                    continue
                pr_number = int(raw_pr_number)

                # Check if this is a Copilot-created PR
                if "copilot" in author or author == "copilot-swe-agent[bot]":
                    logger.info(
                        "Found Copilot PR #%d for issue #%d: state=%s, is_draft=%s",
                        pr_number,
                        issue_number,
                        state,
                        is_draft,
                    )

                    # PR must be OPEN to be processable
                    if state != "OPEN":
                        logger.info(
                            "Copilot PR #%d is not open (state=%s), skipping",
                            pr_number,
                            state,
                        )
                        continue

                    # Get PR details for node ID
                    pr_details = await self.get_pull_request(access_token, owner, repo, pr_number)

                    if not pr_details:
                        logger.warning(
                            "Could not get details for PR #%d",
                            pr_number,
                        )
                        continue

                    # If PR is already not a draft, it's ready (maybe manually marked)
                    if not is_draft:
                        logger.info(
                            "Copilot PR #%d is already ready for review",
                            pr_number,
                        )
                        return {
                            **pr,
                            "id": pr_details.get("id"),
                            "copilot_finished": True,
                        }

                    # PR is still draft - check timeline events for Copilot finish signal
                    timeline_events = await self.get_pr_timeline_events(
                        access_token, owner, repo, pr_number
                    )

                    # If a pipeline start time was provided, filter out stale
                    # events from earlier agents.  This prevents e.g. a
                    # review_requested event from speckit.specify being
                    # mistaken for speckit.implement completing.
                    if pipeline_started_at is not None:
                        fresh_events = []
                        for ev in timeline_events:
                            created_at_str = ev.get("created_at", "")
                            if not created_at_str:
                                fresh_events.append(ev)
                                continue
                            try:
                                from datetime import datetime as _dt

                                event_time = _dt.fromisoformat(
                                    created_at_str.replace("Z", "+00:00")
                                )
                                cutoff = (
                                    pipeline_started_at.replace(tzinfo=event_time.tzinfo)
                                    if pipeline_started_at.tzinfo is None
                                    else pipeline_started_at
                                )
                                if event_time > cutoff:
                                    fresh_events.append(ev)
                            except (ValueError, TypeError):
                                fresh_events.append(ev)
                        logger.debug(
                            "Filtered timeline events for PR #%d: %d/%d after pipeline start %s",
                            pr_number,
                            len(fresh_events),
                            len(timeline_events),
                            pipeline_started_at.isoformat(),
                        )
                        timeline_events = fresh_events

                    copilot_finished = self._check_copilot_finished_events(timeline_events)

                    if copilot_finished:
                        logger.info(
                            "Copilot PR #%d has finished work (timeline events indicate completion)",
                            pr_number,
                        )
                        return {
                            **pr,
                            "id": pr_details.get("id"),
                            "last_commit": pr_details.get("last_commit"),
                            "copilot_finished": True,
                        }

                    # No finish events yet - Copilot is still working
                    logger.info(
                        "Copilot PR #%d has no finish events yet, still in progress",
                        pr_number,
                    )

            return None

        except Exception as e:
            logger.error(
                "Failed to check Copilot PR completion for issue #%d: %s",
                issue_number,
                e,
            )
            return None

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
        the repository's ``.github/agents/*.agent.md`` files.

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
