"""Agents API endpoints — CRUD and chat for Custom GitHub Agent configurations."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.api.auth import get_session_dep
from src.exceptions import GitHubAPIError, NotFoundError, ValidationError
from src.logging_utils import handle_service_error
from src.dependencies import verify_project_access
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
from src.services.agents.service import AgentsService
from src.services.database import get_db
from src.utils import resolve_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_service() -> AgentsService:
    """Instantiate AgentsService with the current DB connection."""
    return AgentsService(get_db())


# ── List ──


@router.get(
    "/{project_id}", response_model=list[Agent], dependencies=[Depends(verify_project_access)]
)
async def list_agents(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[Agent]:
    """List agents visible on the repository default branch under .github/agents/."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise ValidationError("Could not resolve repository for this project") from exc

    return await service.list_agents(
        project_id=project_id,
        owner=owner,
        repo=repo,
        access_token=session.access_token,
    )


@router.get("/{project_id}/pending", response_model=list[Agent])
async def list_pending_agents(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[Agent]:
    """List agent PR work that is still pending merge or pending deletion."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise ValidationError("Could not resolve repository for this project") from exc

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
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise ValidationError("Could not resolve repository for this project") from exc

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
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise ValidationError("Could not resolve repository for this project") from exc

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
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise ValidationError("Could not resolve repository for this project") from exc

    try:
        return await service.create_agent(
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
        handle_service_error(exc, "Agent creation failed", GitHubAPIError)


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
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise ValidationError("Could not resolve repository for this project") from exc

    try:
        return await service.update_agent(
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
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise ValidationError("Could not resolve repository for this project") from exc

    try:
        return await service.delete_agent(
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
        handle_service_error(exc, "Agent deletion failed", GitHubAPIError)


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
        handle_service_error(exc, "Chat completion failed", GitHubAPIError)


# ── Agent-Tool Associations ──


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
    from src.services.tools.service import ToolsService

    service = ToolsService(get_db())
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
    from src.services.tools.service import ToolsService

    service = ToolsService(get_db())

    try:
        return await service.update_agent_tools(
            agent_id=agent_id,
            tool_ids=body.tool_ids,
            project_id=project_id,
            github_user_id=session.github_user_id,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
