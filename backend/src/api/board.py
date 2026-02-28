"""Board API endpoints for the Project Board feature."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.api.auth import get_session_dep
from src.exceptions import GitHubAPIError, NotFoundError
from src.models.board import BoardDataResponse, BoardProjectListResponse, RateLimitInfo
from src.models.user import UserSession
from src.services.cache import cache, get_cache_key
from src.services.github_projects import github_projects_service

logger = logging.getLogger(__name__)
router = APIRouter()

CACHE_PREFIX_BOARD_PROJECTS = "board_projects"
CACHE_PREFIX_BOARD_DATA = "board_data"


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

    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached board projects for user %s", session.github_username)
            return BoardProjectListResponse(projects=cached, rate_limit=_get_rate_limit_info())

    logger.info("Fetching board projects for user %s", session.github_username)

    try:
        projects = await github_projects_service.list_board_projects(
            session.access_token, session.github_username
        )
    except Exception as e:
        logger.error("Failed to fetch board projects: %s", e)
        raise GitHubAPIError(
            message="Failed to fetch projects from GitHub",
            details={"error": str(e)},
        ) from e

    cache.set(cache_key, projects)
    return BoardProjectListResponse(projects=projects, rate_limit=_get_rate_limit_info())


@router.get("/projects/{project_id}", response_model=BoardDataResponse)
async def get_board_data(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    refresh: Annotated[bool, Query(description="Force refresh from GitHub API")] = False,
) -> BoardDataResponse | JSONResponse:
    """Get board data for a specific project with columns and items."""
    cache_key = get_cache_key(CACHE_PREFIX_BOARD_DATA, project_id)

    if not refresh:
        cached = cache.get(cache_key)
        if cached:
            logger.info("Returning cached board data for project %s", project_id)
            if isinstance(cached, BoardDataResponse):
                cached.rate_limit = _get_rate_limit_info()
            return cached

    logger.info("Fetching board data for project %s", project_id)

    try:
        board_data = await github_projects_service.get_board_data(session.access_token, project_id)
    except ValueError as e:
        logger.warning("Project not found: %s - %s", project_id, e)
        raise NotFoundError(f"Project not found: {project_id}") from e
    except Exception as e:
        # Check if this is a rate limit error
        rl = github_projects_service.get_last_rate_limit()
        if isinstance(rl, dict) and rl.get("remaining") == 0:
            logger.warning("Rate limit exceeded while fetching board data for project %s", project_id)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "GitHub API rate limit exceeded",
                    "rate_limit": {
                        "limit": rl["limit"],
                        "remaining": 0,
                        "reset_at": rl["reset_at"],
                        "used": rl["used"],
                    },
                },
            )
        logger.error("Failed to fetch board data: %s", e)
        raise GitHubAPIError(
            message="Failed to fetch board data from GitHub",
            details={"error": str(e)},
        ) from e

    board_data.rate_limit = _get_rate_limit_info()
    # Cache for shorter TTL since board data changes more frequently
    cache.set(cache_key, board_data, ttl_seconds=30)
    return board_data
