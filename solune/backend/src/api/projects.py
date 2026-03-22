"""Projects API endpoints."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from githubkit.exception import PrimaryRateLimitExceeded, RequestFailed

from src.api.auth import get_current_session, get_session_dep
from src.constants import SESSION_COOKIE_NAME
from src.dependencies import verify_project_access
from src.exceptions import GitHubAPIError, NotFoundError, RateLimitError
from src.logging_utils import get_logger
from src.models.project import GitHubProject, ProjectListResponse
from src.models.task import TaskListResponse
from src.models.user import UserResponse, UserSession
from src.services.app_service import create_standalone_project
from src.services.cache import (
    cache,
    cached_fetch,
    compute_data_hash,
    get_project_items_cache_key,
    get_user_projects_cache_key,
)
from src.services.done_items_store import get_done_items
from src.services.github_auth import github_auth_service
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.utils import resolve_repository

logger = get_logger(__name__)
router = APIRouter()


def _is_github_rate_limit_error(exc: Exception) -> bool:
    """Return True when GitHub rejected the request due to rate limits."""
    if isinstance(exc, PrimaryRateLimitExceeded):
        return True
    if isinstance(exc, RequestFailed):
        if exc.response.status_code == 429:
            return True
        if exc.response.status_code == 403:
            remaining = exc.response.headers.get("X-RateLimit-Remaining")
            return remaining is not None and remaining.strip() == "0"
    rl = github_projects_service.get_last_rate_limit()
    return isinstance(rl, dict) and rl.get("remaining") == 0


def _retry_after_seconds(exc: Exception) -> int:
    """Extract retry-after seconds from a GitHub exception when available."""
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is None:
        args = getattr(exc, "args", ())
        if len(args) > 1:
            retry_after = args[1]

    if isinstance(retry_after, timedelta):
        return max(1, int(retry_after.total_seconds()))

    if isinstance(retry_after, int):
        return max(1, retry_after)

    return 60


def _rate_limit_details() -> dict[str, object]:
    """Return serialized rate-limit details from the shared GitHub client state."""
    rl = github_projects_service.get_last_rate_limit()
    if not isinstance(rl, dict):
        return {}
    expected_keys = {"limit", "remaining", "reset_at", "used"}
    if not expected_keys.issubset(rl):
        return {}
    return {
        "rate_limit": {
            "limit": rl["limit"],
            "remaining": rl["remaining"],
            "reset_at": rl["reset_at"],
            "used": rl["used"],
        }
    }


@router.post("/create", status_code=201)
async def create_project_endpoint(
    request: Request,
    body: dict,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Create a standalone GitHub Project V2.

    Request body: ``{title, owner, repo_owner?, repo_name?}``
    Response: ``{project_id, project_number, project_url}``
    """
    from src.dependencies import get_github_service as _get_gh
    from src.exceptions import ValidationError

    title = body.get("title")
    owner = body.get("owner")
    if not title or not owner:
        raise ValidationError("Both 'title' and 'owner' are required.")

    github_service = _get_gh(request)
    result = await create_standalone_project(
        access_token=session.access_token,
        owner=owner,
        title=title,
        github_service=github_service,
        repo_owner=body.get("repo_owner"),
        repo_name=body.get("repo_name"),
    )
    return result


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

    try:
        all_projects = await github_projects_service.list_user_projects(
            session.access_token, session.github_username
        )

        # Cache results
        cache.set(cache_key, all_projects)

        return ProjectListResponse(projects=all_projects)
    except Exception as e:
        if _is_github_rate_limit_error(e):
            if not refresh:
                stale = cache.get_stale(cache_key)
                if stale:
                    logger.warning(
                        "Serving stale cached projects for user %s due to rate limit",
                        session.github_username,
                    )
                    return ProjectListResponse(projects=stale)

            raise RateLimitError(
                message="GitHub API rate limit exceeded",
                retry_after=_retry_after_seconds(e),
                details=_rate_limit_details(),
            ) from e
        if not refresh:
            stale = cache.get_stale(cache_key)
            if stale:
                logger.warning(
                    "Serving stale cached projects for user %s due to GitHub error: %s",
                    session.github_username,
                    e,
                )
                return ProjectListResponse(projects=stale)
        raise GitHubAPIError("Failed to fetch projects from GitHub") from e


@router.get(
    "/{project_id}", response_model=GitHubProject, dependencies=[Depends(verify_project_access)]
)
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


@router.get(
    "/{project_id}/tasks",
    response_model=TaskListResponse,
    dependencies=[Depends(verify_project_access)],
)
async def get_project_tasks(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    refresh: Annotated[bool, Query(description="Force refresh from GitHub API")] = False,
) -> TaskListResponse:
    """Get tasks/items for a project."""
    cache_key = get_project_items_cache_key(project_id)

    async def _fetch():
        logger.info("Fetching tasks for project %s", project_id)
        return await github_projects_service.get_project_items(session.access_token, project_id)

    try:
        tasks = await cached_fetch(cache, cache_key, _fetch, refresh=refresh)
    except Exception:
        # On API failure, try returning DB-cached Done tasks as partial result
        cached_done = await get_done_items(project_id, item_type="task")
        if cached_done:
            from src.models.task import Task

            logger.warning(
                "Returning %d DB-cached Done tasks as fallback for project %s",
                len(cached_done),
                project_id,
            )
            return TaskListResponse(tasks=[Task.model_validate(d) for d in cached_done])
        raise

    return TaskListResponse(tasks=tasks)


@router.post(
    "/{project_id}/select",
    response_model=UserResponse,
    dependencies=[Depends(verify_project_access)],
)
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
    from src.services.copilot_polling import (
        ensure_polling_started,
        get_polling_status,
        stop_polling,
    )

    # Stop any existing polling first — cancel the task so it stops immediately
    # even if it's in the middle of a long-running API call.
    status = get_polling_status()
    if status["is_running"]:
        stop_polling()
        # Give the cancelled task a chance to clean up
        await asyncio.sleep(0.1)

    # Resolve repository info for the project
    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception:
        logger.warning(
            "Could not determine repository for project %s, polling not started",
            project_id,
        )
        return

    await ensure_polling_started(
        access_token=session.access_token,
        project_id=project_id,
        owner=owner,
        repo=repo,
        caller="select_project",
    )


@router.websocket("/{project_id}/subscribe")
async def websocket_subscribe(
    websocket: WebSocket,
    project_id: str,
):
    """
    WebSocket endpoint for real-time project updates.

    On connection, sends all current tasks.
    Periodically checks for updates every 30 seconds (using cached data
    when available; actual GitHub API calls are governed by the cache TTL).
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
        session = await get_current_session(session_id)
    except Exception as e:
        logger.error("WebSocket authentication failed: %s", e)
        await websocket.close(code=1008, reason="Authentication required")
        return

    # Verify the user has access to this project before accepting.
    # Reuse the cached user-projects list when available to avoid an extra
    # upstream API call on every WebSocket connection (R2 optimisation).
    try:
        user_projects_key = get_user_projects_cache_key(session.github_user_id)
        projects = cache.get(user_projects_key)
        if projects is None:
            try:
                projects = await github_projects_service.list_user_projects(
                    session.access_token, session.github_username
                )
                cache.set(user_projects_key, projects)
            except Exception as fetch_err:
                logger.warning(
                    "WebSocket project access revalidation failed for user=%s: %s",
                    session.github_username,
                    fetch_err,
                )
                raise
        if not any(p.project_id == project_id for p in projects):
            logger.warning(
                "WebSocket project access denied: user=%s project=%s",
                session.github_username,
                project_id,
            )
            await websocket.close(code=4403, reason="Project access denied")
            return
    except Exception as e:
        logger.error("WebSocket project access check failed: %s", e)
        await websocket.close(code=4403, reason="Project access denied")
        return

    await connection_manager.connect(websocket, project_id)

    stale_revalidation_count = 0  # tracks consecutive stale returns
    STALE_REVALIDATION_LIMIT = 10  # revalidate after this many stale returns

    async def send_tasks(*, force_refresh: bool = False):
        """Fetch and send current tasks, using cache when possible.

        NOTE: Evaluated for migration to ``cached_fetch()`` (Phase 2, Task 2.2).
        **Not migrated** because the stale-revalidation counter pattern
        (``stale_revalidation_count`` / ``STALE_REVALIDATION_LIMIT``) is
        stateful across calls and controls *when* to bypass cache — a
        fetch-scheduling concern that ``cached_fetch()`` should not own.
        The ``data_hash_fn`` extension covers the hash-diffing portion,
        but the counter introduces call-frequency-dependent state that
        would require single-caller parameters, violating YAGNI.
        See research.md Task 6 for full rationale.
        """
        nonlocal stale_revalidation_count
        cache_key = get_project_items_cache_key(project_id)
        try:
            # Use cache for periodic refreshes to avoid hammering the API.
            # Only bypass cache on initial connection (force_refresh=True).
            if not force_refresh:
                cached = cache.get(cache_key)
                if cached is not None:
                    stale_revalidation_count = 0
                    return cached

                # When the cache has expired, serve stale data to avoid
                # triggering a fresh API call on every periodic check.
                # However, allow a real fetch every N stale cycles so
                # connected clients eventually pick up external changes
                # rather than staying permanently stale.
                stale = cache.get_stale(cache_key)
                if stale is not None:
                    stale_revalidation_count += 1
                    if stale_revalidation_count < STALE_REVALIDATION_LIMIT:
                        logger.debug(
                            "WebSocket periodic check using stale cache for project %s (%d/%d)",
                            project_id,
                            stale_revalidation_count,
                            STALE_REVALIDATION_LIMIT,
                        )
                        return stale
                    # Revalidation threshold reached — fall through to fetch
                    logger.debug(
                        "Stale revalidation limit reached for project %s, fetching fresh data",
                        project_id,
                    )
                    stale_revalidation_count = 0

            tasks = await github_projects_service.get_project_items(
                session.access_token, project_id
            )
            # Compare fetched data against previously cached entry using
            # data_hash (FR-004 change detection).  When the data is
            # unchanged we refresh the TTL instead of storing a new entry,
            # keeping the stale-revalidation counter at zero and avoiding
            # unnecessary downstream refresh messages.
            tasks_payload = [t.model_dump(mode="json") for t in tasks]
            new_hash = compute_data_hash(tasks_payload)
            existing_entry = cache.get_entry(cache_key)
            if existing_entry is not None and existing_entry.data_hash == new_hash:
                cache.refresh_ttl(cache_key)
                logger.debug(
                    "Refreshed cache TTL for project %s — data unchanged",
                    project_id,
                )
            else:
                cache.set(cache_key, tasks, data_hash=new_hash)
            stale_revalidation_count = 0
            return tasks
        except Exception as e:
            logger.error("Failed to fetch tasks for WebSocket: %s", e)
            # On fetch failure, fall back to stale data if available
            stale = cache.get_stale(cache_key)
            if stale is not None:
                logger.debug("Serving stale data after fetch failure for project %s", project_id)
                return stale
            return None

    try:
        # Send all current tasks immediately on connection (bypass cache)
        tasks = await send_tasks(force_refresh=True)
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

        # Keep connection alive and periodically push cached data.
        # Actual GitHub API calls are governed by the cache TTL (default
        # 300 s); this interval only controls how often we check/send.
        last_refresh = asyncio.get_running_loop().time()
        refresh_interval = 30.0  # Check for updates every 30 seconds
        last_sent_hash: str | None = None

        while True:
            try:
                # Wait for incoming messages with timeout
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)

                # Handle ping
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except TimeoutError:
                # Check if we need to refresh
                current_time = asyncio.get_running_loop().time()
                if current_time - last_refresh >= refresh_interval:
                    # Refresh and send updated tasks
                    tasks = await send_tasks()
                    if tasks is not None:
                        tasks_payload = [task.model_dump(mode="json") for task in tasks]
                        current_hash = compute_data_hash(tasks_payload)

                        if current_hash != last_sent_hash:
                            await websocket.send_json(
                                {
                                    "type": "refresh",
                                    "project_id": project_id,
                                    "tasks": tasks_payload,
                                    "count": len(tasks),
                                }
                            )
                            last_sent_hash = current_hash
                            logger.debug(
                                "Refreshed %d tasks for project %s", len(tasks), project_id
                            )
                        else:
                            logger.debug(
                                "Skipping refresh for project %s — data unchanged", project_id
                            )
                    last_refresh = current_time

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for project %s", project_id)
    except Exception as e:
        logger.error("WebSocket error for project %s: %s", project_id, e)
    finally:
        connection_manager.disconnect(websocket)


@router.get("/{project_id}/events", dependencies=[Depends(verify_project_access)])
async def sse_subscribe(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
):
    """
    Server-Sent Events endpoint for real-time updates.

    This is a fallback for clients that don't support WebSocket.
    Uses polling internally with 10-second intervals.
    """

    async def event_generator() -> AsyncGenerator[str]:
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
                    yield f'event: heartbeat\ndata: {{"timestamp": "{asyncio.get_running_loop().time()}"}}\n\n'

                except Exception as e:
                    logger.error("SSE polling error: %s", e)
                    # Serve stale cached data on fetch failure instead of
                    # cascading the error to the client (SC-005 safety).
                    stale = cache.get_stale(cache_key)
                    if stale is not None:
                        cached_tasks = stale
                    yield f'event: heartbeat\ndata: {{"timestamp": "{asyncio.get_running_loop().time()}"}}\n\n'

                # Wait before next poll (30 seconds to reduce API call volume)
                await asyncio.sleep(30)

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
