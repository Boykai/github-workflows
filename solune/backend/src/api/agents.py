"""Agents API endpoints — CRUD and chat for Custom GitHub Agent configurations."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from src.api.auth import get_session_dep
from src.dependencies import verify_project_access
from src.exceptions import AppException, GitHubAPIError, NotFoundError, ValidationError
from src.logging_utils import get_logger, handle_service_error
from src.middleware.rate_limit import limiter
from src.models.agents import (
    Agent,
    AgentChatMessage,
    AgentChatResponse,
    AgentCreate,
    AgentCreateResult,
    AgentDeleteResult,
    AgentPendingCleanupResult,
    AgentUpdate,
    BulkModelUpdateRequest,
    BulkModelUpdateResult,
)
from src.models.tools import AgentToolsResponse, AgentToolsUpdate
from src.models.user import UserSession
from src.services.activity_logger import log_event
from src.services.agents.service import AgentsService
from src.services.database import get_db
from src.utils import resolve_repository

logger = get_logger(__name__)
router = APIRouter()


def _get_service() -> AgentsService:
    """Instantiate AgentsService with the current DB connection."""
    return AgentsService(get_db())


# ── List ──


@router.get("/{project_id}", dependencies=[Depends(verify_project_access)])
async def list_agents(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    limit: Annotated[int | None, Query(ge=1, le=100, description="Items per page")] = None,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
) -> list[Agent] | dict:
    """List agents visible on the repository default branch under .github/agents/."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    agents = await service.list_agents(
        project_id=project_id,
        owner=owner,
        repo=repo,
        access_token=session.access_token,
    )

    if limit is not None or cursor is not None:
        from src.services.pagination import apply_pagination

        try:
            result = apply_pagination(
                agents, limit=limit or 25, cursor=cursor, key_fn=lambda a: a.id
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return result.model_dump()

    return agents


@router.get("/{project_id}/pending", response_model=list[Agent])
async def list_pending_agents(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[Agent]:
    """List agent PR work that is still pending merge or pending deletion."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    return await service.list_pending_agents(
        project_id=project_id,
        owner=owner,
        repo=repo,
        access_token=session.access_token,
    )


@router.delete("/{project_id}/pending", response_model=AgentPendingCleanupResult)
async def purge_pending_agents(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> AgentPendingCleanupResult:
    """Delete stale pending agent rows from SQLite for the selected project."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    logger.info(
        "Purging stale pending agents for project %s (%s/%s)",
        project_id,
        owner,
        repo,
    )
    return await service.purge_pending_agents(project_id=project_id)


# ── Bulk Model Update ──


@router.patch(
    "/{project_id}/bulk-model",
    response_model=BulkModelUpdateResult,
    dependencies=[Depends(verify_project_access)],
)
async def bulk_update_models(
    project_id: str,
    body: BulkModelUpdateRequest,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> BulkModelUpdateResult:
    """Update the default model for all active agents in a project."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    return await service.bulk_update_models(
        project_id=project_id,
        owner=owner,
        repo=repo,
        github_user_id=session.github_user_id,
        body=body,
        access_token=session.access_token,
    )


# ── Create ──


@router.post(
    "/{project_id}",
    response_model=AgentCreateResult,
    status_code=201,
    dependencies=[Depends(verify_project_access)],
)
async def create_agent(
    project_id: str,
    body: AgentCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> AgentCreateResult:
    """Create a new Custom GitHub Agent (branch + commit + PR)."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    try:
        result = await service.create_agent(
            project_id=project_id,
            owner=owner,
            repo=repo,
            body=body,
            access_token=session.access_token,
            github_user_id=session.github_user_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    except RuntimeError as exc:
        handle_service_error(exc, "create agent", GitHubAPIError)

    await log_event(
        get_db(),
        event_type="agent_crud",
        entity_type="agent",
        entity_id=result.agent.id if result.agent else project_id,
        project_id=project_id,
        actor=session.github_username,
        action="created",
        summary=f"Agent '{body.name}' created",
        detail={"entity_name": body.name},
    )

    return result


# ── Update (P3) ──


@router.patch(
    "/{project_id}/{agent_id}",
    response_model=AgentCreateResult,
    dependencies=[Depends(verify_project_access)],
)
async def update_agent(
    project_id: str,
    agent_id: str,
    body: AgentUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> AgentCreateResult:
    """Update an existing agent's configuration (opens PR with changes)."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    try:
        result = await service.update_agent(
            project_id=project_id,
            owner=owner,
            repo=repo,
            agent_id=agent_id,
            body=body,
            access_token=session.access_token,
            github_user_id=session.github_user_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc

    await log_event(
        get_db(),
        event_type="agent_crud",
        entity_type="agent",
        entity_id=agent_id,
        project_id=project_id,
        actor=session.github_username,
        action="updated",
        summary=f"Agent '{agent_id}' updated",
        detail={"entity_name": agent_id},
    )

    return result


# ── Delete ──


@router.delete(
    "/{project_id}/{agent_id}",
    response_model=AgentDeleteResult,
    dependencies=[Depends(verify_project_access)],
)
async def delete_agent(
    project_id: str,
    agent_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> AgentDeleteResult:
    """Delete an agent — opens a PR to remove files from the repo."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    try:
        result = await service.delete_agent(
            project_id=project_id,
            owner=owner,
            repo=repo,
            agent_id=agent_id,
            access_token=session.access_token,
            github_user_id=session.github_user_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc
    except RuntimeError as exc:
        handle_service_error(exc, "delete agent", GitHubAPIError)

    await log_event(
        get_db(),
        event_type="agent_crud",
        entity_type="agent",
        entity_id=agent_id,
        project_id=project_id,
        actor=session.github_username,
        action="deleted",
        summary=f"Agent '{agent_id}' deleted",
        detail={"entity_name": agent_id},
    )

    return result


# ── Chat ──


@router.post(
    "/{project_id}/chat",
    response_model=AgentChatResponse,
    dependencies=[Depends(verify_project_access)],
)
@limiter.limit("5/minute")
async def agent_chat(
    request: Request,
    project_id: str,
    body: AgentChatMessage,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> AgentChatResponse:
    """AI-assisted agent content refinement (multi-turn chat)."""
    service = _get_service()

    try:
        return await service.chat(
            project_id=project_id,
            message=body.message,
            session_id=body.session_id,
            access_token=session.access_token,
        )
    except Exception as exc:
        handle_service_error(exc, "complete agent chat", AppException)


# ── Agent-Tool Associations ──


# ── Sync MCPs ──


@router.post(
    "/{project_id}/sync-mcps",
    dependencies=[Depends(verify_project_access)],
)
async def sync_agent_mcps_endpoint(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Synchronize MCP configurations across all agent files in the repository."""
    from src.services.agents.agent_mcp_sync import sync_agent_mcps

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except AppException:
        raise
    except Exception as exc:
        handle_service_error(exc, "resolve repository", ValidationError)

    result = await sync_agent_mcps(
        owner=owner,
        repo=repo,
        project_id=project_id,
        access_token=session.access_token,
        trigger="manual",
        db=get_db(),
    )

    return {
        "success": result.success,
        "files_updated": result.files_updated,
        "files_skipped": result.files_skipped,
        "files_unchanged": result.files_unchanged,
        "warnings": result.warnings,
        "errors": result.errors,
        "synced_mcps": result.synced_mcps,
    }


# ── Agent-Tool Associations (endpoints below) ──


@router.get(
    "/{project_id}/{agent_id}/tools",
    response_model=AgentToolsResponse,
    dependencies=[Depends(verify_project_access)],
)
async def get_agent_tools(
    project_id: str,
    agent_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> AgentToolsResponse:
    """List MCP tools assigned to a specific agent."""
    from src.services.github_projects import github_projects_service
    from src.services.tools.service import ToolsService

    service = ToolsService(get_db(), github_service=github_projects_service)
    return await service.get_agent_tools(
        agent_id=agent_id,
        project_id=project_id,
        github_user_id=session.github_user_id,
    )


@router.put(
    "/{project_id}/{agent_id}/tools",
    response_model=AgentToolsResponse,
    dependencies=[Depends(verify_project_access)],
)
async def update_agent_tools(
    project_id: str,
    agent_id: str,
    body: AgentToolsUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> AgentToolsResponse:
    """Set the MCP tools for an agent (replace all)."""
    from src.services.github_projects import github_projects_service
    from src.services.tools.service import ToolsService

    service = ToolsService(get_db(), github_service=github_projects_service)

    try:
        return await service.update_agent_tools(
            agent_id=agent_id,
            tool_ids=body.tool_ids,
            project_id=project_id,
            github_user_id=session.github_user_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
