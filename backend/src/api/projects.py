"""Projects API endpoints."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from src.api.auth import get_current_session, get_session_dep
from src.constants import SESSION_COOKIE_NAME
from src.exceptions import NotFoundError
from src.models.project import GitHubProject, ProjectListResponse
from src.models.task import TaskListResponse
from src.models.user import UserResponse, UserSession
from src.services.cache import (
    cache,
    get_project_items_cache_key,
    get_user_projects_cache_key,
)
from src.services.github_auth import github_auth_service
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    session: Annotated[UserSession, Depends(get_session_dep)],
    refresh: Annotated[bool, Query(description="Force refresh from GitHub API")] = False,
) -> ProjectListResponse:
    """List user's accessible GitHub Projects."""
    cache_key = get_user_projects_cache_key(session.github_user_id)

    # Check cache unless refresh requested
    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached projects for user %s", session.github_username)
            return ProjectListResponse(projects=cached)

    # Fetch from GitHub
    logger.info("Fetching projects for user %s", session.github_username)

    # Get user's personal projects
    user_projects = await github_projects_service.list_user_projects(
        session.access_token, session.github_username
    )

    # TODO: Also fetch org projects the user has access to
    # This requires listing orgs first, then querying each

    all_projects = user_projects

    # Cache results
    cache.set(cache_key, all_projects)

    return ProjectListResponse(projects=all_projects)


@router.get("/{project_id}", response_model=GitHubProject)
async def get_project(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> GitHubProject:
    """Get project details including status columns."""
    # First check if we have the project cached in the list
    cache_key = get_user_projects_cache_key(session.github_user_id)
    cached_projects = cache.get(cache_key)

    if cached_projects:
        for project in cached_projects:
            if project.project_id == project_id:
                return project

    # If not cached, fetch projects list
    projects_response = await list_projects(session, refresh=True)

    for project in projects_response.projects:
        if project.project_id == project_id:
            return project

    raise NotFoundError(f"Project not found: {project_id}")


@router.get("/{project_id}/tasks", response_model=TaskListResponse)
async def get_project_tasks(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    refresh: Annotated[bool, Query(description="Force refresh from GitHub API")] = False,
) -> TaskListResponse:
    """Get tasks/items for a project."""
    cache_key = get_project_items_cache_key(project_id)

    # Check cache unless refresh requested
    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached tasks for project %s", project_id)
            return TaskListResponse(tasks=cached)

    # Fetch from GitHub
    logger.info("Fetching tasks for project %s", project_id)
    tasks = await github_projects_service.get_project_items(session.access_token, project_id)

    # Cache results
    cache.set(cache_key, tasks)

    return TaskListResponse(tasks=tasks)


@router.post("/{project_id}/select", response_model=UserResponse)
async def select_project(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> UserResponse:
    """Select a project as the active project and start Copilot polling."""
    # Verify project exists and user has access
    await get_project(project_id, session)

    # Update session
    session.selected_project_id = project_id
    await github_auth_service.update_session(session)

    logger.info("User %s selected project %s", session.github_username, project_id)

    # Auto-start Copilot polling for this project
    await _start_copilot_polling(session, project_id)

    return UserResponse.from_session(session)


async def _start_copilot_polling(session: UserSession, project_id: str) -> None:
    """Start Copilot PR completion polling for the selected project."""
    import src.services.copilot_polling as _cp_module
    from src.services.copilot_polling import (
        get_polling_status,
        poll_for_copilot_completion,
        stop_polling,
    )

    # Stop any existing polling first — cancel the task so it stops immediately
    # even if it's in the middle of a long-running API call.
    status = get_polling_status()
    if status["is_running"]:
        stop_polling()
        # Give the cancelled task a chance to clean up
        await asyncio.sleep(0.1)

    # Get repository info for the project
    repo_info = await github_projects_service.get_project_repository(
        session.access_token,
        project_id,
    )

    if not repo_info:
        # Try to get from workflow config or settings
        from src.api.workflow import get_workflow_config
        from src.config import get_settings

        config = get_workflow_config(project_id)
        if config and config.repository_owner and config.repository_name:
            repo_info = (config.repository_owner, config.repository_name)
        else:
            settings = get_settings()
            if settings.default_repo_owner and settings.default_repo_name:
                repo_info = (settings.default_repo_owner, settings.default_repo_name)

    if not repo_info:
        logger.warning(
            "Could not determine repository for project %s, polling not started",
            project_id,
        )
        return

    owner, repo = repo_info

    # Start polling as background task (15 second interval).
    # Store the task reference so stop_polling() can cancel it.
    task = asyncio.create_task(
        poll_for_copilot_completion(
            access_token=session.access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            interval_seconds=15,
        )
    )
    _cp_module._polling_task = task

    logger.info(
        "Auto-started Copilot PR polling for project %s (%s/%s)",
        project_id,
        owner,
        repo,
    )


@router.websocket("/{project_id}/subscribe")
async def websocket_subscribe(
    websocket: WebSocket,
    project_id: str,
):
    """
    WebSocket endpoint for real-time project updates.

    On connection, sends all current tasks.
    Periodically refreshes and sends updates every 5 seconds.
    Also sends real-time updates when tasks are created, updated, or deleted.

    Message format:
    {
        "type": "initial_data" | "refresh" | "task_created" | "task_update" | "status_changed",
        "tasks": [...] | "task_id": "...",
        "data": {...}
    }
    """
    # Get session from cookie to authenticate
    session_id = websocket.cookies.get(SESSION_COOKIE_NAME)
    try:
        session = get_current_session(session_id)
    except Exception as e:
        logger.error("WebSocket authentication failed: %s", e)
        await websocket.close(code=1008, reason="Authentication required")
        return

    await connection_manager.connect(websocket, project_id)

    async def send_tasks():
        """Fetch and send current tasks."""
        try:
            # Fetch fresh data from GitHub (bypass cache for WebSocket)
            tasks = await github_projects_service.get_project_items(
                session.access_token, project_id
            )

            # Update cache
            cache_key = get_project_items_cache_key(project_id)
            cache.set(cache_key, tasks)

            return tasks
        except Exception as e:
            logger.error("Failed to fetch tasks for WebSocket: %s", e)
            return None

    try:
        # Send all current tasks immediately on connection
        tasks = await send_tasks()
        if tasks is not None:
            await websocket.send_json(
                {
                    "type": "initial_data",
                    "project_id": project_id,
                    "tasks": [task.model_dump(mode="json") for task in tasks],
                    "count": len(tasks),
                }
            )
            logger.info(
                "Sent %d initial tasks to WebSocket for project %s",
                len(tasks),
                project_id,
            )

        # Keep connection alive and periodically refresh
        last_refresh = asyncio.get_event_loop().time()
        refresh_interval = 5.0  # Refresh every 5 seconds

        while True:
            try:
                # Wait for incoming messages with timeout
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)

                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except TimeoutError:
                # Check if we need to refresh
                current_time = asyncio.get_event_loop().time()
                if current_time - last_refresh >= refresh_interval:
                    # Refresh and send updated tasks
                    tasks = await send_tasks()
                    if tasks is not None:
                        await websocket.send_json(
                            {
                                "type": "refresh",
                                "project_id": project_id,
                                "tasks": [task.model_dump(mode="json") for task in tasks],
                                "count": len(tasks),
                            }
                        )
                        logger.debug("Refreshed %d tasks for project %s", len(tasks), project_id)
                    last_refresh = current_time

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for project %s", project_id)
    except Exception as e:
        logger.error("WebSocket error for project %s: %s", project_id, e)
    finally:
        connection_manager.disconnect(websocket)


@router.get("/{project_id}/events")
async def sse_subscribe(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
):
    """
    Server-Sent Events endpoint for real-time updates.

    This is a fallback for clients that don't support WebSocket.
    Uses polling internally with 10-second intervals.
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events by polling for changes."""
        # Get initial state
        cache_key = get_project_items_cache_key(project_id)
        cached_tasks = cache.get(cache_key) or []

        # Send initial connection event
        yield f'event: connected\ndata: {{"project_id": "{project_id}"}}\n\n'

        try:
            while True:
                # Poll for changes
                try:
                    result = await github_projects_service.poll_project_changes(
                        session.access_token,
                        project_id,
                        cached_tasks,
                    )

                    changes = result.get("changes", [])

                    if changes:
                        # Update cache
                        cached_tasks = result.get("current_tasks", [])
                        cache.set(cache_key, cached_tasks)

                        # Send change events
                        for change in changes:
                            import json

                            yield f"event: {change['type']}\ndata: {json.dumps(change)}\n\n"

                    # Send heartbeat
                    yield f'event: heartbeat\ndata: {{"timestamp": "{asyncio.get_event_loop().time()}"}}\n\n'

                except Exception as e:
                    logger.error("SSE polling error: %s", e)
                    yield 'event: error\ndata: {"message": "Polling error"}\n\n'

                # Wait before next poll
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            logger.info("SSE connection closed for project %s", project_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
