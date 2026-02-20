"""Mixin for pull request management operations."""

import logging

import httpx

from ._queries import (
    GET_ISSUE_LINKED_PRS_QUERY,
    GET_PULL_REQUEST_QUERY,
    MARK_PR_READY_FOR_REVIEW_MUTATION,
    MERGE_PULL_REQUEST_MUTATION,
    REQUEST_COPILOT_REVIEW_MUTATION,
)

logger = logging.getLogger(__name__)


class _PrOpsMixin:
    """Mixin for PR search, linking, review, merge, and completion detection."""

    async def _search_open_prs_for_issue_rest(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Search for open PRs related to an issue using the REST API.

        This is a fallback when GraphQL timeline events don't capture the
        PR link. Searches for open PRs whose title or body references the
        issue number (e.g., "Fixes #42", "Closes #42", "#42").

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number to search for

        Returns:
            List of PR dicts with number, state, is_draft, url, author, title
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                params={
                    "state": "open",
                    "per_page": 30,
                    "sort": "created",
                    "direction": "desc",
                },
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code != 200:
                logger.warning(
                    "REST PR search failed with status %d for issue #%d",
                    response.status_code,
                    issue_number,
                )
                return []

            all_prs = response.json()
            issue_ref = f"#{issue_number}"
            matched_prs = []

            for pr in all_prs:
                title = pr.get("title", "")
                body = pr.get("body", "") or ""
                head_branch = pr.get("head", {}).get("ref", "")

                # Match if issue number appears in title, body, or branch name
                # Branch patterns: copilot/fix-42, copilot/issue-42-desc, feature/42-fix
                branch_match = (
                    f"-{issue_number}" in head_branch
                    or f"/{issue_number}-" in head_branch
                    or f"/{issue_number}" == head_branch[-len(f"/{issue_number}") :]
                    or head_branch.endswith(f"-{issue_number}")
                )
                if issue_ref in title or issue_ref in body or branch_match:
                    matched_prs.append(
                        {
                            "id": pr.get("node_id"),
                            "number": pr.get("number"),
                            "title": title,
                            "state": "OPEN",
                            "is_draft": pr.get("draft", False),
                            "url": pr.get("html_url", ""),
                            "author": pr.get("user", {}).get("login", ""),
                            "head_ref": pr.get("head", {}).get("ref", ""),
                        }
                    )

            logger.info(
                "REST fallback found %d open PRs referencing issue #%d",
                len(matched_prs),
                issue_number,
            )
            return matched_prs

        except Exception as e:
            logger.error("REST PR search error for issue #%d: %s", issue_number, e)
            return []

    async def find_existing_pr_for_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> dict | None:
        """
        Find an existing open PR linked to an issue (created by Copilot).

        Used to ensure only one PR per issue. When a subsequent agent is
        assigned, we reuse the existing PR's branch as the ``baseRef``
        so the new agent pushes commits to the same branch and PR.

        Searches first via GraphQL timeline events, then falls back to
        the REST API to catch PRs not captured by timeline events.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            Dict with ``number``, ``head_ref``, ``url`` of the existing PR,
            or None if no existing PR is found.
        """
        try:
            # Strategy 1: GraphQL timeline events (CONNECTED_EVENT / CROSS_REFERENCED_EVENT)
            linked_prs = await self.get_linked_pull_requests(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            # Strategy 2: REST API fallback — search open PRs referencing the issue
            if not linked_prs:
                logger.info(
                    "No linked PRs found via timeline for issue #%d, trying REST fallback",
                    issue_number,
                )
                rest_prs = await self._search_open_prs_for_issue_rest(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )
                if rest_prs:
                    # REST results already have head_ref, pick the best one
                    copilot_prs = [
                        pr for pr in rest_prs if "copilot" in (pr.get("author", "") or "").lower()
                    ]
                    target_pr = (copilot_prs or rest_prs)[0]
                    result = {
                        "number": target_pr["number"],
                        "head_ref": target_pr["head_ref"],
                        "url": target_pr.get("url", ""),
                        "is_draft": target_pr.get("is_draft", False),
                    }
                    logger.info(
                        "REST fallback found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                        result["number"],
                        result["head_ref"],
                        result["is_draft"],
                        issue_number,
                    )
                    return result
                return None

            # Find the first OPEN PR (preferring Copilot-authored ones)
            copilot_prs = [
                pr
                for pr in linked_prs
                if pr.get("state") == "OPEN" and "copilot" in (pr.get("author", "") or "").lower()
            ]

            open_prs = [pr for pr in linked_prs if pr.get("state") == "OPEN"]

            target_pr = (copilot_prs or open_prs or [None])[0]
            if not target_pr:
                # All linked PRs are closed/merged — try REST fallback for open PRs
                rest_prs = await self._search_open_prs_for_issue_rest(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )
                if rest_prs:
                    copilot_rest = [
                        pr for pr in rest_prs if "copilot" in (pr.get("author", "") or "").lower()
                    ]
                    target_rest = (copilot_rest or rest_prs)[0]
                    result = {
                        "number": target_rest["number"],
                        "head_ref": target_rest["head_ref"],
                        "url": target_rest.get("url", ""),
                        "is_draft": target_rest.get("is_draft", False),
                    }
                    logger.info(
                        "REST fallback found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                        result["number"],
                        result["head_ref"],
                        result["is_draft"],
                        issue_number,
                    )
                    return result
                return None

            # Use head_ref directly from timeline if available (avoids extra API call)
            if target_pr.get("head_ref"):
                result = {
                    "number": target_pr["number"],
                    "head_ref": target_pr["head_ref"],
                    "url": target_pr.get("url", ""),
                    "is_draft": target_pr.get("is_draft", False),
                }
                logger.info(
                    "Found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                    result["number"],
                    result["head_ref"],
                    result["is_draft"],
                    issue_number,
                )
                return result

            # Fallback: fetch full PR details to get head_ref
            pr_details = await self.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=target_pr["number"],
            )

            if not pr_details or not pr_details.get("head_ref"):
                return None

            result = {
                "number": pr_details["number"],
                "head_ref": pr_details["head_ref"],
                "url": pr_details.get("url", ""),
                "is_draft": pr_details.get("is_draft", False),
            }

            logger.info(
                "Found existing PR #%d (branch: %s, draft: %s) for issue #%d",
                result["number"],
                result["head_ref"],
                result["is_draft"],
                issue_number,
            )
            return result

        except Exception as e:
            logger.error("Error finding existing PR for issue #%d: %s", issue_number, e)
            return None

    async def get_linked_pull_requests(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> list[dict]:
        """
        Get all pull requests linked to an issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            List of PR details with id, number, title, state, isDraft, url, author
        """
        try:
            data = await self._graphql(
                access_token,
                GET_ISSUE_LINKED_PRS_QUERY,
                {"owner": owner, "name": repo, "number": issue_number},
            )

            prs = []
            timeline_items = (
                data.get("repository", {})
                .get("issue", {})
                .get("timelineItems", {})
                .get("nodes", [])
            )

            for item in timeline_items:
                # Check ConnectedEvent
                pr = item.get("subject") if "subject" in item else item.get("source")
                if pr and pr.get("__typename") == "PullRequest" or (pr and "number" in pr):
                    prs.append(
                        {
                            "id": pr.get("id"),
                            "number": pr.get("number"),
                            "title": pr.get("title"),
                            "state": pr.get("state"),
                            "is_draft": pr.get("isDraft", False),
                            "url": pr.get("url"),
                            "head_ref": pr.get("headRefName", ""),
                            "author": pr.get("author", {}).get("login", ""),
                            "created_at": pr.get("createdAt"),
                            "updated_at": pr.get("updatedAt"),
                        }
                    )

            # Remove duplicates by PR number
            seen = set()
            unique_prs = []
            for pr in prs:
                if pr["number"] and pr["number"] not in seen:
                    seen.add(pr["number"])
                    unique_prs.append(pr)

            logger.info(
                "Found %d linked PRs for issue #%d: %s",
                len(unique_prs),
                issue_number,
                [pr["number"] for pr in unique_prs],
            )
            return unique_prs

        except Exception as e:
            logger.error("Failed to get linked PRs for issue #%d: %s", issue_number, e)
            return []

    async def get_pull_request(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> dict | None:
        """
        Get pull request details.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            PR details dict or None if not found
        """
        try:
            data = await self._graphql(
                access_token,
                GET_PULL_REQUEST_QUERY,
                {"owner": owner, "name": repo, "number": pr_number},
            )

            pr = data.get("repository", {}).get("pullRequest")
            if not pr:
                return None

            # Extract last commit info for completion detection
            last_commit = None
            check_status = None
            commits_data = pr.get("commits", {}).get("nodes", [])
            if commits_data and len(commits_data) > 0:
                commit_node = commits_data[0].get("commit", {})
                last_commit = {
                    "sha": commit_node.get("oid"),
                    "committed_date": commit_node.get("committedDate"),
                }
                status_rollup = commit_node.get("statusCheckRollup")
                if status_rollup:
                    check_status = status_rollup.get("state")

            return {
                "id": pr.get("id"),
                "number": pr.get("number"),
                "title": pr.get("title"),
                "body": pr.get("body"),
                "state": pr.get("state"),
                "is_draft": pr.get("isDraft", False),
                "url": pr.get("url"),
                "head_ref": pr.get("headRefName", ""),
                "base_ref": pr.get("baseRefName", ""),
                "author": pr.get("author", {}).get("login", ""),
                "created_at": pr.get("createdAt"),
                "updated_at": pr.get("updatedAt"),
                "last_commit": last_commit,
                "check_status": check_status,  # SUCCESS, FAILURE, PENDING, etc.
            }

        except Exception as e:
            logger.error("Failed to get PR #%d: %s", pr_number, e)
            return None

    async def mark_pr_ready_for_review(
        self,
        access_token: str,
        pr_node_id: str,
    ) -> bool:
        """
        Convert a draft PR to ready for review.

        Args:
            access_token: GitHub OAuth access token
            pr_node_id: Pull request node ID (GraphQL ID)

        Returns:
            True if successfully marked ready
        """
        try:
            data = await self._graphql(
                access_token,
                MARK_PR_READY_FOR_REVIEW_MUTATION,
                {"pullRequestId": pr_node_id},
            )

            pr = data.get("markPullRequestReadyForReview", {}).get("pullRequest", {})
            if pr and not pr.get("isDraft"):
                logger.info(
                    "Successfully marked PR #%d as ready for review: %s",
                    pr.get("number"),
                    pr.get("url"),
                )
                return True
            else:
                logger.warning("PR may not have been marked ready: %s", pr)
                return False

        except Exception as e:
            logger.error("Failed to mark PR ready for review: %s", e)
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

    async def merge_pull_request(
        self,
        access_token: str,
        pr_node_id: str,
        pr_number: int | None = None,
        commit_headline: str | None = None,
        merge_method: str = "SQUASH",
    ) -> dict | None:
        """
        Merge a pull request into its base branch.

        Used to merge child PR branches into the parent/main branch for an issue
        when an agent completes work.

        Args:
            access_token: GitHub OAuth access token
            pr_node_id: Pull request node ID (GraphQL ID)
            pr_number: Optional PR number for logging
            commit_headline: Optional custom commit message headline
            merge_method: Merge method - MERGE, SQUASH, or REBASE (default: SQUASH)

        Returns:
            Dict with merge details if successful, None otherwise
        """
        try:
            variables = {
                "pullRequestId": pr_node_id,
                "mergeMethod": merge_method,
            }
            if commit_headline:
                variables["commitHeadline"] = commit_headline

            data = await self._graphql(
                access_token,
                MERGE_PULL_REQUEST_MUTATION,
                variables,
            )

            result = data.get("mergePullRequest", {}).get("pullRequest", {})
            if result and result.get("merged"):
                logger.info(
                    "Successfully merged PR #%d (state=%s, merged_at=%s, commit=%s)",
                    result.get("number") or pr_number,
                    result.get("state"),
                    result.get("mergedAt"),
                    result.get("mergeCommit", {}).get("oid", "")[:8],
                )
                return {
                    "number": result.get("number"),
                    "state": result.get("state"),
                    "merged": result.get("merged"),
                    "merged_at": result.get("mergedAt"),
                    "merge_commit": result.get("mergeCommit", {}).get("oid"),
                    "url": result.get("url"),
                }
            else:
                logger.warning(
                    "PR #%d may not have been merged: %s",
                    pr_number or 0,
                    result,
                )
                return None

        except Exception as e:
            logger.error("Failed to merge PR #%d: %s", pr_number or 0, e)
            return None

    async def delete_branch(
        self,
        access_token: str,
        owner: str,
        repo: str,
        branch_name: str,
    ) -> bool:
        """
        Delete a branch from a repository.

        Used to clean up child PR branches after they are merged into the
        parent/main branch for an issue.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            branch_name: Name of the branch to delete (without refs/heads/ prefix)

        Returns:
            True if branch was deleted successfully
        """
        try:
            # Use REST API to delete the branch reference
            response = await self._client.delete(
                f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch_name}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 204:
                logger.info(
                    "Successfully deleted branch '%s' from %s/%s",
                    branch_name,
                    owner,
                    repo,
                )
                return True
            elif response.status_code == 422:
                # Branch doesn't exist or already deleted
                logger.debug(
                    "Branch '%s' does not exist or was already deleted",
                    branch_name,
                )
                return True
            else:
                logger.warning(
                    "Failed to delete branch '%s': %d %s",
                    branch_name,
                    response.status_code,
                    response.text,
                )
                return False

        except Exception as e:
            logger.error("Failed to delete branch '%s': %s", branch_name, e)
            return False

    async def update_pr_base(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
        base: str,
    ) -> bool:
        """
        Update the base branch of a pull request.

        Used to re-target child PRs that were created targeting 'main' (when
        Copilot branches from a commit SHA) so they target the issue's main
        branch instead. This ensures the child PR merges into the correct branch.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            base: New base branch name

        Returns:
            True if the base branch was updated successfully
        """
        try:
            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                json={"base": base},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 200:
                logger.info(
                    "Updated PR #%d base branch to '%s' in %s/%s",
                    pr_number,
                    base,
                    owner,
                    repo,
                )
                return True
            else:
                logger.warning(
                    "Failed to update PR #%d base branch to '%s': %d %s",
                    pr_number,
                    base,
                    response.status_code,
                    response.text[:300] if response.text else "empty",
                )
                return False

        except Exception as e:
            logger.error(
                "Failed to update PR #%d base branch to '%s': %s",
                pr_number,
                base,
                e,
            )
            return False

    async def link_pull_request_to_issue(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
        issue_number: int,
    ) -> bool:
        """
        Link a pull request to a GitHub issue by adding a closing reference.

        Prepends ``Closes #<issue_number>`` to the PR body so that GitHub
        displays the PR in the issue's Development sidebar and automatically
        closes the issue when the PR is merged.

        This is called once for the *first* PR created for an issue — the
        "main" branch that all subsequent agent child PRs merge into.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number
            issue_number: Issue number to link

        Returns:
            True if the PR body was updated successfully
        """
        try:
            # Fetch the current PR body first
            pr_details = await self.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=pr_number,
            )
            current_body = (pr_details or {}).get("body", "") or ""

            closing_ref = f"Closes #{issue_number}"

            # Don't duplicate if the reference already exists
            if closing_ref in current_body:
                logger.debug(
                    "PR #%d already references issue #%d — skipping link",
                    pr_number,
                    issue_number,
                )
                return True

            updated_body = f"{closing_ref}\n\n{current_body}" if current_body else closing_ref

            response = await self._client.patch(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
                json={"body": updated_body},
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )

            if response.status_code == 200:
                logger.info(
                    "Linked PR #%d to issue #%d ('%s') in %s/%s",
                    pr_number,
                    issue_number,
                    closing_ref,
                    owner,
                    repo,
                )
                return True
            else:
                logger.warning(
                    "Failed to link PR #%d to issue #%d: %d %s",
                    pr_number,
                    issue_number,
                    response.status_code,
                    response.text[:300] if response.text else "empty",
                )
                return False

        except Exception as e:
            logger.error(
                "Failed to link PR #%d to issue #%d: %s",
                pr_number,
                issue_number,
                e,
            )
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
        pipeline_started_at: "datetime | None" = None,
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

    async def get_pr_changed_files(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> list[dict]:
        """
        Get the list of files changed in a pull request.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            pr_number: Pull request number

        Returns:
            List of dicts with filename, status, additions, deletions, etc.
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"per_page": 100},
            )

            if response.status_code == 200:
                files = response.json()
                logger.info(
                    "PR #%d has %d changed files",
                    pr_number,
                    len(files),
                )
                return files
            else:
                logger.error(
                    "Failed to get files for PR #%d: %s",
                    pr_number,
                    response.status_code,
                )
                return []

        except Exception as e:
            logger.error("Error getting PR #%d files: %s", pr_number, e)
            return []

    async def get_file_content_from_ref(
        self,
        access_token: str,
        owner: str,
        repo: str,
        path: str,
        ref: str,
    ) -> str | None:
        """
        Get the content of a file from a specific branch/ref.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            path: File path within the repository
            ref: Git ref (branch name, commit SHA, etc.)

        Returns:
            File content as a string, or None if not found
        """
        try:
            response = await self._client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.raw+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                params={"ref": ref},
            )

            if response.status_code == 200:
                return response.text
            else:
                logger.warning(
                    "Failed to get file %s@%s: %s",
                    path,
                    ref,
                    response.status_code,
                )
                return None

        except Exception as e:
            logger.error("Error getting file %s@%s: %s", path, ref, e)
            return None
