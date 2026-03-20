"""Cleanup API endpoints for deleting stale branches, closing stale PRs, and deleting orphaned issues."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_session_dep
from src.dependencies import get_database, get_github_service
from src.exceptions import AppException, GitHubAPIError
from src.logging_utils import get_logger, handle_service_error
from src.models.cleanup import (
    CleanupExecuteRequest,
    CleanupExecuteResponse,
    CleanupHistoryResponse,
    CleanupPreflightRequest,
    CleanupPreflightResponse,
)
from src.models.user import UserSession
from src.services import cleanup_service
from src.services.activity_logger import log_event

logger = get_logger(__name__)
router = APIRouter()


@router.post("/preflight", response_model=CleanupPreflightResponse)
async def cleanup_preflight(
    request: CleanupPreflightRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
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
        handle_service_error(e, "perform cleanup preflight", GitHubAPIError)


@router.post("/execute", response_model=CleanupExecuteResponse)
async def cleanup_execute(
    request: CleanupExecuteRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
    github_service=Depends(get_github_service),  # noqa: B008
    db=Depends(get_database),  # noqa: B008
) -> CleanupExecuteResponse:
    """Execute the cleanup operation: delete branches, close PRs, and delete orphaned issues.

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
        "Cleanup execute for %s/%s by user %s: %d branches, %d PRs, %d issues",
        request.owner,
        request.repo,
        session.github_username,
        len(request.branches_to_delete),
        len(request.prs_to_close),
        len(request.issues_to_delete),
    )
    try:
        result = await cleanup_service.execute_cleanup(
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
        handle_service_error(e, "execute cleanup operation", GitHubAPIError)

    await log_event(
        db,
        event_type="cleanup",
        entity_type="pipeline",
        entity_id=f"{request.owner}/{request.repo}",
        project_id=request.project_id,
        actor=session.github_username,
        action="completed",
        summary=f"Cleanup completed for {request.owner}/{request.repo}",
        detail={
            "branches_deleted": len(request.branches_to_delete),
            "prs_closed": len(request.prs_to_close),
        },
    )

    return result


@router.get("/history", response_model=CleanupHistoryResponse)
async def cleanup_history(
    session: Annotated[UserSession, Depends(get_session_dep)],
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
        handle_service_error(e, "fetch cleanup history", GitHubAPIError)
