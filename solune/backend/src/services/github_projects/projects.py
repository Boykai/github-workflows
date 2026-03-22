from __future__ import annotations

# pyright: reportAttributeAccessIssue=false
import asyncio

from src.constants import DEFAULT_STATUS_BACKLOG, StatusNames
from src.logging_utils import get_logger
from src.models.project import GitHubProject, ProjectType, StatusColumn
from src.models.task import Task
from src.services.done_items_store import save_done_items
from src.services.github_projects.graphql import (
    CREATE_DRAFT_ITEM_MUTATION,
    CREATE_PROJECT_V2_MUTATION,
    GET_PROJECT_FIELD_QUERY,
    GET_PROJECT_FIELDS_QUERY,
    GET_PROJECT_ITEMS_QUERY,
    GET_PROJECT_OWNER_INFO_QUERY,
    GET_PROJECT_REPOSITORY_QUERY,
    GET_PROJECT_STATUS_FIELD_QUERY,
    LINK_PROJECT_V2_TO_REPO_MUTATION,
    LIST_ORG_PROJECTS_QUERY,
    LIST_USER_PROJECTS_QUERY,
    SET_PROJECT_DEFAULT_REPOSITORY_MUTATION,
    UPDATE_DATE_FIELD_MUTATION,
    UPDATE_ITEM_STATUS_MUTATION,
    UPDATE_NUMBER_FIELD_MUTATION,
    UPDATE_PROJECT_V2_SINGLE_SELECT_FIELD_MUTATION,
    UPDATE_SINGLE_SELECT_FIELD_MUTATION,
    UPDATE_TEXT_FIELD_MUTATION,
)
from src.utils import utcnow

# Configurable delay (seconds) before status/assignment updates.
API_ACTION_DELAY_SECONDS: float = 2.0

logger = get_logger(__name__)

# Default Solune project status columns.
_SOLUNE_STATUS_OPTIONS = [
    {"name": "Todo", "color": "BLUE"},
    {"name": "Backlog", "color": "GRAY"},
    {"name": "Ready", "color": "PURPLE"},
    {"name": "In Progress", "color": "YELLOW"},
    {"name": "In Review", "color": "ORANGE"},
    {"name": "Done", "color": "GREEN"},
]


class ProjectsMixin:
    """Project listing, items, fields, status management, and change detection."""

    # ------------------------------------------------------------------
    # 049 — Project creation & linking
    # ------------------------------------------------------------------

    async def create_project_v2(
        self,
        access_token: str,
        owner: str,
        title: str,
    ) -> dict:
        """Create a GitHub Project V2 and best-effort configure status columns.

        Args:
            access_token: GitHub OAuth access token.
            owner: Owner login (user or org).
            title: Project title.

        Returns:
            ``{id, number, url}`` where *id* is the GraphQL node ID.
        """
        from typing import cast as _cast

        # Resolve the owner's node_id.
        # Try user first; fall back to org.
        try:
            user_data = _cast(dict, await self._rest(access_token, "GET", f"/users/{owner}"))
            owner_node_id: str = user_data["node_id"]
        except Exception:
            org_data = _cast(dict, await self._rest(access_token, "GET", f"/orgs/{owner}"))
            owner_node_id = org_data["node_id"]

        # Create the project.
        data = await self._graphql(
            access_token,
            CREATE_PROJECT_V2_MUTATION,
            {"ownerId": owner_node_id, "title": title},
        )
        project = (data.get("createProjectV2") or {}).get("projectV2") or {}
        project_id: str = project.get("id", "")
        result = {
            "id": project_id,
            "number": project.get("number"),
            "url": project.get("url", ""),
        }

        # Best-effort: configure the default Status field options.
        try:
            await self._configure_project_status(access_token, project_id)
        except Exception as exc:
            logger.warning(
                "Non-blocking: could not configure status columns for project %s: %s",
                project_id,
                exc,
            )

        return result

    async def _configure_project_status(
        self,
        access_token: str,
        project_id: str,
    ) -> None:
        """Set the Solune default status options on a project's Status field."""
        # Fetch the Status field ID.
        data = await self._graphql(
            access_token,
            GET_PROJECT_STATUS_FIELD_QUERY,
            {"projectId": project_id},
        )
        field = ((data.get("node") or {}).get("field")) or {}
        field_id = field.get("id")
        if not field_id:
            logger.debug("No Status field found for project %s", project_id)
            return

        await self._graphql(
            access_token,
            UPDATE_PROJECT_V2_SINGLE_SELECT_FIELD_MUTATION,
            {
                "fieldId": field_id,
                "options": _SOLUNE_STATUS_OPTIONS,
            },
        )
        logger.info("Configured Solune status columns for project %s", project_id)

    async def link_project_to_repository(
        self,
        access_token: str,
        project_id: str,
        repository_id: str,
    ) -> None:
        """Link a GitHub Project V2 to a repository.

        Args:
            access_token: GitHub OAuth access token.
            project_id: Project GraphQL node ID.
            repository_id: Repository GraphQL node ID.
        """
        await self._graphql(
            access_token,
            LINK_PROJECT_V2_TO_REPO_MUTATION,
            {"projectId": project_id, "repositoryId": repository_id},
        )
        logger.info("Linked project %s to repository %s", project_id, repository_id)

    async def set_project_default_repository(
        self,
        access_token: str,
        project_id: str,
        repository_id: str,
    ) -> None:
        """Set the default repository on a GitHub Project V2.

        The default repository is used when creating new issues from the
        project board.

        Args:
            access_token: GitHub OAuth access token.
            project_id: Project GraphQL node ID.
            repository_id: Repository GraphQL node ID.
        """
        await self._graphql(
            access_token,
            SET_PROJECT_DEFAULT_REPOSITORY_MUTATION,
            {"projectId": project_id, "repositoryId": repository_id},
        )
        logger.info("Set default repository %s on project %s", repository_id, project_id)

    async def delete_project_v2(
        self,
        access_token: str,
        project_id: str,
    ) -> bool:
        """Delete a GitHub Project V2 by its GraphQL node ID.

        Falls back to closing (archiving) the project when the deletion
        mutation is unavailable or fails due to permissions.

        Args:
            access_token: GitHub OAuth access token.
            project_id: Project GraphQL node ID (PVT_xxx).

        Returns:
            ``True`` if the project was deleted or closed.
        """
        delete_mutation = """
        mutation($projectId: ID!) {
          deleteProjectV2(input: {projectId: $projectId}) {
            projectV2 { id }
          }
        }
        """
        try:
            await self._graphql(access_token, delete_mutation, {"projectId": project_id})
            logger.info("Deleted project %s", project_id)
            return True
        except Exception as exc:
            logger.warning(
                "deleteProjectV2 failed for %s, falling back to close: %s", project_id, exc
            )

        # Fallback: archive/close the project instead of deleting
        close_mutation = """
        mutation($projectId: ID!) {
          updateProjectV2(input: {projectId: $projectId, closed: true}) {
            projectV2 { id closed }
          }
        }
        """
        try:
            await self._graphql(access_token, close_mutation, {"projectId": project_id})
            logger.info("Closed (archived) project %s", project_id)
            return True
        except Exception as exc:
            logger.warning("Could not close project %s: %s", project_id, exc)
            return False

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
                status_columns = [
                    StatusColumn(
                        field_id=status_field["id"],
                        name=option["name"],
                        option_id=option["id"],
                        color=option.get("color"),
                    )
                    for option in status_field.get("options", [])
                ]

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
                    cached_at=utcnow(),
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
        cache_key = f"items:{project_id}"

        async def _fetch() -> list[Task]:
            all_tasks: list[Task] = []
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

                    # Extract labels if available
                    labels_data = content.get("labels")
                    label_list = None
                    if labels_data:
                        label_list = [
                            {"name": ln.get("name", ""), "color": ln.get("color", "")}
                            for ln in labels_data.get("nodes", [])
                            if ln
                        ]

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
                            status=(
                                status_value.get("name", DEFAULT_STATUS_BACKLOG)
                                if status_value
                                else DEFAULT_STATUS_BACKLOG
                            ),
                            status_option_id=(
                                status_value.get("optionId", "") if status_value else ""
                            ),
                            labels=label_list,
                        )
                    )

                has_next_page = page_info.get("hasNextPage", False)
                after = page_info.get("endCursor")

                # Safety check to prevent infinite loops
                if not after:
                    break

            return all_tasks

        all_tasks = await self._cycle_cached(cache_key, _fetch)

        # Persist Done items to DB for fast cold-start loading
        done_tasks = [t.model_dump(mode="json") for t in all_tasks if t.status == StatusNames.DONE]
        try:
            await save_done_items(project_id, done_tasks, item_type="task")
        except Exception:
            logger.debug("Non-critical: failed to persist done tasks cache", exc_info=True)

        logger.info("Fetched %d total tasks from project %s", len(all_tasks), project_id)
        return all_tasks

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
        # Add delay before status update (rate limiting / UX improvement)
        await asyncio.sleep(API_ACTION_DELAY_SECONDS)

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

    async def _get_project_rest_info(
        self,
        access_token: str,
        project_id: str,
    ) -> tuple[int, str, str] | None:
        """
        Get project number, owner type, and owner login for REST API calls.

        Returns:
            Tuple of (project_number, owner_type, owner_login) or None on failure.
            owner_type is 'User' or 'Organization'.
        """
        try:
            data = await self._graphql(
                access_token,
                GET_PROJECT_OWNER_INFO_QUERY,
                {"projectId": project_id},
            )
            node = data.get("node", {})
            project_number = node.get("number")
            owner = node.get("owner", {})
            owner_type = owner.get("__typename", "")
            owner_login = owner.get("login", "")

            if project_number and owner_type and owner_login:
                return (project_number, owner_type, owner_login)
            return None
        except Exception as e:
            logger.debug("Failed to get project REST info: %s", e)
            return None

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

    async def update_item_status_by_name(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        status_name: str,
    ) -> bool:
        """
        Update an item's status by status name (helper method).

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            status_name: Status name (e.g., "Ready", "In Progress")

        Returns:
            True if update succeeded
        """
        # Get project field info
        data = await self._graphql(
            access_token,
            GET_PROJECT_FIELD_QUERY,
            {"projectId": project_id},
        )

        field_data = data.get("node", {}).get("field", {})
        field_id = field_data.get("id")
        options = field_data.get("options", [])

        if not field_id:
            logger.error("Could not find Status field in project %s", project_id)
            return False

        # Find matching option
        option_id = None
        for opt in options:
            if opt.get("name", "").lower() == status_name.lower():
                option_id = opt.get("id")
                break

        if not option_id:
            logger.error(
                "Could not find status option '%s' in project %s",
                status_name,
                project_id,
            )
            return False

        # Update status
        return await self.update_item_status(
            access_token=access_token,
            project_id=project_id,
            item_id=item_id,
            field_id=field_id,
            option_id=option_id,
        )

    async def update_sub_issue_project_status(
        self,
        access_token: str,
        project_id: str,
        sub_issue_node_id: str,
        status_name: str,
    ) -> bool:
        """
        Update a sub-issue's Status field on the project board.

        Sub-issues automatically inherit the parent issue's project, so they
        already have a project item.  This method queries the sub-issue's
        ``projectItems`` connection to find its project-item ID, then delegates
        to ``update_item_status_by_name`` to set the Status column.

        Returns ``True`` on success, ``False`` otherwise.
        """
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
            data = await self._graphql(access_token, query, {"issueId": sub_issue_node_id})
        except Exception as exc:
            logger.warning(
                "GraphQL projectItems query failed for sub-issue %s: %s",
                sub_issue_node_id,
                exc,
            )
            return False

        nodes = data.get("node", {}).get("projectItems", {}).get("nodes", [])

        # Find the project item that belongs to *our* project
        item_id: str | None = None
        for node in nodes:
            if node.get("project", {}).get("id") == project_id:
                item_id = node["id"]
                break

        if not item_id and nodes:
            # Fallback: use the first project item if project_id didn't match
            item_id = nodes[0]["id"]

        if not item_id:
            # Sub-issue is not on the project yet — add it and retry
            logger.info(
                "Sub-issue %s has no project items — adding to project %s first",
                sub_issue_node_id,
                project_id,
            )
            try:
                new_item_id = await self.add_issue_to_project(
                    access_token=access_token,
                    project_id=project_id,
                    issue_node_id=sub_issue_node_id,
                )
                if new_item_id:
                    item_id = new_item_id
                    logger.info(
                        "Added sub-issue %s to project, item_id: %s",
                        sub_issue_node_id,
                        item_id,
                    )
            except Exception as add_err:
                logger.warning(
                    "Failed to add sub-issue %s to project %s: %s",
                    sub_issue_node_id,
                    project_id,
                    add_err,
                )

        if not item_id:
            logger.warning(
                "Sub-issue %s could not be added to project — cannot set status to '%s'",
                sub_issue_node_id,
                status_name,
            )
            return False

        logger.info(
            "Updating sub-issue project board status to '%s' (item %s)",
            status_name,
            item_id,
        )
        return await self.update_item_status_by_name(
            access_token=access_token,
            project_id=project_id,
            item_id=item_id,
            status_name=status_name,
        )

    # ──────────────────────────────────────────────────────────────────
    # Project Field Management (Priority, Size, Estimate, Dates)
    # ──────────────────────────────────────────────────────────────────

    async def get_project_fields(
        self,
        access_token: str,
        project_id: str,
    ) -> dict[str, dict]:
        """
        Get all fields from a project.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID

        Returns:
            Dict mapping field names to field info (id, dataType, options if applicable)
        """
        try:
            data = await self._graphql(
                access_token,
                GET_PROJECT_FIELDS_QUERY,
                {"projectId": project_id},
            )

            fields = {}
            field_nodes = data.get("node", {}).get("fields", {}).get("nodes", [])

            for field in field_nodes:
                if not field:
                    continue
                name = field.get("name")
                if name:
                    fields[name] = {
                        "id": field.get("id"),
                        "dataType": field.get("dataType"),
                        "options": field.get("options", []),
                    }

            logger.debug("Found %d project fields: %s", len(fields), list(fields.keys()))
            return fields

        except Exception as e:
            logger.error("Failed to get project fields: %s", e)
            return {}

    async def update_project_item_field(
        self,
        access_token: str,
        project_id: str,
        item_id: str,
        field_name: str,
        value: str | float,
        field_type: str = "auto",
    ) -> bool:
        """
        Update a project item's field value.

        Args:
            access_token: GitHub OAuth access token
            project_id: GitHub Project V2 node ID
            item_id: Project item node ID
            field_name: Name of the field to update
            value: Value to set (string for select/text, float for number, date string for date)
            field_type: Type hint: "select", "number", "date", "text", or "auto" to detect

        Returns:
            True if update succeeded
        """
        try:
            # Get project fields
            fields = await self.get_project_fields(access_token, project_id)
            field_info = fields.get(field_name)

            if not field_info:
                logger.warning("Field '%s' not found in project %s", field_name, project_id)
                return False

            field_id = field_info["id"]
            data_type = field_info.get("dataType", "")

            # Determine mutation based on data type
            if data_type == "SINGLE_SELECT" or field_type == "select":
                # Find option ID for the value
                options = field_info.get("options", [])
                option_id = None
                for opt in options:
                    if opt.get("name", "").upper() == str(value).upper():
                        option_id = opt.get("id")
                        break

                if not option_id:
                    logger.warning("Option '%s' not found for field '%s'", value, field_name)
                    return False

                await self._graphql(
                    access_token,
                    UPDATE_SINGLE_SELECT_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "optionId": option_id,
                    },
                )

            elif data_type == "NUMBER" or field_type == "number":
                await self._graphql(
                    access_token,
                    UPDATE_NUMBER_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "number": float(value),
                    },
                )

            elif data_type == "DATE" or field_type == "date":
                await self._graphql(
                    access_token,
                    UPDATE_DATE_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "date": str(value),
                    },
                )

            elif data_type == "TEXT" or field_type == "text":
                await self._graphql(
                    access_token,
                    UPDATE_TEXT_FIELD_MUTATION,
                    {
                        "projectId": project_id,
                        "itemId": item_id,
                        "fieldId": field_id,
                        "text": str(value),
                    },
                )

            else:
                logger.warning("Unsupported field type '%s' for field '%s'", data_type, field_name)
                return False

            logger.info("Updated field '%s' to '%s' for item %s", field_name, value, item_id)
            return True

        except Exception as e:
            logger.error("Failed to update field '%s': %s", field_name, e)
            return False

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

    # ──────────────────────────────────────────────────────────────────
    # Polling and Change Detection (T041, T046)
    # ──────────────────────────────────────────────────────────────────

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
        workflow_triggers.extend(
            {
                "trigger": "in_progress_check",
                "task_id": task.github_item_id,
                "title": task.title,
                "issue_id": task.github_issue_id,
            }
            for task in current_tasks
            if task.status and task.status.lower() == in_progress_status.lower()
        )

        return {
            "changes": changes,
            "current_tasks": current_tasks,
            "workflow_triggers": workflow_triggers,
        }

    def _detect_changes(self, old_tasks: list[Task], new_tasks: list[Task]) -> list[dict]:
        """
        Compare two task lists and detect changes.

        Args:
            old_tasks: Previous task list
            new_tasks: Current task list

        Returns:
            List of change records
        """
        changes = []

        # Create lookup maps
        old_map = {t.github_item_id: t for t in old_tasks}
        new_map = {t.github_item_id: t for t in new_tasks}

        # Detect new tasks
        for item_id, task in new_map.items():
            if item_id not in old_map:
                changes.append(
                    {
                        "type": "task_created",
                        "task_id": item_id,
                        "title": task.title,
                        "status": task.status,
                    }
                )

        # Detect deleted tasks
        for item_id, task in old_map.items():
            if item_id not in new_map:
                changes.append(
                    {
                        "type": "task_deleted",
                        "task_id": item_id,
                        "title": task.title,
                    }
                )

        # Detect status changes
        for item_id in old_map.keys() & new_map.keys():
            old_task = old_map[item_id]
            new_task = new_map[item_id]

            if old_task.status != new_task.status:
                changes.append(
                    {
                        "type": "status_changed",
                        "task_id": item_id,
                        "title": new_task.title,
                        "old_status": old_task.status,
                        "new_status": new_task.status,
                    }
                )

            if old_task.title != new_task.title:
                changes.append(
                    {
                        "type": "title_changed",
                        "task_id": item_id,
                        "old_title": old_task.title,
                        "new_title": new_task.title,
                    }
                )

        return changes
