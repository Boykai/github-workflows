from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
from datetime import datetime

from src.logging_utils import get_logger
from src.services.github_projects.graphql import (
    ASSIGN_COPILOT_MUTATION,
    GET_PULL_REQUEST_QUERY,
    GET_SUGGESTED_ACTORS_QUERY,
    REQUEST_COPILOT_REVIEW_MUTATION,
)

# Configurable delay (seconds) before status/assignment updates.
API_ACTION_DELAY_SECONDS: float = 2.0

logger = get_logger(__name__)


class CopilotMixin:
    """Copilot assignment, review, polling, and session error detection."""

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
                graphql_features=[
                    "issues_copilot_assignment_api_support",
                    "coding_agent_model_selection",
                ],
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

            # Scan comments in reverse chronological order for the most recent marker.
            # Use exact line matching to avoid false positives from comments
            # that mention the marker in narrative text (e.g. analysis comments).
            for comment in reversed(comments):
                body = comment.get("body", "")
                if any(line.strip() == marker for line in body.split("\n")):
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
            import asyncio

            # Use REST API to remove Copilot assignee
            response = await self._rest_response(
                access_token,
                "DELETE",
                f"/repos/{owner}/{repo}/issues/{issue_number}/assignees",
                json={"assignees": ["copilot-swe-agent[bot]"]},
            )

            if response.status_code == 200:
                # Verify Copilot was actually removed from assignees
                result = response.json()
                remaining = [a.get("login", "") for a in result.get("assignees", [])]
                copilot_gone = not any(self.is_copilot_author(a) for a in remaining)
                logger.info(
                    "Unassigned Copilot from issue #%d (remaining assignees: %s, copilot_removed: %s)",
                    issue_number,
                    remaining,
                    copilot_gone,
                )
                # Give GitHub a moment to propagate the unassignment
                await asyncio.sleep(API_ACTION_DELAY_SECONDS)
                self._invalidate_cycle_cache(f"assigned:{owner}/{repo}/{issue_number}")
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
        cache_key = f"assigned:{owner}/{repo}/{issue_number}"

        async def _fetch() -> bool:
            issue_data = await self._rest(
                access_token, "GET", f"/repos/{owner}/{repo}/issues/{issue_number}"
            )
            if not isinstance(issue_data, dict):
                logger.warning("Unexpected response for issue #%d", issue_number)
                return True

            assignees = issue_data.get("assignees", [])
            for assignee in assignees:
                login = assignee.get("login") or ""
                if self.is_copilot_author(login):
                    return True
            return False

        try:
            return await self._cycle_cached(cache_key, _fetch)
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
        model: str = "claude-opus-4.6",
    ) -> bool:
        """
        Assign GitHub Copilot to an issue using GraphQL API with agent assignment.

        Uses the GraphQL ``addAssigneesToAssignable`` mutation with the
        ``agentAssignment`` input which explicitly supports ``customAgent``.
        Falls back to the REST API if GraphQL fails.

        NOTE: Evaluated for ``_with_fallback()`` adoption (Phase 2, US3).
        **Not applied** because:
        1. A conditional pre-step (unassign custom agent) executes before
           the primary/fallback flow — ``_with_fallback()`` does not model
           "do X before trying primary".
        2. Returns ``bool``, not ``T | None``.  The caller would need to
           handle ``None`` as ``False``, adding indirection without benefit.
        See research.md Task 7 for full rationale.

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
        # The built-in GitHub Copilot agent is the default assignment path,
        # not a repository custom agent defined under .github/agents/.
        normalized_custom_agent = "" if custom_agent == "copilot" else custom_agent

        logger.info(
            "Assigning Copilot to issue #%s (node=%s) for %s/%s with custom_agent='%s', base_ref='%s', model='%s', instructions_len=%d",
            issue_number,
            issue_node_id,
            owner,
            repo,
            normalized_custom_agent,
            base_ref,
            model,
            len(custom_instructions or ""),
        )

        # If this is a custom agent assignment, unassign Copilot first — but
        # ONLY if Copilot is currently assigned. Skipping this for new issues
        # avoids a race condition where the recovery loop sees "Copilot NOT
        # assigned" between the unassign and re-assign steps.
        if normalized_custom_agent and issue_number:
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
        logger.info(
            "Attempting GraphQL Copilot assignment for issue #%s with custom_agent='%s'",
            issue_number,
            normalized_custom_agent,
        )
        graphql_success = await self._assign_copilot_graphql(
            access_token,
            owner,
            repo,
            issue_node_id,
            base_ref,
            normalized_custom_agent,
            custom_instructions,
            model=model,
        )

        if graphql_success:
            logger.info(
                "GraphQL Copilot assignment succeeded for issue #%s with custom_agent='%s'",
                issue_number,
                normalized_custom_agent,
            )
            if issue_number:
                self._invalidate_cycle_cache(f"assigned:{owner}/{repo}/{issue_number}")
            return True

        # Fall back to REST API if GraphQL failed
        if not issue_number:
            logger.warning("GraphQL assignment failed and no issue_number for REST fallback")
            return False

        logger.warning(
            "GraphQL Copilot assignment failed for issue #%s; falling back to REST with custom_agent='%s', base_ref='%s', model='%s'",
            issue_number,
            normalized_custom_agent,
            base_ref,
            model,
        )
        return await self._assign_copilot_rest(
            access_token,
            owner,
            repo,
            issue_number,
            base_ref,
            normalized_custom_agent,
            custom_instructions,
            model=model,
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
        model: str = "claude-opus-4.6",
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
            model: Model to run for the assigned agent

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
                    "model": model,
                },
            }

            logger.info(
                "REST fallback: Assigning Copilot to issue #%d for %s/%s with custom_agent='%s', base_ref='%s', model='%s', instructions_len=%d",
                issue_number,
                owner,
                repo,
                custom_agent,
                base_ref,
                model,
                len(custom_instructions or ""),
            )

            response = await self._rest_response(
                access_token,
                "POST",
                f"/repos/{owner}/{repo}/issues/{issue_number}/assignees",
                json=payload,
            )

            if response.status_code in (200, 201):
                result = response.json()
                assignees = [a.get("login", "") for a in result.get("assignees", [])]
                logger.info(
                    "REST: Assigned Copilot to issue #%d with custom agent '%s', assignees: %s, status=%d",
                    issue_number,
                    custom_agent,
                    assignees,
                    response.status_code,
                )
                self._invalidate_cycle_cache(f"assigned:{owner}/{repo}/{issue_number}")
                return True
            else:
                logger.error(
                    "REST API failed to assign Copilot to issue #%d for %s/%s with custom_agent='%s', base_ref='%s', model='%s' - Status: %s, Response: %s",
                    issue_number,
                    owner,
                    repo,
                    custom_agent,
                    base_ref,
                    model,
                    response.status_code,
                    response.text[:500] if response.text else "empty",
                )
                return False

        except Exception as e:
            logger.error(
                "REST fallback failed for issue #%d for %s/%s with custom_agent='%s', base_ref='%s', model='%s': %s",
                issue_number,
                owner,
                repo,
                custom_agent,
                base_ref,
                model,
                e,
            )
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
        model: str = "claude-opus-4.6",
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
            logger.info(
                "GraphQL: Preparing Copilot assignment for %s/%s issue_node=%s with custom_agent='%s', base_ref='%s', model='%s', instructions_len=%d",
                owner,
                repo,
                issue_node_id,
                custom_agent,
                base_ref,
                model,
                len(custom_instructions or ""),
            )
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
                    "model": model,
                },
                graphql_features=[
                    "issues_copilot_assignment_api_support",
                    "coding_agent_model_selection",
                ],
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
                    "GraphQL: Assigned Copilot with custom agent '%s' for %s/%s issue_node=%s, assignees: %s",
                    custom_agent,
                    owner,
                    repo,
                    issue_node_id,
                    assigned_logins,
                )
            else:
                logger.info(
                    "GraphQL: Assigned Copilot to %s/%s issue_node=%s, assignees: %s",
                    owner,
                    repo,
                    issue_node_id,
                    assigned_logins,
                )

            return True

        except Exception as e:
            logger.error(
                "GraphQL failed to assign Copilot for %s/%s issue_node=%s with custom_agent='%s', base_ref='%s', model='%s': %s",
                owner,
                repo,
                issue_node_id,
                custom_agent,
                base_ref,
                model,
                e,
            )
            return False

    async def request_copilot_review(
        self,
        access_token: str,
        pr_node_id: str,
        pr_number: int | None = None,
        *,
        owner: str = "",
        repo: str = "",
    ) -> bool:
        """
        Request a code review from GitHub Copilot on a pull request.

        Uses the REST API ``POST /repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers``
        with ``reviewers: ["copilot-pull-request-reviewer[bot]"]``.
        This is the documented way to programmatically request a Copilot
        code review and does NOT consume the GraphQL rate limit.

        Falls back to the GraphQL ``requestReviews`` mutation with
        ``botIds`` when owner/repo are not provided (legacy callers).

        Args:
            access_token: GitHub OAuth access token
            pr_node_id: Pull request node ID (GraphQL ID) — used by GraphQL fallback
            pr_number: Pull request number (required for REST path)
            owner: Repository owner (required for REST path)
            repo: Repository name (required for REST path)

        Returns:
            True if review was successfully requested
        """
        # ── Primary path: REST API (preferred — no GraphQL rate-limit cost) ──
        if pr_number and owner and repo:
            try:
                response = await self._rest_response(
                    access_token,
                    "POST",
                    f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
                    json={"reviewers": ["copilot-pull-request-reviewer[bot]"]},
                )

                if response.status_code in (200, 201):
                    logger.info(
                        "Successfully requested Copilot code review on PR #%d "
                        "via REST API (status=%d)",
                        pr_number,
                        response.status_code,
                    )
                    return True

                # 422 often means the bot isn't available or PR is draft
                body = response.text[:500] if response.text else ""
                logger.warning(
                    "REST Copilot review request for PR #%d returned %d: %s",
                    pr_number,
                    response.status_code,
                    body,
                )
                # Fall through to GraphQL fallback
            except Exception as e:
                logger.warning(
                    "REST Copilot review request failed for PR #%d, trying GraphQL fallback: %s",
                    pr_number,
                    e,
                )

        # ── Fallback: GraphQL requestReviews with botIds ──
        try:
            data = await self._graphql(
                access_token,
                REQUEST_COPILOT_REVIEW_MUTATION,
                {"pullRequestId": pr_node_id},
                graphql_features=["copilot_code_review"],
            )

            pr = data.get("requestReviews", {}).get("pullRequest", {})
            if pr:
                logger.info(
                    "Successfully requested Copilot review for PR #%d via GraphQL: %s",
                    pr.get("number") or pr_number or 0,
                    pr.get("url", ""),
                )
                return True
            else:
                logger.warning("GraphQL Copilot review request may have failed: %s", data)
                return False

        except Exception as e:
            logger.error("Failed to request Copilot review for PR #%d: %s", pr_number or 0, e)
            return False

    async def dismiss_copilot_reviews(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
        *,
        submitted_before: datetime | None = None,
    ) -> int:
        """Dismiss all Copilot reviewer bot reviews on a pull request.

        GitHub can auto-trigger Copilot reviews when a PR is opened.  This
        method dismisses those reviews so the pipeline can request a fresh
        one whose completion timestamp is unambiguous.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            submitted_before: If provided, only dismiss reviews submitted
                **before** this UTC timestamp (to avoid dismissing a review
                that Solune itself requested).

        Returns:
            Number of reviews dismissed.
        """
        dismissed = 0
        try:
            reviews_result = await self._rest(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                params={"per_page": 100},
            )
            reviews = reviews_result if isinstance(reviews_result, list) else []

            for review in reviews:
                user = review.get("user", {}) if isinstance(review, dict) else {}
                review_id = review.get("id") if isinstance(review, dict) else None
                state = (
                    (review.get("state", "") if isinstance(review, dict) else "") or ""
                ).upper()
                submitted_at = review.get("submitted_at") if isinstance(review, dict) else None

                if not (user and review_id and self.is_copilot_reviewer_bot(user.get("login", ""))):
                    continue

                # Only dismiss completed (non-PENDING) reviews
                if state == "PENDING":
                    continue

                # Honour the submitted_before filter
                if submitted_before and submitted_at:
                    from datetime import datetime as _dt

                    try:
                        review_ts = _dt.fromisoformat(submitted_at)
                        if review_ts >= submitted_before:
                            continue  # Review is after the cutoff — keep it
                    except (ValueError, TypeError):
                        pass  # Cannot parse — dismiss to be safe

                try:
                    resp = await self._rest_response(
                        access_token,
                        "PUT",
                        f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews/{review_id}/dismissals",
                        json={
                            "message": (
                                "Dismissed: auto-triggered review replaced by "
                                "Solune pipeline-requested review"
                            ),
                        },
                    )
                    if resp.status_code in (200, 201):
                        dismissed += 1
                        logger.info(
                            "Dismissed auto-triggered Copilot review %s on PR #%d "
                            "(state=%s, submitted_at=%s)",
                            review_id,
                            pr_number,
                            state,
                            submitted_at,
                        )
                    else:
                        logger.warning(
                            "Failed to dismiss Copilot review %s on PR #%d: %d %s",
                            review_id,
                            pr_number,
                            resp.status_code,
                            resp.text[:300] if resp.text else "",
                        )
                except Exception as exc:
                    logger.warning(
                        "Error dismissing Copilot review %s on PR #%d: %s",
                        review_id,
                        pr_number,
                        exc,
                    )

        except Exception as e:
            logger.warning(
                "Failed to list/dismiss Copilot reviews on PR #%d: %s",
                pr_number,
                e,
            )

        if dismissed:
            logger.info(
                "Dismissed %d auto-triggered Copilot review(s) on PR #%d",
                dismissed,
                pr_number,
            )
        return dismissed

    async def has_copilot_reviewed_pr(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
        min_submitted_after: datetime | None = None,
    ) -> bool:
        """
        Check if GitHub Copilot has already reviewed a pull request.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            min_submitted_after: If provided, only count reviews submitted
                after this UTC timestamp.  This filters out GitHub
                auto-triggered reviews that were submitted before Solune
                explicitly requested the copilot-review step.

        Returns:
            True if Copilot has submitted a qualifying review
        """
        _ts_suffix = f":{min_submitted_after.isoformat()}" if min_submitted_after else ""
        cache_key = f"reviewed:{owner}/{repo}/{pr_number}{_ts_suffix}"

        async def _fetch() -> bool:
            try:
                requested = await self._rest(
                    access_token,
                    "GET",
                    f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
                )
                requested_users = requested.get("users", []) if isinstance(requested, dict) else []
                copilot_still_requested = any(
                    isinstance(user, dict) and self.is_copilot_reviewer_bot(user.get("login", ""))
                    for user in requested_users
                )
                if copilot_still_requested:
                    logger.debug(
                        "Copilot reviewer is still requested on PR #%d; review not complete yet",
                        pr_number,
                    )
                    return False

                reviews_result = await self._rest(
                    access_token,
                    "GET",
                    f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                    params={"per_page": 100},
                )
                reviews = reviews_result if isinstance(reviews_result, list) else []

                for review in reviews:
                    user = review.get("user", {}) if isinstance(review, dict) else {}
                    state = (
                        (review.get("state", "") if isinstance(review, dict) else "") or ""
                    ).upper()
                    body = (review.get("body", "") if isinstance(review, dict) else "") or ""
                    submitted_at = review.get("submitted_at") if isinstance(review, dict) else None
                    if (
                        user
                        and self.is_copilot_reviewer_bot(user.get("login", ""))
                        and state != "PENDING"
                        and submitted_at
                        and body.strip()
                    ):
                        # Filter out reviews submitted before Solune requested
                        if min_submitted_after:
                            from datetime import datetime as _dt

                            try:
                                review_ts = _dt.fromisoformat(submitted_at)
                                if review_ts <= min_submitted_after:
                                    logger.debug(
                                        "Ignoring Copilot review on PR #%d submitted at %s "
                                        "(before Solune request at %s)",
                                        pr_number,
                                        submitted_at,
                                        min_submitted_after.isoformat(),
                                    )
                                    continue
                            except (ValueError, TypeError):
                                pass  # Cannot parse — accept the review
                        logger.info(
                            "Found submitted Copilot review on PR #%d via REST "
                            "(state: %s, submitted_at: %s, body_len: %d)",
                            pr_number,
                            state,
                            submitted_at,
                            len(body),
                        )
                        return True

                return False
            except Exception as e:
                logger.warning(
                    "REST Copilot review status check failed for PR #%d; falling back to GraphQL: %s",
                    pr_number,
                    e,
                )

            data = await self._graphql(
                access_token,
                GET_PULL_REQUEST_QUERY,
                {"owner": owner, "name": repo, "number": pr_number},
            )

            pr = data.get("repository", {}).get("pullRequest", {})
            if not pr:
                return False

            review_requests = pr.get("reviewRequests", {}).get("nodes", [])
            if any(
                self.is_copilot_reviewer_bot(
                    (node.get("requestedReviewer", {}) if isinstance(node, dict) else {}).get(
                        "login", ""
                    )
                )
                for node in review_requests
            ):
                logger.debug(
                    "Copilot reviewer is still requested on PR #%d per GraphQL; review not complete yet",
                    pr_number,
                )
                return False

            reviews = pr.get("reviews", {}).get("nodes", [])

            # Check if any submitted review was posted by the dedicated
            # Copilot pull-request reviewer bot. Require a submission
            # timestamp and a non-empty body to guard against transient
            # placeholder review objects.
            for review in reviews:
                author = review.get("author", {})
                state = review.get("state", "")
                body = review.get("body", "")
                submitted_at = review.get("submittedAt")
                if (
                    author
                    and self.is_copilot_reviewer_bot(author.get("login", ""))
                    and state != "PENDING"
                    and submitted_at
                    and body.strip()
                ):
                    # Filter out reviews submitted before Solune requested
                    if min_submitted_after:
                        from datetime import datetime as _dt

                        try:
                            review_ts = _dt.fromisoformat(submitted_at)
                            if review_ts <= min_submitted_after:
                                logger.debug(
                                    "Ignoring Copilot review on PR #%d submitted at %s "
                                    "(before Solune request at %s) via GraphQL",
                                    pr_number,
                                    submitted_at,
                                    min_submitted_after.isoformat(),
                                )
                                continue
                        except (ValueError, TypeError):
                            pass  # Cannot parse — accept the review
                    logger.info(
                        "Found submitted Copilot review on PR #%d via GraphQL "
                        "(state: %s, submitted_at: %s, body_len: %d)",
                        pr_number,
                        state,
                        submitted_at,
                        len(body),
                    )
                    return True

            return False

        try:
            return await self._cycle_cached(cache_key, _fetch)
        except Exception as e:
            logger.error("Failed to check Copilot review status for PR #%d: %s", pr_number, e)
            return False

    def check_copilot_finished_events(self, events: list[dict]) -> bool:
        """
        Check if the Copilot SWE agent has finished work based on timeline events.

        Copilot is considered finished when one of these events exists:
        - 'copilot_work_finished' event
        - 'review_requested' event where review_requester is the SWE agent
          (NOT the Copilot pull-request reviewer bot, which can auto-trigger
          on WIP/draft PRs)

        Args:
            events: List of timeline events

        Returns:
            True if the SWE agent has finished work
        """
        for event in events:
            event_type = event.get("event", "")

            # Check for copilot_work_finished event
            if event_type == "copilot_work_finished":
                logger.info("Found 'copilot_work_finished' timeline event")
                return True

            # Check for review_requested event from the SWE agent specifically.
            # Auto-triggered Copilot code reviews (e.g. copilot-pull-request-
            # reviewer[bot]) must NOT be treated as agent work completion.
            if event_type == "review_requested":
                review_requester = event.get("review_requester", {})
                requester_login = review_requester.get("login", "")
                if self.is_copilot_swe_agent(requester_login):
                    logger.info(
                        "Found 'review_requested' event from SWE agent for reviewer: %s",
                        event.get("requested_reviewer", {}).get("login"),
                    )
                    return True

        return False

    def check_copilot_stopped_events(self, events: list[dict]) -> bool:
        """
        Check if the Copilot SWE agent has stopped/errored based on timeline events.

        Copilot is considered errored when a ``copilot_work_stopped`` event
        exists in the PR timeline.  This happens when Copilot encounters
        a fatal error (e.g. billing misconfiguration, rate limits) and
        stops working on the PR.

        Args:
            events: List of timeline events

        Returns:
            True if the SWE agent has stopped due to an error
        """
        for event in events:
            event_type = event.get("event", "")
            if event_type == "copilot_work_stopped":
                logger.warning("Found 'copilot_work_stopped' timeline event — Copilot errored")
                return True
        return False

    async def check_copilot_session_error(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> bool:
        """
        Check if the Copilot agent has stopped/errored on a PR.

        Detects both timeline events (``copilot_work_stopped``) and
        error comments posted by the Copilot SWE agent bot (e.g.
        "Copilot stopped work on behalf of … due to an error").

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            True if Copilot has errored/stopped on the PR
        """
        # Check timeline events first (cheapest signal)
        timeline_events = await self.get_pr_timeline_events(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=pr_number,
        )
        if self.check_copilot_stopped_events(timeline_events):
            return True

        # Fall back to checking PR comments for error messages
        try:
            issue_data = await self.get_issue_with_comments(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=pr_number,
            )
            for comment in issue_data.get("comments", []):
                author = (comment.get("author", "") or "").lower()
                body = comment.get("body", "") or ""
                if self.is_copilot_swe_agent(author) and "stopped work" in body.lower():
                    logger.warning(
                        "Found Copilot error comment on PR #%d: %.200s",
                        pr_number,
                        body,
                    )
                    return True
        except Exception as e:
            logger.debug("Could not check PR #%d comments for Copilot errors: %s", pr_number, e)

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
                if self.is_copilot_author(author):
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

                                event_time = _dt.fromisoformat(created_at_str)
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

                    copilot_finished = self.check_copilot_finished_events(timeline_events)

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

                    # Fallback: Title-based completion detection (when timeline
                    # API fails).  Copilot creates draft PRs with a "[WIP]"
                    # title prefix and removes it when work is finished.  If the
                    # timeline API returned no events (likely 403 or other API
                    # error) but the title no longer has the "[WIP]" prefix,
                    # treat as completed.
                    if not timeline_events:
                        pr_title = pr_details.get("title", "")
                        if pr_title and not pr_title.startswith("[WIP]"):
                            logger.info(
                                "Copilot PR #%d title '%s' has no '[WIP]' prefix and "
                                "timeline events unavailable — treating as completed "
                                "(title-based fallback)",
                                pr_number,
                                pr_title[:80],
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
