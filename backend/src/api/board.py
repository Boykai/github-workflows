"""Board API endpoints for the Project Board feature."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_session_dep
from src.exceptions import GitHubAPIError, NotFoundError
from src.models.board import BoardDataResponse, BoardProjectListResponse
from src.models.user import UserSession
from src.services.cache import cache, get_cache_key
from src.services.github_projects import github_projects_service

logger = logging.getLogger(__name__)
router = APIRouter()

CACHE_PREFIX_BOARD_PROJECTS = "board_projects"
CACHE_PREFIX_BOARD_DATA = "board_data"


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
            return BoardProjectListResponse(projects=cached)

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
    return BoardProjectListResponse(projects=projects)


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
            return cached

    logger.info("Fetching board data for project %s", project_id)

    try:
        board_data = await github_projects_service.get_board_data(session.access_token, project_id)
    except ValueError as e:
        logger.warning("Project not found: %s - %s", project_id, e)
        raise NotFoundError(f"Project not found: {project_id}") from e
    except Exception as e:
        logger.error("Failed to fetch board data: %s", e)
        raise GitHubAPIError(
            message="Failed to fetch board data from GitHub",
            details={"error": str(e)},
        ) from e

    # Cache for shorter TTL since board data changes more frequently
    cache.set(cache_key, board_data, ttl_seconds=30)
    return board_data
