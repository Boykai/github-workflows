"""Workflow API endpoints for issue creation and management."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_session_dep
from src.api.chat import _recommendations
from src.exceptions import NotFoundError, ValidationError
from src.models.agent import AvailableAgentsResponse
from src.models.recommendation import RecommendationStatus
from src.models.workflow import (
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
    get_agent_slugs,
    get_all_pipeline_states,
    get_pipeline_state,
    get_transitions,
    get_workflow_config,
    get_workflow_orchestrator,
    set_pipeline_state,
    set_workflow_config,
)
from src.utils import resolve_repository, utcnow

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow", tags=["Workflow"])

# In-memory duplicate detection (T029)
# Maps hash of original_input to (timestamp, recommendation_id)
_recent_requests: dict[str, tuple[datetime, str]] = {}
DUPLICATE_WINDOW_MINUTES = 5


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
    now = utcnow()
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
        raise ValidationError(f"Recommendation already {recommendation.status.value}")

    # Check for duplicates (T029)
    if _check_duplicate(recommendation.original_input, recommendation_id):
        raise ValidationError(
            "A similar request was recently processed. Please wait a few minutes."
        )

    # Require project selection
    if not session.selected_project_id:
        raise ValidationError("Please select a project first")

    # Resolve repository info using shared 3-step fallback
    owner, repo = await resolve_repository(session.access_token, session.selected_project_id)

    logger.info("Using repository %s/%s for issue creation", owner, repo)

    # Get settings for default assignee
    from src.config import get_settings

    settings = get_settings()

    # Get or create workflow config
    config = await get_workflow_config(session.selected_project_id)
    if not config:
        config = WorkflowConfiguration(
            project_id=session.selected_project_id,
            repository_owner=owner,
            repository_name=repo,
            copilot_assignee=settings.default_assignee,
        )
        await set_workflow_config(
            session.selected_project_id,
            config,
            github_user_id=session.github_user_id,
        )
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
            recommendation.confirmed_at = utcnow()

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

            # Send agent_assigned notification for the first Backlog agent
            backlog_slugs = get_agent_slugs(config, config.status_backlog)
            if backlog_slugs:
                await connection_manager.broadcast_to_project(
                    session.selected_project_id,
                    {
                        "type": "agent_assigned",
                        "issue_number": result.issue_number,
                        "agent_name": backlog_slugs[0],
                        "status": "Backlog",
                        "next_agent": (backlog_slugs[1] if len(backlog_slugs) > 1 else None),
                        "timestamp": utcnow().isoformat(),
                    },
                )

            logger.info(
                "Workflow completed: issue #%d created and placed in Backlog",
                result.issue_number,
            )

            # Ensure Copilot polling is running so the pipeline advances
            from src.services.copilot_polling import ensure_polling_started

            await ensure_polling_started(
                access_token=session.access_token,
                project_id=session.selected_project_id,
                owner=owner,
                repo=repo,
                caller="confirm_recommendation",
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
        raise ValidationError(f"Recommendation already {recommendation.status.value}")

    recommendation.status = RecommendationStatus.REJECTED
    logger.info("Recommendation %s rejected", recommendation_id)

    return {
        "message": "Recommendation rejected",
        "recommendation_id": recommendation_id,
    }


@router.post("/pipeline/{issue_number}/retry")
async def retry_pipeline(
    issue_number: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """
    Retry a failed or stalled agent assignment for an issue.

    Looks up the pipeline state for the given issue number and retries
    the current agent assignment. This is useful when:
    - Agent assignment failed due to transient errors
    - The pipeline is stuck after a network failure
    - The user wants to manually kick off the next agent
    """
    if not session.selected_project_id:
        raise ValidationError("No project selected")

    state = get_pipeline_state(issue_number)
    if not state:
        raise NotFoundError(f"No pipeline state found for issue #{issue_number}")

    if state.project_id != session.selected_project_id:
        raise NotFoundError(f"No pipeline state found for issue #{issue_number}")

    if state.is_complete:
        return {"message": "Pipeline already complete", "issue_number": issue_number}

    current_agent = state.current_agent
    if not current_agent:
        return {"message": "No pending agent to retry", "issue_number": issue_number}

    # Get config and build context
    config = await get_workflow_config(state.project_id)
    if not config:
        raise ValidationError("No workflow configuration found for this project")

    # Resolve repository info
    repo_info = await github_projects_service.get_project_repository(
        session.access_token,
        session.selected_project_id,
    )

    if repo_info:
        owner, repo = repo_info
    else:
        owner = config.repository_owner
        repo = config.repository_name

    if not owner or not repo:
        from src.config import get_settings

        settings = get_settings()
        owner = owner or settings.default_repo_owner or ""
        repo = repo or settings.default_repo_name or ""

    if not owner or not repo:
        raise ValidationError("No repository configured for this project")

    ctx = WorkflowContext(
        session_id=str(session.session_id),
        project_id=state.project_id,
        access_token=session.access_token,
        repository_owner=owner,
        repository_name=repo,
        config=config,
    )

    # Get issue info
    try:
        issue_data = await github_projects_service.get_issue_with_comments(
            access_token=session.access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )
        ctx.issue_id = issue_data.get("node_id", "")
        ctx.issue_number = issue_number
        ctx.issue_url = issue_data.get("html_url", "")
    except Exception as e:
        raise ValidationError(f"Failed to fetch issue #{issue_number}: {e}") from e

    # Clear the error state so retry proceeds
    state.error = None
    set_pipeline_state(issue_number, state)

    # Clear any pending assignment dedup guards for this agent
    try:
        from src.services.copilot_polling import _pending_agent_assignments

        pending_key = f"{issue_number}:{current_agent}"
        _pending_agent_assignments.pop(pending_key, None)
    except ImportError:
        pass

    # Retry the assignment
    orchestrator = get_workflow_orchestrator()
    success = await orchestrator.assign_agent_for_status(
        ctx, state.status, agent_index=state.current_agent_index
    )

    if success:
        logger.info(
            "Retry succeeded: agent '%s' assigned to issue #%d",
            current_agent,
            issue_number,
        )

        # Send WebSocket notification
        await connection_manager.broadcast_to_project(
            state.project_id,
            {
                "type": "agent_assigned",
                "issue_number": issue_number,
                "agent_name": current_agent,
                "status": state.status,
            },
        )

        return {
            "message": f"Successfully retried agent '{current_agent}' on issue #{issue_number}",
            "issue_number": issue_number,
            "agent": current_agent,
            "success": True,
        }
    else:
        logger.warning(
            "Retry failed: agent '%s' on issue #%d",
            current_agent,
            issue_number,
        )
        return {
            "message": f"Retry failed for agent '{current_agent}' on issue #{issue_number}",
            "issue_number": issue_number,
            "agent": current_agent,
            "success": False,
        }


@router.get("/config", response_model=WorkflowConfiguration)
async def get_config(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> WorkflowConfiguration:
    """
    Get workflow configuration for the selected project (T039).
    """
    if not session.selected_project_id:
        raise NotFoundError("No project selected")

    config = await get_workflow_config(session.selected_project_id)
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

    await set_workflow_config(
        session.selected_project_id,
        config_update,
        github_user_id=session.github_user_id,
    )
    logger.info("Updated workflow config for project %s", session.selected_project_id)

    return config_update


@router.get("/agents", response_model=AvailableAgentsResponse)
async def list_agents(
    session: Annotated[UserSession, Depends(get_session_dep)],
    owner: str | None = Query(None, description="Repository owner (default: config)"),
    repo: str | None = Query(None, description="Repository name (default: config)"),
) -> AvailableAgentsResponse:
    """
    List available agents for the selected repository (T017).

    Discovers agents from the repository's `.github/agents/*.agent.md` files
    and combines them with built-in agents (GitHub Copilot, Copilot Review).
    """
    if not session.selected_project_id:
        raise NotFoundError("No project selected")

    # Resolve owner/repo
    resolved_owner = owner
    resolved_repo = repo

    if not resolved_owner or not resolved_repo:
        config = await get_workflow_config(session.selected_project_id)
        if config:
            resolved_owner = resolved_owner or config.repository_owner
            resolved_repo = resolved_repo or config.repository_name

    if not resolved_owner or not resolved_repo:
        resolved_owner, resolved_repo = _get_repository_info(session)

    agents = await github_projects_service.list_available_agents(
        owner=resolved_owner or "",
        repo=resolved_repo or "",
        access_token=session.access_token,
    )

    return AvailableAgentsResponse(agents=agents)


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


@router.get("/pipeline-states")
async def list_pipeline_states(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """
    Get all active pipeline states for the current project.

    Returns pipeline progress for all issues being tracked.
    """
    all_states = get_all_pipeline_states()

    # Filter to states matching the user's selected project
    project_states = {}
    if session.selected_project_id:
        project_states = {
            k: {
                "issue_number": v.issue_number,
                "project_id": v.project_id,
                "status": v.status,
                "agents": v.agents,
                "current_agent_index": v.current_agent_index,
                "current_agent": v.current_agent,
                "completed_agents": v.completed_agents,
                "is_complete": v.is_complete,
                "started_at": v.started_at.isoformat() if v.started_at else None,
                "error": v.error,
            }
            for k, v in all_states.items()
            if v.project_id == session.selected_project_id
        }

    return {
        "pipeline_states": project_states,
        "count": len(project_states),
    }


@router.get("/pipeline-states/{issue_number}")
async def get_pipeline_state_for_issue(
    issue_number: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """
    Get pipeline state for a specific issue.

    Returns the current pipeline progress including which agent is active.
    """
    state = get_pipeline_state(issue_number)

    if not state:
        raise NotFoundError(f"No pipeline state found for issue #{issue_number}")

    # Verify project access
    if session.selected_project_id and state.project_id != session.selected_project_id:
        raise NotFoundError(f"No pipeline state found for issue #{issue_number}")

    return {
        "issue_number": state.issue_number,
        "project_id": state.project_id,
        "status": state.status,
        "agents": state.agents,
        "current_agent_index": state.current_agent_index,
        "current_agent": state.current_agent,
        "completed_agents": state.completed_agents,
        "is_complete": state.is_complete,
        "started_at": state.started_at.isoformat() if state.started_at else None,
        "error": state.error,
    }


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


# ──────────────────────────────────────────────────────────────────────────────
# Copilot PR Polling Endpoints
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/polling/status")
async def get_polling_status(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Get the current status of the Copilot PR polling service."""
    from src.services.copilot_polling import get_polling_status

    return get_polling_status()


@router.post("/polling/check-issue/{issue_number}")
async def check_issue_copilot_completion(
    issue_number: int,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """
    Manually check a specific issue for Copilot PR completion.

    If a Copilot PR is found ready (not draft), the issue status
    will be updated to "In Review".
    """
    if not session.selected_project_id:
        raise ValidationError("No project selected")

    # Get repository info
    repo_info = await github_projects_service.get_project_repository(
        session.access_token,
        session.selected_project_id,
    )

    if not repo_info:
        config = await get_workflow_config(session.selected_project_id)
        if config and config.repository_owner and config.repository_name:
            repo_info = (config.repository_owner, config.repository_name)
        else:
            from src.config import get_settings

            settings = get_settings()
            if settings.default_repo_owner and settings.default_repo_name:
                repo_info = (settings.default_repo_owner, settings.default_repo_name)
            else:
                raise ValidationError("No repository configured for this project")

    owner, repo = repo_info

    from src.services.copilot_polling import check_issue_for_copilot_completion

    result = await check_issue_for_copilot_completion(
        access_token=session.access_token,
        project_id=session.selected_project_id,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )

    # Broadcast WebSocket notification if status was updated
    if result.get("status") == "success":
        await connection_manager.broadcast_to_project(
            session.selected_project_id,
            {
                "type": "status_updated",
                "issue_number": issue_number,
                "from_status": "In Progress",
                "to_status": "In Review",
                "title": result.get("task_title", f"Issue #{issue_number}"),
                "pr_number": result.get("pr_number"),
                "triggered_by": "polling",
            },
        )

    return result


@router.post("/polling/start")
async def start_copilot_polling(
    session: Annotated[UserSession, Depends(get_session_dep)],
    interval_seconds: int = 15,
) -> dict:
    """
    Start background polling for Copilot PR completions.

    Args:
        interval_seconds: Polling interval in seconds (default: 15)
    """
    if not session.selected_project_id:
        raise ValidationError("No project selected")

    from src.services.copilot_polling import (
        get_polling_status,
        poll_for_copilot_completion,
    )

    status = get_polling_status()
    if status["is_running"]:
        return {"message": "Polling is already running", "status": status}

    # Get repository info
    repo_info = await github_projects_service.get_project_repository(
        session.access_token,
        session.selected_project_id,
    )

    if not repo_info:
        config = await get_workflow_config(session.selected_project_id)
        if config and config.repository_owner and config.repository_name:
            repo_info = (config.repository_owner, config.repository_name)
        else:
            from src.config import get_settings

            settings = get_settings()
            if settings.default_repo_owner and settings.default_repo_name:
                repo_info = (settings.default_repo_owner, settings.default_repo_name)
            else:
                raise ValidationError("No repository configured for this project")

    owner, repo = repo_info

    from src.services.copilot_polling import ensure_polling_started

    await ensure_polling_started(
        access_token=session.access_token,
        project_id=session.selected_project_id,
        owner=owner,
        repo=repo,
        interval_seconds=interval_seconds,
        caller="start_polling_endpoint",
    )

    logger.info(
        "Started Copilot PR polling for project %s (interval: %ds)",
        session.selected_project_id,
        interval_seconds,
    )

    return {
        "message": "Polling started",
        "interval_seconds": interval_seconds,
        "project_id": session.selected_project_id,
        "repository": f"{owner}/{repo}",
    }


@router.post("/polling/stop")
async def stop_copilot_polling(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Stop the background Copilot PR polling."""
    from src.services.copilot_polling import get_polling_status, stop_polling

    status = get_polling_status()
    if not status["is_running"]:
        return {"message": "Polling is not running", "status": status}

    stop_polling()

    logger.info("Stopped Copilot PR polling")

    return {"message": "Polling stopped", "status": get_polling_status()}


@router.post("/polling/check-all")
async def check_all_in_progress_issues(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """
    Check all issues in "In Progress" status for Copilot PR completion.

    This triggers a one-time scan of all in-progress issues.
    """
    if not session.selected_project_id:
        raise ValidationError("No project selected")

    # Get repository info
    repo_info = await github_projects_service.get_project_repository(
        session.access_token,
        session.selected_project_id,
    )

    if not repo_info:
        config = await get_workflow_config(session.selected_project_id)
        if config and config.repository_owner and config.repository_name:
            repo_info = (config.repository_owner, config.repository_name)
        else:
            from src.config import get_settings

            settings = get_settings()
            if settings.default_repo_owner and settings.default_repo_name:
                repo_info = (settings.default_repo_owner, settings.default_repo_name)
            else:
                raise ValidationError("No repository configured for this project")

    owner, repo = repo_info

    from src.services.copilot_polling import check_in_progress_issues

    results = await check_in_progress_issues(
        access_token=session.access_token,
        project_id=session.selected_project_id,
        owner=owner,
        repo=repo,
    )

    # Broadcast WebSocket notifications for any updated issues
    for result in results:
        if result.get("status") == "success":
            await connection_manager.broadcast_to_project(
                session.selected_project_id,
                {
                    "type": "status_updated",
                    "issue_number": result.get("issue_number"),
                    "from_status": "In Progress",
                    "to_status": "In Review",
                    "title": result.get("task_title"),
                    "pr_number": result.get("pr_number"),
                    "triggered_by": "polling",
                },
            )

    return {
        "checked_count": len(results),
        "results": results,
    }
