"""Cleanup API endpoints for deleting stale branches and closing stale PRs."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_current_session
from src.dependencies import get_database, get_github_service
from src.exceptions import AppException, GitHubAPIError
from src.models.cleanup import (
    CleanupExecuteRequest,
    CleanupExecuteResponse,
    CleanupHistoryResponse,
    CleanupPreflightRequest,
    CleanupPreflightResponse,
)
from src.models.user import UserSession
from src.services import cleanup_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/preflight", response_model=CleanupPreflightResponse)
async def cleanup_preflight(
    request: CleanupPreflightRequest,
    session: Annotated[UserSession, Depends(get_current_session)],
    github_service=Depends(get_github_service),  # noqa: B008
) -> CleanupPreflightResponse:
    """Perform a preflight check: fetch branches, PRs, and project board issues.

    Computes deletion/preservation lists without performing any mutations.
    """
    logger.info(
        "Cleanup preflight for %s/%s by user %s",
        request.owner,
        request.repo,
        session.github_username,
    )
    try:
        return await cleanup_service.preflight(
            github_service,
            session.access_token,
            session.github_username,
            request,
        )
    except Exception as e:
        logger.error("Cleanup preflight failed: %s", e, exc_info=True)
        raise GitHubAPIError(
            message="Failed to perform cleanup preflight",
        ) from e


@router.post("/execute", response_model=CleanupExecuteResponse)
async def cleanup_execute(
    request: CleanupExecuteRequest,
    session: Annotated[UserSession, Depends(get_current_session)],
    github_service=Depends(get_github_service),  # noqa: B008
    db=Depends(get_database),  # noqa: B008
) -> CleanupExecuteResponse:
    """Execute the cleanup operation: delete branches and close PRs.

    The main branch is rejected server-side even if included in the request.
    """
    # Server-side main branch protection
    if "main" in request.branches_to_delete:
        raise AppException(
            message="Cannot delete the main branch",
            status_code=400,
            details={
                "message": (
                    "The 'main' branch was included in the deletion list "
                    "and has been rejected. The main branch is unconditionally protected."
                ),
            },
        )

    logger.info(
        "Cleanup execute for %s/%s by user %s: %d branches, %d PRs",
        request.owner,
        request.repo,
        session.github_username,
        len(request.branches_to_delete),
        len(request.prs_to_close),
    )
    try:
        return await cleanup_service.execute_cleanup(
            github_service,
            session.access_token,
            request.owner,
            request.repo,
            request,
            db,
            session.github_user_id,
        )
    except AppException:
        raise
    except Exception as e:
        logger.error("Cleanup execution failed: %s", e, exc_info=True)
        raise GitHubAPIError(
            message="Cleanup operation failed",
        ) from e


@router.get("/history", response_model=CleanupHistoryResponse)
async def cleanup_history(
    session: Annotated[UserSession, Depends(get_current_session)],
    owner: Annotated[str, Query(description="Repository owner")],
    repo: Annotated[str, Query(description="Repository name")],
    limit: Annotated[int, Query(description="Max results", ge=1, le=50)] = 10,
    db=Depends(get_database),  # noqa: B008
) -> CleanupHistoryResponse:
    """Retrieve audit trail of past cleanup operations."""
    try:
        return await cleanup_service.get_cleanup_history(
            db, session.github_user_id, owner, repo, limit
        )
    except Exception as e:
        logger.error("Failed to fetch cleanup history: %s", e, exc_info=True)
        raise GitHubAPIError(
            message="Failed to fetch cleanup history",
        ) from e
