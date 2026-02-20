"""Project fields and status management operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from src.models.task import Task

from .graphql_queries import (
    GET_PROJECT_FIELD_QUERY,
    GET_PROJECT_FIELDS_QUERY,
    GET_PROJECT_REPOSITORY_QUERY,
    UPDATE_DATE_FIELD_MUTATION,
    UPDATE_NUMBER_FIELD_MUTATION,
    UPDATE_SINGLE_SELECT_FIELD_MUTATION,
    UPDATE_TEXT_FIELD_MUTATION,
)

if TYPE_CHECKING:
    import httpx

logger = logging.getLogger(__name__)


class FieldsMixin:
    """Project field management and change detection."""

    _client: httpx.AsyncClient

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
