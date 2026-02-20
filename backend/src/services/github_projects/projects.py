"""Project listing and board operations."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.task import Task

from .graphql_queries import (
    BOARD_GET_PROJECT_ITEMS_QUERY,
    BOARD_LIST_PROJECTS_QUERY,
    GET_PROJECT_ITEMS_QUERY,
    LIST_ORG_PROJECTS_QUERY,
    LIST_USER_PROJECTS_QUERY,
)

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class ProjectsMixin:
    """Project listing and board display operations."""

    _client: httpx.AsyncClient

    async def list_user_projects(
        self, access_token: str, username: str, limit: int = 20
    ) -> list[GitHubProject]:
        """
        List projects owned by a user.

        Args:
            access_token: GitHub OAuth access token
            username: GitHub username
            limit: Maximum number of projects to return

        Returns:
            List of GitHubProject objects
        """
        data = await self._graphql(
            access_token,
            LIST_USER_PROJECTS_QUERY,
            {"login": username, "first": limit},
        )

        user_data = data.get("user")
        if not user_data:
            return []

        return self._parse_projects(
            user_data.get("projectsV2", {}).get("nodes", []),
            owner_login=username,
            project_type=ProjectType.USER,
        )

    async def list_org_projects(
        self, access_token: str, org: str, limit: int = 20
    ) -> list[GitHubProject]:
        """
        List projects owned by an organization.

        Args:
            access_token: GitHub OAuth access token
            org: Organization login name
            limit: Maximum number of projects to return

        Returns:
            List of GitHubProject objects
        """
        data = await self._graphql(
            access_token,
            LIST_ORG_PROJECTS_QUERY,
            {"login": org, "first": limit},
        )

        org_data = data.get("organization")
        if not org_data:
            return []

        return self._parse_projects(
            org_data.get("projectsV2", {}).get("nodes", []),
            owner_login=org,
            project_type=ProjectType.ORGANIZATION,
        )

    def _parse_projects(
        self, nodes: list[dict], owner_login: str, project_type: ProjectType
    ) -> list[GitHubProject]:
        """Parse GraphQL project nodes into GitHubProject models."""
        projects = []

        for node in nodes:
            if not node or node.get("closed"):
                continue

            # Parse status field
            status_columns = []
            status_field = node.get("field")
            if status_field:
                for option in status_field.get("options", []):
                    status_columns.append(
                        StatusColumn(
                            field_id=status_field["id"],
                            name=option["name"],
                            option_id=option["id"],
                            color=option.get("color"),
                        )
                    )

            # Default status columns if none found
            if not status_columns:
                from src.constants import DEFAULT_STATUS_COLUMNS

                status_columns = [
                    StatusColumn(field_id="", name=name, option_id="")
                    for name in DEFAULT_STATUS_COLUMNS
                ]

            projects.append(
                GitHubProject(
                    project_id=node["id"],
                    owner_id="",  # Not available in this query
                    owner_login=owner_login,
                    name=node["title"],
                    type=project_type,
                    url=node["url"],
                    description=node.get("shortDescription"),
                    status_columns=status_columns,
                    item_count=node.get("items", {}).get("totalCount"),
                    cached_at=datetime.utcnow(),
                )
            )

        return projects

    async def get_project_items(
        self, access_token: str, project_id: str, limit: int = 100
    ) -> list[Task]:
        """
        Get items (tasks) from a project with pagination support.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            limit: Maximum number of items per page (default 100)

        Returns:
            List of Task objects
        """
        all_tasks = []
        has_next_page = True
        after = None

        while has_next_page:
            data = await self._graphql(
                access_token,
                GET_PROJECT_ITEMS_QUERY,
                {"projectId": project_id, "first": limit, "after": after},
            )

            node = data.get("node")
            if not node:
                break

            items_data = node.get("items", {})
            items = items_data.get("nodes", [])
            page_info = items_data.get("pageInfo", {})

            for item in items:
                if not item:
                    continue

                content = item.get("content", {})
                if not content:
                    continue

                status_value = item.get("fieldValueByName", {})

                # Extract repository info if available
                repo_info = content.get("repository", {})
                repo_owner = repo_info.get("owner", {}).get("login") if repo_info else None
                repo_name = repo_info.get("name") if repo_info else None

                all_tasks.append(
                    Task(
                        project_id=project_id,
                        github_item_id=item["id"],
                        github_content_id=content.get("id"),
                        github_issue_id=(content.get("id") if content.get("number") else None),
                        issue_number=content.get("number"),
                        repository_owner=repo_owner,
                        repository_name=repo_name,
                        title=content.get("title", "Untitled"),
                        description=content.get("body"),
                        status=(status_value.get("name", "Todo") if status_value else "Todo"),
                        status_option_id=(status_value.get("optionId", "") if status_value else ""),
                    )
                )

            has_next_page = page_info.get("hasNextPage", False)
            after = page_info.get("endCursor")

            # Safety check to prevent infinite loops
            if not after:
                break

        logger.info("Fetched %d total tasks from project %s", len(all_tasks), project_id)
        return all_tasks

    # ──────────────────────────────────────────────────────────────────
    # Board feature methods
    # ──────────────────────────────────────────────────────────────────

    async def list_board_projects(self, access_token: str, username: str, limit: int = 20) -> list:
        """
        List projects with full status field configuration for board display.

        Args:
            access_token: GitHub OAuth access token
            username: GitHub username
            limit: Maximum number of projects

        Returns:
            List of BoardProject objects with status field options
        """
        from src.models.board import BoardProject, StatusField, StatusOption

        data = await self._graphql(
            access_token,
            BOARD_LIST_PROJECTS_QUERY,
            {"login": username, "first": limit},
        )

        user_data = data.get("user")
        if not user_data:
            return []

        projects = []
        for node in user_data.get("projectsV2", {}).get("nodes", []):
            if not node or node.get("closed"):
                continue

            status_field_data = node.get("field")
            if not status_field_data:
                continue  # Skip projects without a Status field

            options = []
            for opt in status_field_data.get("options", []):
                options.append(
                    StatusOption(
                        option_id=opt["id"],
                        name=opt["name"],
                        color=opt.get("color", "GRAY"),
                        description=opt.get("description"),
                    )
                )

            projects.append(
                BoardProject(
                    project_id=node["id"],
                    name=node["title"],
                    description=node.get("shortDescription"),
                    url=node["url"],
                    owner_login=username,
                    status_field=StatusField(
                        field_id=status_field_data["id"],
                        options=options,
                    ),
                )
            )

        return projects

    async def get_board_data(self, access_token: str, project_id: str, limit: int = 100):
        """
        Get full board data for a project: items with custom fields and linked PRs.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            limit: Maximum items per page

        Returns:
            BoardDataResponse with project metadata and columns
        """
        from src.models.board import (
            Assignee,
            BoardColumn,
            BoardDataResponse,
            BoardItem,
            BoardProject,
            ContentType,
            CustomFieldValue,
            LinkedPR,
            PRState,
            Repository,
            StatusColor,
            StatusField,
            StatusOption,
            SubIssue,
        )

        all_items: list[BoardItem] = []
        has_next_page = True
        after = None
        project_meta = None

        while has_next_page:
            data = await self._graphql(
                access_token,
                BOARD_GET_PROJECT_ITEMS_QUERY,
                {"projectId": project_id, "first": limit, "after": after},
            )

            node = data.get("node")
            if not node:
                break

            # Parse project metadata on first page
            if project_meta is None:
                status_field_data = node.get("field")
                if not status_field_data:
                    raise ValueError(f"Project {project_id} has no Status field")

                status_options = [
                    StatusOption(
                        option_id=opt["id"],
                        name=opt["name"],
                        color=opt.get("color", "GRAY"),
                        description=opt.get("description"),
                    )
                    for opt in status_field_data.get("options", [])
                ]

                owner_data = node.get("owner", {})
                owner_login = owner_data.get("login", "")

                project_meta = BoardProject(
                    project_id=project_id,
                    name=node.get("title", ""),
                    description=node.get("shortDescription"),
                    url=node.get("url", ""),
                    owner_login=owner_login,
                    status_field=StatusField(
                        field_id=status_field_data["id"],
                        options=status_options,
                    ),
                )

            items_data = node.get("items", {})
            page_info = items_data.get("pageInfo", {})

            for item in items_data.get("nodes", []):
                if not item:
                    continue

                content = item.get("content", {})
                if not content:
                    continue

                # Parse field values (Status, Priority, Size, Estimate)
                field_values = item.get("fieldValues", {}).get("nodes", [])
                status_name = ""
                status_option_id = ""
                priority_val = None
                size_val = None
                estimate_val = None

                for fv in field_values:
                    if not fv:
                        continue
                    field_info = fv.get("field", {})
                    field_name = field_info.get("name", "")

                    if field_name == "Status":
                        status_name = fv.get("name", "")
                        status_option_id = fv.get("optionId", "")
                    elif field_name == "Priority":
                        priority_val = CustomFieldValue(
                            name=fv.get("name", ""),
                            color=fv.get("color"),
                        )
                    elif field_name == "Size":
                        size_val = CustomFieldValue(
                            name=fv.get("name", ""),
                            color=fv.get("color"),
                        )
                    elif field_name == "Estimate":
                        num = fv.get("number")
                        if num is not None:
                            estimate_val = float(num)

                # Determine content type
                if content.get("number") is not None and "state" in content:
                    content_type = ContentType.PULL_REQUEST
                elif content.get("number") is not None:
                    content_type = ContentType.ISSUE
                else:
                    content_type = ContentType.DRAFT_ISSUE

                # Parse assignees
                assignees = []
                for assignee_node in content.get("assignees", {}).get("nodes", []):
                    if assignee_node:
                        assignees.append(
                            Assignee(
                                login=assignee_node["login"],
                                avatar_url=assignee_node.get("avatarUrl", ""),
                            )
                        )

                # Parse repository
                repo_data = content.get("repository")
                repository = None
                if repo_data:
                    repository = Repository(
                        owner=repo_data.get("owner", {}).get("login", ""),
                        name=repo_data.get("name", ""),
                    )

                # Parse linked PRs from timeline events
                linked_prs: list[LinkedPR] = []
                seen_pr_ids: set[str] = set()
                timeline = content.get("timelineItems", {}).get("nodes", [])
                for event in timeline:
                    if not event:
                        continue
                    pr_data = event.get("subject") or event.get("source")
                    if pr_data and pr_data.get("id"):
                        pr_id = pr_data["id"]
                        if pr_id not in seen_pr_ids:
                            seen_pr_ids.add(pr_id)
                            pr_state_raw = pr_data.get("state", "OPEN").upper()
                            if pr_state_raw == "MERGED":
                                pr_state = PRState.MERGED
                            elif pr_state_raw == "CLOSED":
                                pr_state = PRState.CLOSED
                            else:
                                pr_state = PRState.OPEN

                            linked_prs.append(
                                LinkedPR(
                                    pr_id=pr_id,
                                    number=pr_data.get("number", 0),
                                    title=pr_data.get("title", ""),
                                    state=pr_state,
                                    url=pr_data.get("url", ""),
                                )
                            )

                all_items.append(
                    BoardItem(
                        item_id=item["id"],
                        content_id=content.get("id"),
                        content_type=content_type,
                        title=content.get("title", "Untitled"),
                        number=content.get("number"),
                        repository=repository,
                        url=content.get("url"),
                        body=content.get("body"),
                        status=status_name or "No Status",
                        status_option_id=status_option_id,
                        assignees=assignees,
                        priority=priority_val,
                        size=size_val,
                        estimate=estimate_val,
                        linked_prs=linked_prs,
                    )
                )

            has_next_page = page_info.get("hasNextPage", False)
            after = page_info.get("endCursor")
            if not after:
                break

        if project_meta is None:
            raise ValueError(f"Project not found: {project_id}")

        # Fetch sub-issues for each issue item
        for board_item in all_items:
            if (
                board_item.content_type == ContentType.ISSUE
                and board_item.number is not None
                and board_item.repository
            ):
                try:
                    raw_sub_issues = await self.get_sub_issues(
                        access_token=access_token,
                        owner=board_item.repository.owner,
                        repo=board_item.repository.name,
                        issue_number=board_item.number,
                    )
                    for si in raw_sub_issues:
                        si_assignees = [
                            Assignee(
                                login=a.get("login", ""),
                                avatar_url=a.get("avatar_url", ""),
                            )
                            for a in si.get("assignees", [])
                            if isinstance(a, dict)
                        ]
                        # Detect agent from title: "[speckit.implement] Feature title"
                        si_title = si.get("title", "")
                        si_agent = None
                        if si_title.startswith("[") and "]" in si_title:
                            si_agent = si_title[1 : si_title.index("]")]
                        board_item.sub_issues.append(
                            SubIssue(
                                id=si.get("node_id", ""),
                                number=si.get("number", 0),
                                title=si_title,
                                url=si.get("html_url", ""),
                                state=si.get("state", "open"),
                                assigned_agent=si_agent,
                                assignees=si_assignees,
                            )
                        )
                except Exception as e:
                    logger.debug(
                        "Failed to fetch sub-issues for item #%s: %s",
                        board_item.number,
                        e,
                    )

        # Group items into columns by status
        status_options = project_meta.status_field.options

        # Also create a "No Status" column for items without a status
        columns_map: dict[str, list[BoardItem]] = {opt.option_id: [] for opt in status_options}
        no_status_items: list[BoardItem] = []

        for board_item in all_items:
            if board_item.status_option_id in columns_map:
                columns_map[board_item.status_option_id].append(board_item)
            else:
                no_status_items.append(board_item)

        columns: list[BoardColumn] = []
        for opt in status_options:
            col_items = columns_map[opt.option_id]
            estimate_total = sum(it.estimate or 0.0 for it in col_items)
            columns.append(
                BoardColumn(
                    status=opt,
                    items=col_items,
                    item_count=len(col_items),
                    estimate_total=estimate_total,
                )
            )

        # Append no-status column if there are unclassified items
        if no_status_items:
            no_status_option = StatusOption(
                option_id="__no_status__",
                name="No Status",
                color=StatusColor.GRAY,
            )
            estimate_total = sum(it.estimate or 0.0 for it in no_status_items)
            columns.append(
                BoardColumn(
                    status=no_status_option,
                    items=no_status_items,
                    item_count=len(no_status_items),
                    estimate_total=estimate_total,
                )
            )

        logger.info(
            "Board data for project %s: %d items across %d columns",
            project_id,
            len(all_items),
            len(columns),
        )

        return BoardDataResponse(project=project_meta, columns=columns)

    async def poll_project_changes(
        self,
        access_token: str,
        project_id: str,
        cached_tasks: list[Task],
        ready_status: str = "Ready",
        in_progress_status: str = "In Progress",
    ) -> dict:
        """
        Poll for changes in a project by comparing with cached state.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            cached_tasks: Previously cached task list
            ready_status: Name of the Ready status column
            in_progress_status: Name of the In Progress status column

        Returns:
            Dict with:
            - 'changes': list of detected changes
            - 'current_tasks': updated task list
            - 'workflow_triggers': tasks that need workflow processing
        """
        current_tasks = await self.get_project_items(access_token, project_id)
        changes = self._detect_changes(cached_tasks, current_tasks)

        # T041: Detect tasks that need workflow processing
        workflow_triggers = []

        for change in changes:
            if change.get("type") == "status_changed":
                new_status = change.get("new_status", "")

                # Detect Ready status (trigger In Progress + Copilot assignment)
                if new_status.lower() == ready_status.lower():
                    workflow_triggers.append(
                        {
                            "trigger": "ready_detected",
                            "task_id": change.get("task_id"),
                            "title": change.get("title"),
                        }
                    )

                # T046: Detect completion signals (In Progress → closed or labeled)
                # This is handled via labels/state, not status change
                # Status-based completion detection would be In Progress → Done
                # but spec says completion is via label or closed state

        # Also check for tasks currently in "In Progress" that might have completed PRs
        for task in current_tasks:
            if task.status and task.status.lower() == in_progress_status.lower():
                workflow_triggers.append(
                    {
                        "trigger": "in_progress_check",
                        "task_id": task.github_item_id,
                        "title": task.title,
                        "issue_id": task.github_issue_id,
                    }
                )

        return {
            "changes": changes,
            "current_tasks": current_tasks,
            "workflow_triggers": workflow_triggers,
        }
