"""Tasks API endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.auth import get_session_dep
from src.exceptions import NotFoundError, ValidationError
from src.models.task import Task, TaskCreateRequest
from src.models.user import UserSession
from src.services.cache import cache, get_project_items_cache_key
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.utils import resolve_repository

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=Task)
async def create_task(
    request: TaskCreateRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> Task:
    """Create a new task in a GitHub Project."""
    # Validate project is selected or provided
    project_id = request.project_id
    if not project_id:
        if not session.selected_project_id:
            raise ValidationError("No project selected. Please select a project first.")
        project_id = session.selected_project_id

    logger.info("Creating issue in project %s: %s", project_id, request.title)

    # Resolve repository info for issue creation
    owner, repo = await resolve_repository(session.access_token, project_id)

    # Step 1: Create a real GitHub Issue via REST API
    issue = await github_projects_service.create_issue(
        access_token=session.access_token,
        owner=owner,
        repo=repo,
        title=request.title,
        body=request.description or "",
    )

    issue_number = issue["number"]
    issue_node_id = issue["node_id"]
    issue_url = issue["html_url"]

    # Step 2: Add the issue to the project
    item_id = await github_projects_service.add_issue_to_project(
        access_token=session.access_token,
        project_id=project_id,
        issue_node_id=issue_node_id,
    )

    if not item_id:
        raise ValidationError("Failed to add issue to GitHub Project")

    # Create task response
    task = Task(
        project_id=project_id,
        github_item_id=item_id,
        title=request.title,
        description=request.description,
        status="Todo",  # Default status for new items
        status_option_id="",  # Will be set by GitHub
        issue_number=issue_number,
    )

    # Invalidate cache
    cache.delete(get_project_items_cache_key(project_id))

    # Broadcast WebSocket message to connected clients
    await connection_manager.broadcast_to_project(
        project_id,
        {
            "type": "task_created",
            "task_id": item_id,
            "title": request.title,
            "issue_number": issue_number,
            "issue_url": issue_url,
        },
    )

    logger.info("Created issue #%d in project %s", issue_number, project_id)
    return task


@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: str,
    status: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> Task:
    """Update a task's status."""
    # This endpoint requires task lookup and status field info
    # For MVP, we'll implement basic functionality

    if not session.selected_project_id:
        raise ValidationError("No project selected")

    # Get project items to find the task
    cache_key = get_project_items_cache_key(session.selected_project_id)
    tasks = cache.get(cache_key)

    if not tasks:
        tasks = await github_projects_service.get_project_items(
            session.access_token, session.selected_project_id
        )
        cache.set(cache_key, tasks)

    # Find the task
    target_task = None
    for t in tasks:
        if str(t.task_id) == task_id or t.github_item_id == task_id:
            target_task = t
            break

    if not target_task:
        raise NotFoundError(f"Task not found: {task_id}")

    # For full implementation, we'd need to:
    # 1. Get the status field ID and option ID for the target status
    # 2. Call update_item_status with those IDs
    # This is simplified for MVP

    logger.info("Status update requested for task %s to %s", task_id, status)

    # Update task object (in real implementation, would update GitHub)
    target_task.status = status

    # Invalidate cache
    cache.delete(cache_key)

    # Broadcast WebSocket message to connected clients
    await connection_manager.broadcast_to_project(
        session.selected_project_id,
        {
            "type": "task_update",
            "task_id": task_id,
            "status": status,
        },
    )

    return target_task
