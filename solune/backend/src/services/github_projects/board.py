from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.models.board import BoardItem

from src.constants import StatusNames
from src.logging_utils import get_logger
from src.services.done_items_store import save_done_items
from src.services.github_projects.graphql import (
    BOARD_GET_PROJECT_ITEMS_QUERY,
    BOARD_LIST_PROJECTS_QUERY,
    BOARD_RECONCILE_ITEMS_QUERY,
)

logger = get_logger(__name__)


class BoardMixin:
    """Kanban board view — project board data with columns and items."""

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

            options = [
                StatusOption(
                    option_id=opt["id"],
                    name=opt["name"],
                    color=opt.get("color", "GRAY"),
                    description=opt.get("description"),
                )
                for opt in status_field_data.get("options", [])
            ]

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

    @staticmethod
    def _parse_board_item(item: dict, board_models: dict) -> BoardItem | None:
        """Parse a single GraphQL project item node into a BoardItem."""
        Assignee = board_models["Assignee"]
        BoardItem = board_models["BoardItem"]
        ContentType = board_models["ContentType"]
        CustomFieldValue = board_models["CustomFieldValue"]
        Label = board_models["Label"]
        LinkedPR = board_models["LinkedPR"]
        PRState = board_models["PRState"]
        Repository = board_models["Repository"]

        if not item:
            return None
        content = item.get("content", {})
        if not content:
            return None

        field_values = item.get("fieldValues", {}).get("nodes", [])
        status_name = ""
        status_option_id = ""
        priority_val = None
        size_val = None
        estimate_val = None

        for fv in field_values:
            if not fv:
                continue
            field_name = fv.get("field", {}).get("name", "")
            if field_name == "Status":
                status_name = fv.get("name", "")
                status_option_id = fv.get("optionId", "")
            elif field_name == "Priority":
                priority_val = CustomFieldValue(name=fv.get("name", ""), color=fv.get("color"))
            elif field_name == "Size":
                size_val = CustomFieldValue(name=fv.get("name", ""), color=fv.get("color"))
            elif field_name == "Estimate":
                num = fv.get("number")
                if num is not None:
                    estimate_val = float(num)

        if content.get("number") is not None and "state" in content:
            content_type = ContentType.PULL_REQUEST
        elif content.get("number") is not None:
            content_type = ContentType.ISSUE
        else:
            content_type = ContentType.DRAFT_ISSUE

        assignees = [
            Assignee(login=a["login"], avatar_url=a.get("avatarUrl", ""))
            for a in content.get("assignees", {}).get("nodes", [])
            if a
        ]

        repo_data = content.get("repository")
        repository = (
            Repository(
                owner=repo_data.get("owner", {}).get("login", ""), name=repo_data.get("name", "")
            )
            if repo_data
            else None
        )

        linked_prs: list = []
        seen_pr_ids: set[str] = set()
        for event in content.get("timelineItems", {}).get("nodes", []):
            if not event:
                continue
            pr_data = event.get("subject") or event.get("source")
            if pr_data and pr_data.get("id") and pr_data["id"] not in seen_pr_ids:
                seen_pr_ids.add(pr_data["id"])
                pr_state_raw = pr_data.get("state", "OPEN").upper()
                pr_state = (
                    PRState.MERGED
                    if pr_state_raw == "MERGED"
                    else PRState.CLOSED
                    if pr_state_raw == "CLOSED"
                    else PRState.OPEN
                )
                linked_prs.append(
                    LinkedPR(
                        pr_id=pr_data["id"],
                        number=pr_data.get("number", 0),
                        title=pr_data.get("title", ""),
                        state=pr_state,
                        url=pr_data.get("url", ""),
                    )
                )

        content_labels = [
            Label(id=ln.get("id", ""), name=ln.get("name", ""), color=ln.get("color", ""))
            for ln in content.get("labels", {}).get("nodes", [])
            if ln
        ]

        issue_type_data = content.get("issueType")
        issue_type_name: str | None = (
            issue_type_data.get("name") if isinstance(issue_type_data, dict) else None
        )

        milestone_data = content.get("milestone")
        return BoardItem(
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
            labels=content_labels,
            issue_type=issue_type_name,
            created_at=content.get("createdAt"),
            updated_at=content.get("updatedAt"),
            milestone=milestone_data.get("title") if milestone_data else None,
        )

    @staticmethod
    def _build_board_columns(
        all_items: list,
        status_options: list,
        board_models: dict,
    ) -> list:
        """Group board items into columns by status and filter out sub-issues."""
        BoardColumn = board_models["BoardColumn"]
        StatusOption = board_models["StatusOption"]
        StatusColor = board_models["StatusColor"]

        columns_map: dict[str, list] = {opt.option_id: [] for opt in status_options}
        no_status_items: list = []
        for board_item in all_items:
            if board_item.status_option_id in columns_map:
                columns_map[board_item.status_option_id].append(board_item)
            else:
                no_status_items.append(board_item)

        columns = []
        for opt in status_options:
            col_items = columns_map[opt.option_id]
            columns.append(
                BoardColumn(
                    status=opt,
                    items=col_items,
                    item_count=len(col_items),
                    estimate_total=sum(it.estimate or 0.0 for it in col_items),
                )
            )

        if no_status_items:
            columns.append(
                BoardColumn(
                    status=StatusOption(
                        option_id="__no_status__", name="No Status", color=StatusColor.GRAY
                    ),
                    items=no_status_items,
                    item_count=len(no_status_items),
                    estimate_total=sum(it.estimate or 0.0 for it in no_status_items),
                )
            )

        # Filter out sub-issues from all columns.
        # Primary: collect IDs referenced by parent items' sub_issues lists.
        # Secondary: items carrying the "sub-issue" label are also excluded,
        # which catches sub-issues whose parent didn't list them (API race,
        # parent not on the board, etc.).
        from src.constants import SUB_ISSUE_LABEL

        all_sub_issue_ids: set[str] = set()
        for board_item in all_items:
            for si in board_item.sub_issues:
                if si.id:
                    all_sub_issue_ids.add(si.id)

        def _is_sub_issue(item) -> bool:
            if item.content_id and item.content_id in all_sub_issue_ids:
                return True
            return any(lb.name == SUB_ISSUE_LABEL for lb in item.labels)

        for col in columns:
            original_count = len(col.items)
            col.items = [it for it in col.items if not _is_sub_issue(it)]
            if len(col.items) != original_count:
                col.item_count = len(col.items)
                col.estimate_total = sum(it.estimate or 0.0 for it in col.items)

        return columns

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
            Label,
            LinkedPR,
            PRState,
            Repository,
            StatusColor,
            StatusField,
            StatusOption,
            SubIssue,
        )

        board_models = {
            "Assignee": Assignee,
            "BoardColumn": BoardColumn,
            "BoardItem": BoardItem,
            "ContentType": ContentType,
            "CustomFieldValue": CustomFieldValue,
            "Label": Label,
            "LinkedPR": LinkedPR,
            "PRState": PRState,
            "Repository": Repository,
            "StatusColor": StatusColor,
            "StatusOption": StatusOption,
        }

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
                parsed = self._parse_board_item(item, board_models)
                if parsed:
                    all_items.append(parsed)

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

        # ── Reconciliation: supplement items that the project's items()
        # connection may not yet include due to a known GitHub API bug
        # where addProjectV2ItemById creates items that never appear in
        # ProjectV2.items(). This is confirmed to affect both the GraphQL
        # API and the REST API (POST /users/{owner}/projectsV2/{n}/items).
        # The issue's projectItems connection (which IS consistent) is
        # the only reliable way to verify an item is on a project.
        # We query recent issues from the repository and check their
        # projectItems to find any that are on this project but were not
        # returned by the main items() query.
        existing_content_ids = {item.content_id for item in all_items if item.content_id}
        repos_seen: set[tuple[str, str]] = set()
        for item in all_items:
            if item.repository:
                repos_seen.add((item.repository.owner, item.repository.name))

        # Also include the workflow config repo as a fallback source for
        # reconciliation. This handles the edge case where ALL items from
        # a repo are "ghost" items not returned by items().
        try:
            from src.services.workflow_orchestrator import get_workflow_config

            config = await get_workflow_config(project_id)
            if config and config.repository_owner and config.repository_name:
                repos_seen.add((config.repository_owner, config.repository_name))
        except Exception as e:
            logger.debug("Suppressed error: %s", e)

        for owner, repo_name in repos_seen:
            try:
                reconciled = await self._reconcile_board_items(
                    access_token=access_token,
                    owner=owner,
                    repo=repo_name,
                    project_id=project_id,
                    existing_content_ids=existing_content_ids,
                    limit=100,  # Check more issues for better coverage
                )
                if reconciled:
                    logger.info(
                        "Board reconciliation found %d missing items from %s/%s",
                        len(reconciled),
                        owner,
                        repo_name,
                    )
                    all_items.extend(reconciled)
            except Exception as e:
                logger.debug("Board reconciliation failed for %s/%s: %s", owner, repo_name, e)

        columns = self._build_board_columns(
            all_items, project_meta.status_field.options, board_models
        )

        # Persist Done board items to DB for fast cold-start loading
        done_board_items = [
            item.model_dump(mode="json") for item in all_items if item.status == StatusNames.DONE
        ]
        try:
            await save_done_items(project_id, done_board_items, item_type="board")
        except Exception:
            logger.debug("Non-critical: failed to persist done board items cache", exc_info=True)

        logger.info(
            "Board data for project %s: %d items across %d columns",
            project_id,
            len(all_items),
            len(columns),
        )

        return BoardDataResponse(project=project_meta, columns=columns)

    async def _reconcile_board_items(
        self,
        access_token: str,
        owner: str,
        repo: str,
        project_id: str,
        existing_content_ids: set[str],
        limit: int = 50,
    ) -> list:
        """
        Find project items that the ProjectV2.items() connection missed.

        GitHub's Projects V2 API has eventual consistency: items added via
        addProjectV2ItemById may not immediately appear in the project's
        items() connection, even though they ARE visible from the issue's
        projectItems connection. This method queries recent repository
        issues and checks their projectItems to find any that belong to
        this project but were not returned by the main items query.

        Args:
            access_token: GitHub OAuth access token
            owner: Repository owner
            repo: Repository name
            project_id: GitHub Project V2 node ID
            existing_content_ids: Set of issue/PR node IDs already in the board
            limit: Number of recent issues to check

        Returns:
            List of BoardItem objects for missing items
        """
        from src.models.board import (
            Assignee,
            BoardItem,
            ContentType,
            CustomFieldValue,
            LinkedPR,
            PRState,
            Repository,
            SubIssue,
        )

        data = await self._graphql(
            access_token,
            BOARD_RECONCILE_ITEMS_QUERY,
            {"owner": owner, "name": repo, "first": limit},
        )

        issues = data.get("repository", {}).get("issues", {}).get("nodes", [])

        reconciled_items: list[BoardItem] = []

        for issue in issues:
            if not issue:
                continue

            issue_id = issue.get("id", "")

            # Skip issues already in the board data
            if issue_id in existing_content_ids:
                continue

            # Check if this issue is on our target project
            project_items = issue.get("projectItems", {}).get("nodes", [])
            matching_pi = None
            for pi in project_items:
                if (
                    pi
                    and not pi.get("isArchived", False)
                    and pi.get("project", {}).get("id") == project_id
                ):
                    matching_pi = pi
                    break

            if not matching_pi:
                continue

            # Parse field values from the project item
            status_name = ""
            status_option_id = ""
            priority_val = None
            size_val = None
            estimate_val = None

            for fv in matching_pi.get("fieldValues", {}).get("nodes", []):
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

            # Parse assignees
            assignees = [
                Assignee(
                    login=a["login"],
                    avatar_url=a.get("avatarUrl", ""),
                )
                for a in issue.get("assignees", {}).get("nodes", [])
                if a
            ]

            # Parse repository
            repo_data = issue.get("repository")
            repository = None
            if repo_data:
                repository = Repository(
                    owner=repo_data.get("owner", {}).get("login", ""),
                    name=repo_data.get("name", ""),
                )

            # Parse linked PRs from timeline events
            linked_prs: list[LinkedPR] = []
            seen_pr_ids: set[str] = set()
            timeline = issue.get("timelineItems", {}).get("nodes", [])
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

            board_item = BoardItem(
                item_id=matching_pi["id"],
                content_id=issue_id,
                content_type=ContentType.ISSUE,
                title=issue.get("title", "Untitled"),
                number=issue.get("number"),
                repository=repository,
                url=issue.get("url"),
                body=issue.get("body"),
                status=status_name or "No Status",
                status_option_id=status_option_id,
                assignees=assignees,
                priority=priority_val,
                size=size_val,
                estimate=estimate_val,
                linked_prs=linked_prs,
            )

            # Fetch sub-issues for the reconciled item
            if board_item.number and repository:
                try:
                    raw_sub_issues = await self.get_sub_issues(
                        access_token=access_token,
                        owner=repository.owner,
                        repo=repository.name,
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
                        "Failed to fetch sub-issues for reconciled item #%s: %s",
                        board_item.number,
                        e,
                    )

            reconciled_items.append(board_item)

        return reconciled_items
