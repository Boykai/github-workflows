"""Tasks API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from src.api.auth import get_session_dep
from src.config import get_settings
from src.constants import DEFAULT_STATUS_BACKLOG
from src.dependencies import require_selected_project, verify_project_access
from src.exceptions import ValidationError
from src.logging_utils import get_logger
from src.models.task import Task, TaskCreateRequest
from src.models.user import UserSession
from src.models.workflow import WorkflowConfiguration
from src.services.cache import cache, get_project_items_cache_key
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.services.workflow_orchestrator import (
    WorkflowContext,
    get_workflow_config,
    get_workflow_orchestrator,
    set_workflow_config,
)
from src.utils import resolve_repository

logger = get_logger(__name__)
router = APIRouter()


async def _create_parent_issue_sub_issues(
    *,
    session: UserSession,
    project_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    issue_node_id: str,
    item_id: str,
) -> None:
    """Pre-create pipeline sub-issues for a newly created parent issue."""
    settings = get_settings()

    config = await get_workflow_config(project_id)
    if not config:
        config = WorkflowConfiguration(
            project_id=project_id,
            repository_owner=owner,
            repository_name=repo,
            copilot_assignee=settings.default_assignee,
        )
        await set_workflow_config(project_id, config)
    else:
        config.repository_owner = owner
        config.repository_name = repo
        if not config.copilot_assignee:
            config.copilot_assignee = settings.default_assignee

    ctx = WorkflowContext(
        session_id=str(session.session_id),
        project_id=project_id,
        access_token=session.access_token,
        repository_owner=owner,
        repository_name=repo,
        config=config,
    )
    ctx.issue_id = issue_node_id
    ctx.issue_number = issue_number
    ctx.project_item_id = item_id

    agent_sub_issues = await get_workflow_orchestrator().create_all_sub_issues(ctx)
    if agent_sub_issues:
        logger.info(
            "Pre-created %d sub-issues for task issue #%d",
            len(agent_sub_issues),
            issue_number,
        )


@router.post("", response_model=Task)
async def create_task(
    http_request: Request,
    request: TaskCreateRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> Task:
    """Create a new task in a GitHub Project."""
    # Validate project is selected or provided
    project_id = request.project_id
    if not project_id:
        project_id = require_selected_project(session)

    # Verify ownership — project_id comes from the request body, not URL path,
    # so we call verify_project_access directly instead of using a dependency.
    await verify_project_access(http_request, project_id, session)

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
    issue_database_id = issue["id"]

    # Step 2: Add the issue to the project
    item_id = await github_projects_service.add_issue_to_project(
        access_token=session.access_token,
        project_id=project_id,
        issue_node_id=issue_node_id,
        issue_database_id=issue_database_id,
    )

    if not item_id:
        raise ValidationError("Failed to add issue to GitHub Project")

    try:
        await _create_parent_issue_sub_issues(
            session=session,
            project_id=project_id,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            issue_node_id=issue_node_id,
            item_id=item_id,
        )
    except Exception:
        logger.exception(
            "Failed to pre-create sub-issues for task issue #%d in project %s",
            issue_number,
            project_id,
        )

    # Create task response
    task = Task(
        project_id=project_id,
        github_item_id=item_id,
        title=request.title,
        description=request.description,
        status=DEFAULT_STATUS_BACKLOG,  # Default status for new items
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


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    status: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> JSONResponse:
    """Update a task's status.

    Not yet implemented — returns 501 until the full GitHub Projects V2
    field-mutation flow is built.
    """
    return JSONResponse(
        status_code=501,
        content={
            "error": "Not implemented",
            "details": {
                "message": "Task status update via GitHub Projects API is not yet implemented"
            },
        },
    )
