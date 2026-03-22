from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
import asyncio
from typing import cast

from githubkit.exception import RequestFailed

from src.exceptions import ValidationError
from src.logging_utils import get_logger
from src.services.github_projects.graphql import (
    ADD_ISSUE_TO_PROJECT_MUTATION,
    DELETE_PROJECT_ITEM_MUTATION,
    GET_ISSUE_WITH_COMMENTS_QUERY,
    VERIFY_ITEM_ON_PROJECT_QUERY,
)

logger = get_logger(__name__)


class IssuesMixin:
    """Issue CRUD, sub-issues, comments, assignment, and project attachment."""

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
        milestone: int | None = None,
        assignees: list[str] | None = None,
    ) -> dict:
        """Create a GitHub Issue using the REST API."""
        payload: dict = {
            "title": title,
            "body": body,
            "labels": labels or [],
        }
        if milestone is not None:
            payload["milestone"] = milestone
        if assignees:
            payload["assignees"] = assignees

        try:
            issue = cast(
                dict,
                await self._rest(
                    access_token,
                    "POST",
                    f"/repos/{owner}/{repo}/issues",
                    json=payload,
                ),
            )
        except RequestFailed as exc:
            if exc.response.status_code == 404:
                raise ValidationError(
                    f"GitHub could not create an issue in {owner}/{repo}. "
                    "Your current GitHub session may be missing repository write access. "
                    "Log out and sign in again to refresh permissions."
                ) from exc
            raise

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
            await self._rest(
                access_token,
                "PATCH",
                f"/repos/{owner}/{repo}/issues/{issue_number}",
                json={"body": body},
            )
            logger.info("Updated body of issue #%d in %s/%s", issue_number, owner, repo)
            self._invalidate_cycle_cache(f"issue:{owner}/{repo}/{issue_number}")
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
        state: str | None = None,
        state_reason: str | None = None,
        labels_add: list[str] | None = None,
        labels_remove: list[str] | None = None,
    ) -> bool:
        """Update a GitHub issue's state and optionally adjust labels."""
        try:
            payload: dict = {}
            if state:
                payload["state"] = state
            if state_reason:
                payload["state_reason"] = state_reason

            if payload:
                await self._rest(
                    access_token,
                    "PATCH",
                    f"/repos/{owner}/{repo}/issues/{issue_number}",
                    json=payload,
                )

            if labels_add:
                await self._rest(
                    access_token,
                    "POST",
                    f"/repos/{owner}/{repo}/issues/{issue_number}/labels",
                    json={"labels": labels_add},
                )

            if labels_remove:
                for label in labels_remove:
                    try:
                        await self._rest(
                            access_token,
                            "DELETE",
                            f"/repos/{owner}/{repo}/issues/{issue_number}/labels/{label}",
                        )
                    except RequestFailed as exc:
                        if exc.response.status_code != 404:
                            raise

            self._invalidate_cycle_cache(f"issue:{owner}/{repo}/{issue_number}")
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
        issue_database_id: int | None = None,
    ) -> str:
        """
        Add an existing issue to a GitHub Project (T020).

        Uses ``_with_fallback()`` to implement a multi-strategy approach
        that works around a known GitHub API bug where items added via
        ``addProjectV2ItemById`` (GraphQL) or the REST API may not appear
        in the project's ``items()`` connection, despite being visible
        through the issue's ``projectItems`` connection.

        Strategy:
        1. Add via GraphQL ``addProjectV2ItemById`` (primary)
        2. Verify the item is on the project via the issue's
           ``projectItems`` (verify_fn)
        3. If verification fails and ``issue_database_id`` is provided,
           retry via REST API (fallback)

        The board reconciliation in ``get_board_data()`` provides an
        additional safety net by checking issue-side ``projectItems`` for
        any items the project-side ``items()`` connection missed.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            issue_node_id: GitHub Issue node ID
            issue_database_id: GitHub Issue database integer ID (for REST fallback)

        Returns:
            Project item ID
        """
        # Capture the GraphQL item_id so fallback can reference it
        graphql_item_id: str = ""

        async def _primary() -> str:
            nonlocal graphql_item_id
            data = await self._graphql(
                access_token,
                ADD_ISSUE_TO_PROJECT_MUTATION,
                {"projectId": project_id, "contentId": issue_node_id},
            )
            graphql_item_id = data.get("addProjectV2ItemById", {}).get("item", {}).get("id", "")
            logger.info(
                "Added issue %s to project via GraphQL, item_id: %s",
                issue_node_id,
                graphql_item_id,
            )
            return graphql_item_id

        async def _verify() -> bool:
            return await self._verify_item_on_project(access_token, issue_node_id, project_id)

        async def _fallback() -> str:
            if not issue_database_id:
                # No REST fallback possible without database ID — return
                # the GraphQL item_id as best-effort result.
                return graphql_item_id
            rest_item_id = await self._add_issue_to_project_rest(
                access_token=access_token,
                project_id=project_id,
                item_id=graphql_item_id,
                issue_database_id=issue_database_id,
            )
            return rest_item_id or graphql_item_id

        result = await self._with_fallback(
            primary_fn=_primary,
            fallback_fn=_fallback,
            operation=f"add issue {issue_node_id} to project {project_id}",
            verify_fn=_verify,
        )
        # Soft-failure contract: _with_fallback returns None on total
        # failure.  Fall back to the GraphQL item_id (possibly empty).
        return result or graphql_item_id

    async def _verify_item_on_project(
        self,
        access_token: str,
        issue_node_id: str,
        project_id: str,
    ) -> bool:
        """
        Verify an issue is on a project by querying the issue's projectItems.

        The issue-side ``projectItems`` connection is always consistent and
        reliable, unlike the project-side ``items()`` connection.

        Args:
            access_token: GitHub OAuth access token
            issue_node_id: GitHub Issue node ID
            project_id: GitHub Project V2 node ID

        Returns:
            True if the issue is found on the project
        """
        try:
            await asyncio.sleep(1)  # Brief delay for propagation
            data = await self._graphql(
                access_token,
                VERIFY_ITEM_ON_PROJECT_QUERY,
                {"issueId": issue_node_id},
            )
            project_items = data.get("node", {}).get("projectItems", {}).get("nodes", [])
            for pi in project_items:
                if (
                    pi
                    and not pi.get("isArchived", False)
                    and pi.get("project", {}).get("id") == project_id
                ):
                    return True
            return False
        except Exception as e:
            logger.debug("Verification query failed: %s", e)
            return False

    async def _add_issue_to_project_rest(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        issue_database_id: int,
    ) -> str | None:
        """
        Add an issue to a project via the REST API as a fallback strategy.

        Deletes the existing GraphQL-created item first, then re-adds via
        the REST ``POST /users/{owner}/projectsV2/{number}/items`` (or
        the org equivalent) endpoint. This uses a different internal GitHub
        code path that may handle project indexing differently.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Existing project item ID (from GraphQL) to delete first
            issue_database_id: GitHub Issue integer database ID

        Returns:
            New project item node_id from the REST API, or None on failure
        """
        try:
            # Get project number and owner type
            rest_info = await self._get_project_rest_info(access_token, project_id)
            if not rest_info:
                logger.warning("Could not resolve project REST info for %s", project_id)
                return None

            project_number, owner_type, owner_login = rest_info

            # Delete existing item
            if item_id:
                try:
                    await self._graphql(
                        access_token,
                        DELETE_PROJECT_ITEM_MUTATION,
                        {"projectId": project_id, "itemId": item_id},
                    )
                    logger.info("Deleted item %s before REST re-add", item_id)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.debug("Failed to delete item before REST re-add: %s", e)

            # Build REST API URL based on owner type
            if owner_type == "Organization":
                path = f"/orgs/{owner_login}/projectsV2/{project_number}/items"
            else:
                path = f"/users/{owner_login}/projectsV2/{project_number}/items"

            response = await self._rest_response(
                access_token,
                "POST",
                path,
                json={"type": "Issue", "id": issue_database_id},
            )

            if response.status_code in (200, 201):
                result = response.json()
                node_id = result.get("node_id") or result.get("value", {}).get("node_id", "")
                logger.info(
                    "REST API added issue (db_id=%d) to project %s/%d, node_id: %s",
                    issue_database_id,
                    owner_login,
                    project_number,
                    node_id,
                )
                return node_id
            else:
                logger.warning(
                    "REST API add item returned status %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return None

        except Exception as e:
            logger.warning("REST API fallback failed: %s", e)
            return None

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
        response = await self._rest_response(
            access_token,
            "PATCH",
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            json={"assignees": assignees},
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
        *,
        max_pages: int = 10,
    ) -> dict:
        """
        Fetch issue details including title, body, and all comments.

        Uses cursor-based pagination to retrieve all comments (FR-021).
        Each page fetches up to 100 comments; pagination continues until
        ``hasNextPage`` is False or ``max_pages`` is reached (safety cap).

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            max_pages: Maximum pagination requests (default 10 = 1000 comments)

        Returns:
            Dict with issue title, body, and comments list
        """
        cache_key = f"issue:{owner}/{repo}/{issue_number}"

        async def _fetch() -> dict:
            all_comments: list[dict] = []
            title = ""
            body = ""
            author_login = ""
            cursor: str | None = None

            for _page in range(max_pages):
                variables: dict = {
                    "owner": owner,
                    "name": repo,
                    "number": issue_number,
                }
                if cursor is not None:
                    variables["after"] = cursor

                data = await self._graphql(
                    access_token,
                    GET_ISSUE_WITH_COMMENTS_QUERY,
                    variables,
                )

                issue = data.get("repository", {}).get("issue", {})

                # Capture title/body/author from the first page only
                if not title:
                    title = issue.get("title", "")
                    body = issue.get("body", "")
                    author_login = (issue.get("author") or {}).get("login", "")

                comments_data = issue.get("comments", {})
                nodes = comments_data.get("nodes", [])
                all_comments.extend(
                    {
                        "node_id": c.get("id", ""),
                        "database_id": c.get("databaseId"),
                        "author": c.get("author", {}).get("login", "unknown"),
                        "body": c.get("body", ""),
                        "created_at": c.get("createdAt", ""),
                    }
                    for c in nodes
                )

                page_info = comments_data.get("pageInfo", {})
                if not page_info.get("hasNextPage", False):
                    break
                cursor = page_info.get("endCursor")

            return {
                "title": title,
                "body": body,
                "comments": all_comments,
                "user": {"login": author_login},
            }

        try:
            return await self._cycle_cached(cache_key, _fetch)
        except Exception as e:
            logger.error("Failed to fetch issue #%d with comments: %s", issue_number, e)
            return {"title": "", "body": "", "comments": [], "user": {"login": ""}}

    async def check_issue_closed(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> bool:
        """
        Check if a GitHub Issue is closed.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number

        Returns:
            True if the issue state is 'closed'
        """
        try:
            issue_data = cast(
                dict,
                await self._rest(
                    access_token, "GET", f"/repos/{owner}/{repo}/issues/{issue_number}"
                ),
            )
            return issue_data.get("state", "") == "closed"
        except RequestFailed as e:
            # 404 / 410 means the issue was deleted — treat as closed so
            # the chore's open-instance slot is freed up.
            if e.response.status_code in (404, 410):
                logger.info(
                    "Issue #%d returned %d — treating as closed (deleted)",
                    issue_number,
                    e.response.status_code,
                )
                return True
            logger.warning("Error checking issue #%d state: %s", issue_number, e)
            return False
        except Exception as e:
            logger.warning("Error checking issue #%d state: %s", issue_number, e)
            return False

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
        response = await self._rest_response(
            access_token,
            "GET",
            f"/repos/{owner}/{repo}/assignees/{username}",
        )

        # 204 means user can be assigned
        return response.status_code == 204

    async def get_issue_node_and_project_item(
        self,
        access_token: str,
        owner: str,
        repo: str,
        issue_number: int,
        project_id: str,
    ) -> tuple[str | None, str | None]:
        """Return the issue node id and matching project item id for an issue."""
        try:
            issue_data = await self._rest(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/issues/{issue_number}",
            )
        except Exception as exc:
            logger.warning(
                "Failed to load issue #%d from %s/%s: %s",
                issue_number,
                owner,
                repo,
                exc,
            )
            return None, None

        if not isinstance(issue_data, dict):
            logger.warning("Unexpected issue payload for #%d in %s/%s", issue_number, owner, repo)
            return None, None

        issue_node_id = issue_data.get("node_id")
        if not issue_node_id:
            logger.warning("Issue #%d in %s/%s has no node_id", issue_number, owner, repo)
            return None, None

        query = """
        query($issueId: ID!) {
            node(id: $issueId) {
                ... on Issue {
                    projectItems(first: 10) {
                        nodes {
                            id
                            project { id }
                        }
                    }
                }
            }
        }
        """

        try:
            data = await self._graphql(access_token, query, {"issueId": issue_node_id})
        except Exception as exc:
            logger.warning(
                "Failed to query project items for issue #%d (%s): %s",
                issue_number,
                issue_node_id,
                exc,
            )
            return issue_node_id, None

        nodes = data.get("node", {}).get("projectItems", {}).get("nodes", [])
        item_id: str | None = None
        for node in nodes:
            if node.get("project", {}).get("id") == project_id:
                item_id = node.get("id")
                break

        if not item_id and nodes:
            item_id = nodes[0].get("id")

        if not item_id:
            try:
                item_id = await self.add_issue_to_project(
                    access_token=access_token,
                    project_id=project_id,
                    issue_node_id=issue_node_id,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to attach issue #%d to project %s: %s",
                    issue_number,
                    project_id,
                    exc,
                )

        return issue_node_id, item_id

    # ──────────────────────────────────────────────────────────────────
    # Sub-Issues
    # ──────────────────────────────────────────────────────────────────

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
        # Route through _request_with_retry so transient 502/503 errors are
        # retried automatically — prevents orphaned sub-issues.
        try:
            await self._rest(
                access_token,
                "POST",
                f"/repos/{owner}/{repo}/issues/{parent_issue_number}/sub_issues",
                json={"sub_issue_id": sub_issue["id"]},
            )
            logger.info(
                "Attached sub-issue #%d to parent issue #%d",
                sub_issue_number,
                parent_issue_number,
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
        from src.services.cache import cache, cached_fetch, get_sub_issues_cache_key

        cache_key = get_sub_issues_cache_key(owner, repo, issue_number)

        async def _fetch() -> list:
            response = await self._rest_response(
                access_token,
                "GET",
                f"/repos/{owner}/{repo}/issues/{issue_number}/sub_issues",
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

        try:
            return await cached_fetch(cache, cache_key, _fetch, ttl_seconds=600)
        except Exception as e:
            logger.debug("Failed to get sub-issues for issue #%d: %s", issue_number, e)
            return []

    # ──────────────────────────────────────────────────────────────────
    # Issue Comments and PR File Content
    # ──────────────────────────────────────────────────────────────────

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
            response = await self._rest_response(
                access_token,
                "POST",
                f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
                json={"body": body},
            )

            if response.status_code in (200, 201):
                result = response.json()
                logger.info(
                    "Created comment on issue #%d (id=%s)",
                    issue_number,
                    result.get("id"),
                )
                self._invalidate_cycle_cache(f"issue:{owner}/{repo}/{issue_number}")
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

    async def delete_issue_comment(
        self,
        access_token: str,
        owner: str,
        repo: str,
        comment_database_id: int,
        issue_number: int | None = None,
    ) -> bool:
        """Delete a comment on a GitHub Issue by its database ID.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            comment_database_id: The integer database ID of the comment
            issue_number: Optional issue number for cache invalidation

        Returns:
            True if the comment was deleted successfully
        """
        try:
            response = await self._rest_response(
                access_token,
                "DELETE",
                f"/repos/{owner}/{repo}/issues/comments/{comment_database_id}",
            )

            if response.status_code == 204:
                logger.info(
                    "Deleted comment %d on %s/%s",
                    comment_database_id,
                    owner,
                    repo,
                )
                if issue_number is not None:
                    self._invalidate_cycle_cache(f"issue:{owner}/{repo}/{issue_number}")
                return True
            else:
                logger.error(
                    "Failed to delete comment %d: %s %s",
                    comment_database_id,
                    response.status_code,
                    response.text[:300] if response.text else "",
                )
                return False

        except Exception as e:
            logger.error("Error deleting comment %d: %s", comment_database_id, e)
            return False
