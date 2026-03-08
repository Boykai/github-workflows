"""Board API endpoints for the Project Board feature."""

import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from githubkit.exception import PrimaryRateLimitExceeded, RequestFailed

from src.api.auth import get_session_dep
from src.exceptions import AuthenticationError, GitHubAPIError, NotFoundError, RateLimitError
from src.logging_utils import handle_service_error
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

        handle_service_error(e, "fetch board projects", GitHubAPIError)

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
        handle_service_error(e, "fetch board data", GitHubAPIError)

    board_data.rate_limit = _get_rate_limit_info()

    # Cache board data — 300 seconds aligns with frontend's 5-minute auto-refresh.
    # Manual refresh (refresh=true) bypasses this cache entirely.
    cache.set(cache_key, board_data, ttl_seconds=300)
    return board_data
