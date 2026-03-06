"""Agents API endpoints — CRUD and chat for Custom GitHub Agent configurations."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from src.api.auth import get_session_dep
from src.models.agents import (
    Agent,
    AgentChatMessage,
    AgentChatResponse,
    AgentCreate,
    AgentCreateResult,
    AgentDeleteResult,
    AgentUpdate,
)
from src.models.user import UserSession
from src.rate_limit import limiter
from src.services.agents.service import AgentsService
from src.services.database import get_db
from src.utils import resolve_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_service() -> AgentsService:
    """Instantiate AgentsService with the current DB connection."""
    return AgentsService(get_db())


# ── List ──


@router.get("/{project_id}", response_model=list[Agent])
async def list_agents(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> list[Agent]:
    """List all agents for a project (merged from SQLite + GitHub repo)."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s: %s", project_id, exc)
        raise HTTPException(
            status_code=400,
            detail="Could not resolve repository for this project",
        ) from exc

    return await service.list_agents(
        project_id=project_id,
        owner=owner,
        repo=repo,
        access_token=session.access_token,
    )


# ── Create ──


@router.post("/{project_id}", response_model=AgentCreateResult, status_code=201)
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
        raise HTTPException(
            status_code=400,
            detail="Could not resolve repository for this project",
        ) from exc

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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Agent creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Agent creation failed") from exc


# ── Update (P3) ──


@router.patch("/{project_id}/{agent_id}", response_model=AgentCreateResult)
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
        raise HTTPException(
            status_code=400,
            detail="Could not resolve repository for this project",
        ) from exc

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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── Delete ──


@router.delete("/{project_id}/{agent_id}", response_model=AgentDeleteResult)
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
        raise HTTPException(
            status_code=400,
            detail="Could not resolve repository for this project",
        ) from exc

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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.error("Agent deletion failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Agent deletion failed") from exc


# ── Chat ──


@router.post("/{project_id}/chat", response_model=AgentChatResponse)
@limiter.limit("30/minute")
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
        logger.error("Agent chat failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Chat completion failed") from exc
