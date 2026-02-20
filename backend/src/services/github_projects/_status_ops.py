"""Mixin for status and label management operations."""

import asyncio
import logging

from ._queries import (
    GET_PROJECT_FIELD_QUERY,
    UPDATE_ITEM_STATUS_MUTATION,
)

logger = logging.getLogger(__name__)


class _StatusOpsMixin:
    """Mixin for updating item status on project boards."""

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
        # Add 2 second delay before status update (rate limiting / UX improvement)
        await asyncio.sleep(2)

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
