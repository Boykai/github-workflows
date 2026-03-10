"""Board API endpoints for the Project Board feature."""

import asyncio
import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from githubkit.exception import PrimaryRateLimitExceeded, RequestFailed

from src.api.auth import get_session_dep
from src.dependencies import verify_project_access
from src.exceptions import AuthenticationError, GitHubAPIError, NotFoundError, RateLimitError
from src.models.board import (
    BoardDataResponse,
    BoardProject,
    BoardProjectListResponse,
    RateLimitInfo,
    StatusColor,
    StatusField,
    StatusOption,
)
from src.models.project import GitHubProject
from src.models.user import UserSession
from src.services.cache import (
    cache,
    get_cache_key,
    get_sub_issues_cache_key,
    get_user_projects_cache_key,
)
from src.services.github_projects import github_projects_service


def _is_github_auth_error(exc: Exception) -> bool:
    """Return True if *exc* indicates the GitHub token is invalid/expired.

    Covers httpx status errors (401/403) and GraphQL "FORBIDDEN" / "UNAUTHORIZED"
    errors that GitHub returns inside a 200 response.

    A 403 with ``X-RateLimit-Remaining: 0`` is a primary rate-limit response,
    NOT an auth error — those are handled separately by the retry logic.
    """
    if isinstance(exc, RequestFailed):
        response = exc.response
        code = response.status_code
        if code == 401:
            return True
        if code == 403:
            # GitHub uses 403 for both auth/permission errors AND primary rate
            # limiting.  When rate-limited, X-RateLimit-Remaining is "0".
            remaining = response.headers.get("X-RateLimit-Remaining")
            if remaining is not None and remaining.strip() == "0":
                return False
            return True
        return False
    # GraphQL wraps auth problems in ValueError("GraphQL error: ...")
    msg = str(exc).lower()
    if any(
        keyword in msg
        for keyword in (
            "bad credentials",
            "unauthorized",
            "forbidden",
            "insufficient scopes",
            "401",
            "403",
        )
    ):
        return True
    return False


def _classify_github_error(exc: Exception) -> str:
    """Return a safe, user-facing error classification for *exc*.

    Never exposes raw internal strings (URLs, hostnames, stack traces).
    """
    msg = str(exc).lower()
    if isinstance(exc, RequestFailed):
        code = exc.response.status_code
        if code == 429:
            return "GitHub API rate limit exceeded"
        if code >= 500:
            return "GitHub API is temporarily unavailable"
        return f"GitHub API returned status {code}"
    if "graphql error" in msg:
        return "GitHub GraphQL query failed"
    if "timeout" in msg or "timed out" in msg:
        return "Request to GitHub API timed out"
    if "connect" in msg:
        return "Could not connect to GitHub API"
    return "Unexpected error communicating with GitHub"


def _is_github_rate_limit_error(exc: Exception) -> bool:
    """Return True if *exc* represents a GitHub rate-limit response."""
    if isinstance(exc, PrimaryRateLimitExceeded):
        return True
    if isinstance(exc, RequestFailed):
        response = exc.response
        if response.status_code == 429:
            return True
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining")
            return remaining is not None and remaining.strip() == "0"
    rate_limit = _get_rate_limit_info()
    return rate_limit is not None and rate_limit.remaining == 0


def _rate_limit_details() -> dict[str, object]:
    """Return serialized rate-limit details when available."""
    rate_limit = _get_rate_limit_info()
    return {"rate_limit": rate_limit.model_dump()} if rate_limit is not None else {}


def _retry_after_seconds(exc: Exception) -> int:
    """Best-effort extraction of retry-after seconds from GitHub exceptions."""
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


logger = logging.getLogger(__name__)
router = APIRouter()

CACHE_PREFIX_BOARD_PROJECTS = "board_projects"
CACHE_PREFIX_BOARD_DATA = "board_data"


def _normalize_status_color(color: str | None) -> StatusColor:
    if not color:
        return StatusColor.GRAY
    normalized = color.upper()
    try:
        return StatusColor(normalized)
    except ValueError:
        return StatusColor.GRAY


def _to_board_projects(projects: list[GitHubProject]) -> list[BoardProject]:
    board_projects: list[BoardProject] = []
    for project in projects:
        valid_columns = [c for c in project.status_columns if c.field_id and c.option_id]
        if not valid_columns:
            continue

        field_id = valid_columns[0].field_id
        options = [
            StatusOption(
                option_id=column.option_id,
                name=column.name,
                color=_normalize_status_color(column.color),
                description=None,
            )
            for column in valid_columns
            if column.field_id == field_id
        ]
        if not options:
            continue

        board_projects.append(
            BoardProject(
                project_id=project.project_id,
                name=project.name,
                description=project.description,
                url=project.url,
                owner_login=project.owner_login,
                status_field=StatusField(field_id=field_id, options=options),
            )
        )

    return board_projects


def _get_rate_limit_info() -> RateLimitInfo | None:
    """Build RateLimitInfo from the last GitHub API response headers."""
    rl = github_projects_service.get_last_rate_limit()
    if not isinstance(rl, dict):
        return None
    try:
        return RateLimitInfo(
            limit=rl["limit"],
            remaining=rl["remaining"],
            reset_at=rl["reset_at"],
            used=rl["used"],
        )
    except (KeyError, TypeError):
        return None


@router.get("/projects", response_model=BoardProjectListResponse)
async def list_board_projects(
    session: Annotated[UserSession, Depends(get_session_dep)],
    refresh: Annotated[bool, Query(description="Force refresh from GitHub API")] = False,
) -> BoardProjectListResponse:
    """List available GitHub Projects with status field configuration for board display."""
    cache_key = get_cache_key(CACHE_PREFIX_BOARD_PROJECTS, session.github_user_id)
    user_projects_cache_key = get_user_projects_cache_key(session.github_user_id)

    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached board projects for user %s", session.github_username)
            return BoardProjectListResponse(projects=cached, rate_limit=_get_rate_limit_info())

        cached_user_projects = cache.get(user_projects_cache_key)
        if cached_user_projects:
            board_projects = _to_board_projects(cached_user_projects)
            if board_projects:
                logger.info(
                    "Reusing cached generic projects for board projects (user %s)",
                    session.github_username,
                )
                cache.set(cache_key, board_projects)
                return BoardProjectListResponse(
                    projects=board_projects,
                    rate_limit=_get_rate_limit_info(),
                )

    logger.info("Fetching board projects for user %s", session.github_username)

    try:
        projects = await github_projects_service.list_board_projects(
            session.access_token, session.github_username
        )
    except Exception as e:
        if _is_github_rate_limit_error(e):
            logger.warning(
                "Rate limit exceeded while fetching board projects for user %s",
                session.github_username,
            )
            raise RateLimitError(
                message="GitHub API rate limit exceeded",
                retry_after=_retry_after_seconds(e),
                details=_rate_limit_details(),
            ) from e
        if _is_github_auth_error(e):
            logger.warning(
                "GitHub token invalid/expired for user %s — returning 401",
                session.github_username,
            )
            raise AuthenticationError(
                "Your GitHub session has expired. Please log in again."
            ) from e

        if not refresh:
            stale_cached = cache.get_stale(cache_key)
            if stale_cached:
                logger.warning(
                    "Serving stale cached board projects for user %s due to GitHub error: %s",
                    session.github_username,
                    e,
                )
                return BoardProjectListResponse(
                    projects=stale_cached,
                    rate_limit=_get_rate_limit_info(),
                )

            stale_user_projects = cache.get_stale(user_projects_cache_key)
            if stale_user_projects:
                stale_board_projects = _to_board_projects(stale_user_projects)
                if stale_board_projects:
                    logger.warning(
                        "Serving stale transformed projects for user %s due to GitHub error: %s",
                        session.github_username,
                        e,
                    )
                    return BoardProjectListResponse(
                        projects=stale_board_projects,
                        rate_limit=_get_rate_limit_info(),
                    )

        logger.error("Failed to fetch board projects: %s", e, exc_info=True)
        raise GitHubAPIError(
            message="Failed to fetch board projects from GitHub.",
            details={"reason": _classify_github_error(e)},
        ) from e

    cache.set(cache_key, projects)
    return BoardProjectListResponse(projects=projects, rate_limit=_get_rate_limit_info())


@router.get("/projects/{project_id}", response_model=BoardDataResponse)
async def get_board_data(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    refresh: Annotated[bool, Query(description="Force refresh from GitHub API")] = False,
) -> BoardDataResponse:
    """Get board data for a specific project with columns and items."""
    cache_key = get_cache_key(CACHE_PREFIX_BOARD_DATA, project_id)

    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached board data for project %s", project_id)
            if isinstance(cached, BoardDataResponse):
                # Return a shallow copy to avoid mutating the shared cache entry,
                # which could leak stale rate_limit values across requests.
                return cached.model_copy(update={"rate_limit": _get_rate_limit_info()})
            return cached

    # On manual refresh, clear sub-issue caches BEFORE fetching board data so
    # that get_board_data() → get_sub_issues() doesn't serve stale cached entries.
    if refresh:
        old_cached = cache.get(cache_key)
        if isinstance(old_cached, BoardDataResponse) and hasattr(old_cached, "columns"):
            for col in old_cached.columns:
                for item in col.items:
                    if item.number is not None and item.repository:
                        si_key = get_sub_issues_cache_key(
                            item.repository.owner, item.repository.name, item.number
                        )
                        cache.delete(si_key)

    logger.info("Fetching board data for project %s", project_id)

    try:
        board_data = await github_projects_service.get_board_data(session.access_token, project_id)
    except ValueError as e:
        logger.warning("Project not found: %s - %s", project_id, e)
        raise NotFoundError("Project not found") from e
    except Exception as e:
        if _is_github_rate_limit_error(e):
            logger.warning(
                "Rate limit exceeded while fetching board data for project %s", project_id
            )
            raise RateLimitError(
                message="GitHub API rate limit exceeded",
                retry_after=_retry_after_seconds(e),
                details=_rate_limit_details(),
            ) from e
        if _is_github_auth_error(e):
            logger.warning(
                "GitHub token invalid/expired for user %s — returning 401",
                session.github_username,
            )
            raise AuthenticationError(
                "Your GitHub session has expired. Please log in again."
            ) from e
        logger.error("Failed to fetch board data: %s", e, exc_info=True)
        raise GitHubAPIError(
            message="Failed to fetch board data from GitHub",
            details={"reason": _classify_github_error(e)},
        ) from e

    board_data.rate_limit = _get_rate_limit_info()

    # Cache board data — 300 seconds aligns with frontend's 5-minute auto-refresh.
    # Manual refresh (refresh=true) bypasses this cache entirely.
    cache.set(cache_key, board_data, ttl_seconds=300)
    return board_data


@router.get("/projects/{project_id}/blocking-queue", dependencies=[Depends(verify_project_access)])
async def get_blocking_queue(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[dict]:
    """Get active blocking queue entries for a project.

    Returns non-completed entries ordered by created_at ASC, providing
    data for the blocking chain tooltip/sidebar on the board.

    Runs a stale-entry sweep before returning so that issues closed
    directly on GitHub (not via the Delete action) are automatically
    cleared from the queue instead of remaining visible as Blocking.
    """
    try:
        from src.services import blocking_queue as bq_service
        from src.services import blocking_queue_store as bq_store

        # Sweep stale entries: detect issues that were closed on GitHub
        # outside the app and mark them completed so the queue advances.
        initial_entries = await bq_store.get_by_project(project_id)
        active_repo_keys = {
            e.repo_key for e in initial_entries if e.queue_status in ("active", "in_review")
        }
        for repo_key in active_repo_keys:
            owner, repo = repo_key.split("/", 1)
            try:
                await bq_service.sweep_stale_entries(session.access_token, owner, repo)
            except Exception as e:
                logger.debug("Blocking queue sweep skipped for %s: %s", repo_key, e)

        entries = await bq_store.get_by_project(project_id)
        return [entry.model_dump() for entry in entries]
    except Exception as exc:
        logger.warning("Failed to load blocking queue for project %s", project_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load blocking queue",
        ) from exc


@router.post(
    "/projects/{project_id}/blocking-queue/{issue_number}/skip",
    dependencies=[Depends(verify_project_access)],
)
async def skip_blocking_issue(
    project_id: str,
    issue_number: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[dict]:
    """Skip a blocking queue entry — marks it completed and advances the queue.

    Activates the next pending issue(s) in the blocking queue and dispatches
    agent assignment in the background so work starts immediately.

    Returns the updated (non-completed) queue entries for the project.
    """
    from src.services import blocking_queue as bq_service
    from src.services import blocking_queue_store as bq_store

    entry = await _resolve_queue_entry(project_id, issue_number)
    activated = await bq_service.mark_completed(entry.repo_key, issue_number)

    if activated:
        asyncio.create_task(
            _dispatch_agents_for_activated(
                access_token=session.access_token,
                project_id=project_id,
                activated=activated,
            )
        )

    updated = await bq_store.get_by_project(project_id)
    return [e.model_dump() for e in updated]


@router.delete(
    "/projects/{project_id}/blocking-queue/{issue_number}",
    dependencies=[Depends(verify_project_access)],
)
async def delete_blocking_issue(
    project_id: str,
    issue_number: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[dict]:
    """Close the GitHub issue and skip it in the blocking queue.

    1. Closes the issue on GitHub (state → closed, reason → not_planned).
    2. Marks the queue entry as completed and advances to the next entry.

    Returns the updated (non-completed) queue entries for the project.
    """
    from src.services import blocking_queue as bq_service
    from src.services import blocking_queue_store as bq_store

    entry = await _resolve_queue_entry(project_id, issue_number)
    owner, repo = entry.repo_key.split("/", 1)

    # update_issue_state catches all exceptions internally and returns False on
    # failure instead of raising — so we must check the return value, not rely
    # on a try/except to detect the error.
    closed = await github_projects_service.update_issue_state(
        session.access_token,
        owner,
        repo,
        issue_number,
        state="closed",
        state_reason="not_planned",
    )
    if not closed:
        logger.warning(
            "Failed to close issue #%d on GitHub (%s)",
            issue_number,
            entry.repo_key,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to close issue on GitHub",
        )

    activated = await bq_service.mark_completed(entry.repo_key, issue_number)

    if activated:
        asyncio.create_task(
            _dispatch_agents_for_activated(
                access_token=session.access_token,
                project_id=project_id,
                activated=activated,
            )
        )

    updated = await bq_store.get_by_project(project_id)
    return [e.model_dump() for e in updated]


async def _dispatch_agents_for_activated(
    access_token: str,
    project_id: str,
    activated: list,
) -> None:
    """Background task: assign first agent for each newly activated issue.

    After a blocking issue is skipped or deleted, the blocking queue activates
    the next pending issue(s) but does not start agent work.  This function
    bridges that gap by looking up each activated issue on the project board
    and calling ``assign_agent_for_status`` so the pipeline starts immediately
    instead of waiting for the next recovery cycle.
    """
    from src.services.copilot_polling import ensure_polling_started, get_workflow_config
    from src.services.workflow_orchestrator import get_workflow_orchestrator
    from src.services.workflow_orchestrator.models import WorkflowContext, WorkflowState

    if not activated:
        return

    # Fetch board items once for all activated entries
    try:
        tasks = await github_projects_service.get_project_items(access_token, project_id)
    except Exception:
        logger.exception("Skip dispatch: failed to fetch project items")
        return

    task_by_issue = {t.issue_number: t for t in tasks if t.issue_number}

    config = await get_workflow_config(project_id)
    orchestrator = get_workflow_orchestrator()

    for entry in activated:
        issue_number = entry.issue_number
        owner, repo = entry.repo_key.split("/", 1)

        task = task_by_issue.get(issue_number)
        if not task:
            logger.warning(
                "Skip dispatch: issue #%d not found on project board — recovery will handle it",
                issue_number,
            )
            continue

        if not config:
            # Bootstrap a default config so assignment can proceed
            from src.services.copilot_polling import WorkflowConfiguration

            config = WorkflowConfiguration(
                project_id=project_id,
                repository_owner=owner,
                repository_name=repo,
            )

        status_name = task.status or "Backlog"

        ctx = WorkflowContext(
            session_id="blocking-queue-dispatch",
            project_id=project_id,
            access_token=access_token,
            repository_owner=owner,
            repository_name=repo,
            issue_id=task.github_content_id,
            issue_number=issue_number,
            project_item_id=task.github_item_id,
            current_state=WorkflowState.READY,
        )
        ctx.config = config

        try:
            assigned = await orchestrator.assign_agent_for_status(ctx, status_name, agent_index=0)
            if assigned:
                logger.info(
                    "Skip dispatch: assigned first agent for issue #%d (status=%s)",
                    issue_number,
                    status_name,
                )
            else:
                logger.warning(
                    "Skip dispatch: assign_agent_for_status returned False for issue #%d",
                    issue_number,
                )
        except Exception:
            logger.exception(
                "Skip dispatch: failed to assign agent for issue #%d",
                issue_number,
            )

    # Ensure polling is running so the pipeline advances after assignment
    try:
        first = activated[0]
        first_owner, first_repo = first.repo_key.split("/", 1)
        await ensure_polling_started(
            access_token=access_token,
            project_id=project_id,
            owner=first_owner,
            repo=first_repo,
            caller="blocking_queue_skip_dispatch",
        )
    except Exception:
        logger.debug("Skip dispatch: ensure_polling_started failed", exc_info=True)


async def _resolve_queue_entry(project_id: str, issue_number: int):
    """Look up a blocking queue entry by project + issue number, or raise 404."""
    from src.services import blocking_queue_store as bq_store

    entries = await bq_store.get_by_project(project_id)
    for entry in entries:
        if entry.issue_number == issue_number:
            return entry
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Issue #{issue_number} not found in blocking queue for this project",
    )
