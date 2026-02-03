"""Workflow API endpoints for issue creation and management."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query

from src.api.auth import SESSION_COOKIE_NAME, get_current_session
from src.api.chat import _recommendations
from src.exceptions import NotFoundError, ValidationError
from src.models.chat import (
    IssueRecommendation,
    RecommendationStatus,
    WorkflowConfiguration,
    WorkflowResult,
    WorkflowTransition,
)
from src.models.user import UserSession
from src.services.cache import cache, get_user_projects_cache_key
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.services.workflow_orchestrator import (
    WorkflowContext,
    WorkflowOrchestrator,
    get_transitions,
    get_workflow_config,
    get_workflow_orchestrator,
    set_workflow_config,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow", tags=["Workflow"])

# In-memory duplicate detection (T029)
# Maps hash of original_input to (timestamp, recommendation_id)
_recent_requests: dict[str, tuple[datetime, str]] = {}
DUPLICATE_WINDOW_MINUTES = 5


async def get_session_dep(
    session_id: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> UserSession:
    """Dependency for getting current session."""
    return get_current_session(session_id)


def _check_duplicate(original_input: str, recommendation_id: str) -> bool:
    """
    Check if this is a duplicate request within the time window (T029).

    Args:
        original_input: User's original input text
        recommendation_id: Current recommendation ID

    Returns:
        True if duplicate detected
    """
    # Clean old entries
    now = datetime.utcnow()
    cutoff = now - timedelta(minutes=DUPLICATE_WINDOW_MINUTES)
    expired = [k for k, (ts, _) in _recent_requests.items() if ts < cutoff]
    for k in expired:
        del _recent_requests[k]

    # Hash the input
    input_hash = hashlib.sha256(original_input.encode()).hexdigest()

    # Check for duplicate
    if input_hash in _recent_requests:
        existing_ts, existing_id = _recent_requests[input_hash]
        if existing_id != recommendation_id:
            logger.warning(
                "Duplicate request detected: %s (existing: %s)",
                recommendation_id,
                existing_id,
            )
            return True

    # Record this request
    _recent_requests[input_hash] = (now, recommendation_id)
    return False


def _get_repository_info(session: UserSession) -> tuple[str, str]:
    """
    Get repository owner and name from session/project context.

    Returns:
        Tuple of (owner, repo_name)
    """
    # Try to get from cached projects
    cache_key = get_user_projects_cache_key(session.github_user_id)
    cached_projects = cache.get(cache_key)

    if cached_projects and session.selected_project_id:
        for p in cached_projects:
            if p.project_id == session.selected_project_id:
                # Parse owner from project URL: https://github.com/users/{user}/projects/{num}
                # or https://github.com/orgs/{org}/projects/{num}
                url = p.url or ""
                if "/users/" in url:
                    parts = url.split("/users/")[1].split("/")
                    return parts[0], ""  # User project, no specific repo
                elif "/orgs/" in url:
                    parts = url.split("/orgs/")[1].split("/")
                    return parts[0], ""  # Org project, no specific repo

    # Fall back to username
    return session.github_username or "", ""


@router.post("/recommendations/{recommendation_id}/confirm", response_model=WorkflowResult)
async def confirm_recommendation(
    recommendation_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> WorkflowResult:
    """
    Confirm an AI-generated issue recommendation (T025).

    This triggers:
    1. GitHub Issue creation (REST API)
    2. Project attachment (GraphQL API)
    3. Initial status set to "Backlog"
    4. Auto-transition to "Ready"
    """
    # Get recommendation
    recommendation = _recommendations.get(recommendation_id)
    if not recommendation:
        raise NotFoundError(f"Recommendation not found: {recommendation_id}")

    if str(recommendation.session_id) != str(session.session_id):
        raise NotFoundError(f"Recommendation not found: {recommendation_id}")

    if recommendation.status != RecommendationStatus.PENDING:
        raise ValidationError(
            f"Recommendation already {recommendation.status.value}"
        )

    # Check for duplicates (T029)
    if _check_duplicate(recommendation.original_input, recommendation_id):
        raise ValidationError(
            "A similar request was recently processed. Please wait a few minutes."
        )

    # Require project selection
    if not session.selected_project_id:
        raise ValidationError("Please select a project first")

    # Get repository info - first try from project items
    repo_info = await github_projects_service.get_project_repository(
        session.access_token,
        session.selected_project_id,
    )

    if repo_info:
        owner, repo = repo_info
    else:
        # Fall back to workflow config if already set
        config = get_workflow_config(session.selected_project_id)
        if config and config.repository_owner and config.repository_name:
            owner, repo = config.repository_owner, config.repository_name
        else:
            # Fall back to default repository from settings
            from src.config import get_settings
            settings = get_settings()
            if settings.default_repo_owner and settings.default_repo_name:
                owner, repo = settings.default_repo_owner, settings.default_repo_name
                logger.info("Using default repository from settings: %s/%s", owner, repo)
            else:
                # Fall back to parsing from project URL or username
                owner, repo = _get_repository_info(session)
                if not owner:
                    owner = session.github_username or ""
                if not repo:
                    # If no repo found, we can't create issues
                    raise ValidationError(
                        "No repository found for this project. Configure DEFAULT_REPOSITORY in .env "
                        "or ensure the project has at least one linked issue."
                    )

    logger.info("Using repository %s/%s for issue creation", owner, repo)

    # Get settings for default assignee
    from src.config import get_settings
    settings = get_settings()

    # Get or create workflow config
    config = get_workflow_config(session.selected_project_id)
    if not config:
        config = WorkflowConfiguration(
            project_id=session.selected_project_id,
            repository_owner=owner,
            repository_name=repo,
            copilot_assignee=settings.default_assignee,
        )
        set_workflow_config(session.selected_project_id, config)
    else:
        # Update config with discovered repository
        config.repository_owner = owner
        config.repository_name = repo
        # Update assignee if not already set
        if not config.copilot_assignee:
            config.copilot_assignee = settings.default_assignee

    # Create workflow context
    ctx = WorkflowContext(
        session_id=str(session.session_id),
        project_id=session.selected_project_id,
        access_token=session.access_token,
        repository_owner=config.repository_owner,
        repository_name=config.repository_name,
        recommendation_id=recommendation_id,
        config=config,
    )

    # Execute workflow (T030 - error handling included in orchestrator)
    try:
        orchestrator = get_workflow_orchestrator()
        result = await orchestrator.execute_full_workflow(ctx, recommendation)

        if result.success:
            # Update recommendation status
            recommendation.status = RecommendationStatus.CONFIRMED
            recommendation.confirmed_at = datetime.utcnow()

            # Broadcast WebSocket notification for issue creation
            await connection_manager.broadcast_to_project(
                session.selected_project_id,
                {
                    "type": "issue_created",
                    "issue_id": result.issue_id,
                    "issue_number": result.issue_number,
                    "issue_url": result.issue_url,
                    "title": recommendation.title,
                    "status": result.current_status,
                },
            )

            # T035: Send WebSocket notification for Ready status transition
            if result.current_status == "Ready":
                await connection_manager.broadcast_to_project(
                    session.selected_project_id,
                    {
                        "type": "status_updated",
                        "issue_id": result.issue_id,
                        "issue_number": result.issue_number,
                        "from_status": "Backlog",
                        "to_status": "Ready",
                        "title": recommendation.title,
                    },
                )

            logger.info(
                "Workflow completed: issue #%d created",
                result.issue_number,
            )

        return result

    except Exception as e:
        logger.error("Workflow failed: %s", e)
        return WorkflowResult(
            success=False,
            message=f"Failed to create issue: {str(e)}",
        )


@router.post("/recommendations/{recommendation_id}/reject")
async def reject_recommendation(
    recommendation_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """
    Reject an AI-generated issue recommendation (T026).
    """
    recommendation = _recommendations.get(recommendation_id)
    if not recommendation:
        raise NotFoundError(f"Recommendation not found: {recommendation_id}")

    if str(recommendation.session_id) != str(session.session_id):
        raise NotFoundError(f"Recommendation not found: {recommendation_id}")

    if recommendation.status != RecommendationStatus.PENDING:
        raise ValidationError(
            f"Recommendation already {recommendation.status.value}"
        )

    recommendation.status = RecommendationStatus.REJECTED
    logger.info("Recommendation %s rejected", recommendation_id)

    return {"message": "Recommendation rejected", "recommendation_id": recommendation_id}


@router.get("/config", response_model=WorkflowConfiguration)
async def get_config(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> WorkflowConfiguration:
    """
    Get workflow configuration for the selected project (T039).
    """
    if not session.selected_project_id:
        raise NotFoundError("No project selected")

    config = get_workflow_config(session.selected_project_id)
    if not config:
        # Return default config
        owner, repo = _get_repository_info(session)
        config = WorkflowConfiguration(
            project_id=session.selected_project_id,
            repository_owner=owner or session.github_username or "",
            repository_name=repo or "",
        )

    return config


@router.put("/config", response_model=WorkflowConfiguration)
async def update_config(
    config_update: WorkflowConfiguration,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> WorkflowConfiguration:
    """
    Update workflow configuration (T040).
    """
    if not session.selected_project_id:
        raise NotFoundError("No project selected")

    # Ensure project_id matches
    config_update.project_id = session.selected_project_id

    set_workflow_config(session.selected_project_id, config_update)
    logger.info("Updated workflow config for project %s", session.selected_project_id)

    return config_update


@router.get("/transitions", response_model=list[WorkflowTransition])
async def get_transition_history(
    session: Annotated[UserSession, Depends(get_session_dep)],
    issue_id: str | None = Query(None, description="Filter by issue ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
) -> list[WorkflowTransition]:
    """
    Get workflow transition history (T034).
    """
    transitions = get_transitions(issue_id=issue_id, limit=limit)
    return transitions


@router.post("/notify/in-review")
async def notify_in_review(
    session: Annotated[UserSession, Depends(get_session_dep)],
    issue_id: str = Query(..., description="GitHub Issue node ID"),
    issue_number: int = Query(..., description="Issue number"),
    title: str = Query(..., description="Issue title"),
    reviewer: str = Query(..., description="Assigned reviewer"),
) -> dict:
    """
    Send notification when issue moves to In Review (T047).

    This is called by the workflow orchestrator after detecting completion.
    """
    if not session.selected_project_id:
        raise NotFoundError("No project selected")

    # Broadcast WebSocket notification
    await connection_manager.broadcast_to_project(
        session.selected_project_id,
        {
            "type": "status_updated",
            "issue_id": issue_id,
            "issue_number": issue_number,
            "from_status": "In Progress",
            "to_status": "In Review",
            "title": title,
            "reviewer": reviewer,
        },
    )

    logger.info(
        "Sent In Review notification for issue #%d, reviewer: %s",
        issue_number,
        reviewer,
    )

    return {"message": "Notification sent", "issue_number": issue_number}
