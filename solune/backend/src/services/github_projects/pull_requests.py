from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
from src.logging_utils import get_logger
from src.services.github_projects.graphql import (
    CREATE_PULL_REQUEST_MUTATION,
    GET_ISSUE_LINKED_PRS_QUERY,
    GET_PULL_REQUEST_QUERY,
    MARK_PR_READY_FOR_REVIEW_MUTATION,
    MERGE_PULL_REQUEST_MUTATION,
)

logger = get_logger(__name__)


class PullRequestsMixin:
    """Pull request operations — lookup, linking, merging, timeline, and changed files."""

    # ──────────────────────────────────────────────────────────────────
    # Pull Request Detection and Management
    # ──────────────────────────────────────────────────────────────────

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
            response = await self._rest_response(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/pulls",
                params={
                    "state": "open",
                    "per_page": 30,
                    "sort": "created",
                    "direction": "desc",
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

        NOTE: Evaluated for ``_with_fallback()`` adoption (Phase 2, US3).
        **Not applied** because the post-processing (filter by Copilot
        author, pick first match) diverges between the primary (GraphQL
        timeline) and fallback (REST search) paths.  Extracting both
        into ``primary_fn`` / ``fallback_fn`` lambdas would hide
        important filtering logic, increasing indirection without
        reducing code or improving clarity.
        See research.md Task 7 for full rationale.

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
                        pr for pr in rest_prs if self.is_copilot_author(pr.get("author", ""))
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
                if pr.get("state") == "OPEN" and self.is_copilot_author(pr.get("author", ""))
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
                        pr for pr in rest_prs if self.is_copilot_author(pr.get("author", ""))
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
        cache_key = f"linked_prs:{owner}/{repo}/{issue_number}"

        async def _fetch() -> list[dict]:
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
                if (pr and pr.get("__typename") == "PullRequest") or (pr and "number" in pr):
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

        try:
            return await self._cycle_cached(cache_key, _fetch)
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
        cache_key = f"pr:{owner}/{repo}/{pr_number}"

        async def _fetch() -> dict | None:
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
                "changed_files": pr.get("changedFiles", -1),
                "last_commit": last_commit,
                "check_status": check_status,  # SUCCESS, FAILURE, PENDING, etc.
            }

        try:
            return await self._cycle_cached(cache_key, _fetch)
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
                # Invalidate cached PR details — draft status changed
                pr_num = pr.get("number")
                if pr_num:
                    for key in list(self._cycle_cache):
                        if key.startswith("pr:") and key.endswith(f"/{pr_num}"):
                            del self._cycle_cache[key]
                return True
            else:
                logger.warning("PR may not have been marked ready: %s", pr)
                return False

        except Exception as e:
            logger.error("Failed to mark PR ready for review: %s", e)
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
                # Invalidate cached PR details — state changed
                merged_num = result.get("number") or pr_number
                if merged_num:
                    for key in list(self._cycle_cache):
                        if key.startswith("pr:") and key.endswith(f"/{merged_num}"):
                            del self._cycle_cache[key]
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
            response = await self._rest_response(
                access_token,
                "PATCH",
                f"/repos/{owner}/{repo}/pulls/{pr_number}",
                json={"base": base},
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

            response = await self._rest_response(
                access_token,
                "PATCH",
                f"/repos/{owner}/{repo}/pulls/{pr_number}",
                json={"body": updated_body},
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
                self._invalidate_cycle_cache(
                    f"linked_prs:{owner}/{repo}/{issue_number}",
                    f"pr:{owner}/{repo}/{pr_number}",
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
        cache_key = f"timeline:{owner}/{repo}/{issue_number}"

        async def _fetch() -> list:
            result = await self._rest(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/issues/{issue_number}/timeline",
            )
            return result if isinstance(result, list) else []

        try:
            return await self._cycle_cached(cache_key, _fetch)
        except Exception as e:
            logger.error(
                "Failed to get timeline events for issue #%d: %s",
                issue_number,
                e,
            )
            return []

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
            response = await self._rest_response(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/pulls/{pr_number}/files",
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

    async def create_pull_request(
        self,
        access_token: str,
        repository_id: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str,
        draft: bool = False,
    ) -> dict | None:
        """Create a Pull Request.

        Args:
            access_token: GitHub OAuth token.
            repository_id: Repository node ID.
            title: PR title.
            body: PR body (markdown).
            head_branch: Bare head branch name.
            base_branch: Bare base branch name.
            draft: Whether to create as draft.

        Returns:
            ``{"id": str, "number": int, "url": str}`` on success, ``None`` on failure.
        """
        try:
            data = await self._graphql(
                access_token,
                CREATE_PULL_REQUEST_MUTATION,
                {
                    "repositoryId": repository_id,
                    "title": title,
                    "body": body,
                    "headRefName": head_branch,
                    "baseRefName": base_branch,
                },
            )
            pr = (data.get("createPullRequest") or {}).get("pullRequest") or {}
            result = {
                "id": pr.get("id", ""),
                "number": pr.get("number", 0),
                "url": pr.get("url", ""),
            }
            logger.info("Created PR #%d: %s", result["number"], title)
            return result
        except ValueError as exc:
            error_msg = str(exc).lower()
            # PR already exists for this head→base — treat as existing
            if "already exists" in error_msg or "pull request already exists" in error_msg:
                logger.info("PR for %s→%s already exists", head_branch, base_branch)
                return {"id": "", "number": 0, "url": "", "existing": True}
            logger.error("Failed to create PR: %s", exc)
            return None

    # ──────────────────────────────────────────────────────────────────
    # Auto Merge Helpers
    # ──────────────────────────────────────────────────────────────────

    async def get_check_runs_for_ref(
        self,
        access_token: str,
        owner: str,
        repo: str,
        ref: str,
    ) -> list[dict] | None:
        """Fetch check runs for a commit ref via REST API.

        GET /repos/{owner}/{repo}/commits/{ref}/check-runs

        Returns:
            List of check run dicts, or None on failure.
        """
        try:
            resp = await self._rest_response(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/commits/{ref}/check-runs",
            )
            if resp is None or resp.status_code != 200:
                logger.warning(
                    "Failed to fetch check runs for %s/%s ref=%s (status=%s)",
                    owner,
                    repo,
                    ref[:8],
                    resp.status_code if resp else "no response",
                )
                return None
            data = resp.json()
            return data.get("check_runs", [])
        except Exception:
            logger.error(
                "Error fetching check runs for %s/%s ref=%s",
                owner,
                repo,
                ref[:8],
                exc_info=True,
            )
            return None

    async def get_pr_mergeable_state(
        self,
        access_token: str,
        owner: str,
        repo: str,
        pr_number: int,
    ) -> str | None:
        """Fetch the mergeable state of a PR via GraphQL.

        Queries pullRequest.mergeable field which returns one of:
        MERGEABLE, CONFLICTING, or UNKNOWN.

        Returns:
            Mergeable state string, or None on failure.
        """
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
          repository(owner: $owner, name: $repo) {
            pullRequest(number: $number) {
              mergeable
            }
          }
        }
        """
        try:
            data = await self._graphql(
                access_token,
                query,
                {"owner": owner, "repo": repo, "number": pr_number},
            )
            pr = data.get("repository", {}).get("pullRequest", {})
            return pr.get("mergeable")
        except Exception:
            logger.error(
                "Error fetching mergeable state for PR #%d in %s/%s",
                pr_number,
                owner,
                repo,
                exc_info=True,
            )
            return None
