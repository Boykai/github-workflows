"""Tools API endpoints — CRUD and sync for MCP tool configurations."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.api.auth import get_session_dep
from src.dependencies import verify_project_access
from src.exceptions import AppException, NotFoundError, ValidationError
from src.models.tools import (
    McpToolConfigCreate,
    McpToolConfigListResponse,
    McpToolConfigResponse,
    McpToolConfigSyncResult,
    McpToolConfigUpdate,
    ToolDeleteResult,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.services.tools.service import DuplicateToolNameError, ToolsService
from src.utils import resolve_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_service() -> ToolsService:
    """Instantiate ToolsService with the current DB connection."""
    return ToolsService(get_db())


# ── List Tools ──


@router.get(
    "/{project_id}",
    response_model=McpToolConfigListResponse,
    dependencies=[Depends(verify_project_access)],
)
async def list_tools(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> McpToolConfigListResponse:
    """List all MCP tool configurations for a project."""
    service = _get_service()
    return await service.list_tools(
        project_id=project_id,
        github_user_id=session.github_user_id,
    )


# ── Create Tool ──


@router.post(
    "/{project_id}",
    response_model=McpToolConfigResponse,
    status_code=201,
    dependencies=[Depends(verify_project_access)],
)
async def create_tool(
    project_id: str,
    data: McpToolConfigCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> McpToolConfigResponse:
    """Upload and create a new MCP tool configuration."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s", project_id, exc_info=True)
        raise ValidationError("Cannot resolve repository for project") from exc

    try:
        return await service.create_tool(
            project_id=project_id,
            github_user_id=session.github_user_id,
            data=data,
            owner=owner,
            repo=repo,
            access_token=session.access_token,
        )
    except DuplicateToolNameError as exc:
        raise AppException(str(exc), status_code=409) from exc
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


# ── Get Tool ──


@router.get(
    "/{project_id}/{tool_id}",
    response_model=McpToolConfigResponse,
    dependencies=[Depends(verify_project_access)],
)
async def get_tool(
    project_id: str,
    tool_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> McpToolConfigResponse:
    """Get a single MCP tool configuration."""
    service = _get_service()
    tool = await service.get_tool(
        project_id=project_id,
        tool_id=tool_id,
        github_user_id=session.github_user_id,
    )
    if not tool:
        raise NotFoundError("Tool not found")
    return tool


@router.put(
    "/{project_id}/{tool_id}",
    response_model=McpToolConfigResponse,
    dependencies=[Depends(verify_project_access)],
)
async def update_tool(
    project_id: str,
    tool_id: str,
    data: McpToolConfigUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> McpToolConfigResponse:
    """Update an existing MCP tool configuration."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s", project_id, exc_info=True)
        raise ValidationError("Cannot resolve repository for project") from exc

    try:
        return await service.update_tool(
            project_id=project_id,
            tool_id=tool_id,
            github_user_id=session.github_user_id,
            data=data,
            owner=owner,
            repo=repo,
            access_token=session.access_token,
        )
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc
    except DuplicateToolNameError as exc:
        raise AppException(str(exc), status_code=409) from exc
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


# ── Sync Tool ──


@router.post(
    "/{project_id}/{tool_id}/sync",
    response_model=McpToolConfigSyncResult,
    dependencies=[Depends(verify_project_access)],
)
async def sync_tool(
    project_id: str,
    tool_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> McpToolConfigSyncResult:
    """Trigger a sync (or re-sync) of an MCP tool to GitHub."""
    service = _get_service()

    tool = await service.get_tool(
        project_id=project_id,
        tool_id=tool_id,
        github_user_id=session.github_user_id,
    )
    if not tool:
        raise NotFoundError("Tool not found")

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s", project_id, exc_info=True)
        raise ValidationError("Cannot resolve repository for project") from exc

    return await service.sync_tool_to_github(
        tool_id=tool_id,
        project_id=project_id,
        github_user_id=session.github_user_id,
        owner=owner,
        repo=repo,
        access_token=session.access_token,
    )


# ── Delete Tool ──


@router.delete(
    "/{project_id}/{tool_id}",
    response_model=ToolDeleteResult,
    dependencies=[Depends(verify_project_access)],
)
async def delete_tool(
    project_id: str,
    tool_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    confirm: bool = Query(default=False),
) -> ToolDeleteResult:
    """Delete an MCP tool configuration."""
    service = _get_service()

    tool = await service.get_tool(
        project_id=project_id,
        tool_id=tool_id,
        github_user_id=session.github_user_id,
    )
    if not tool:
        raise NotFoundError("Tool not found")

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s", project_id, exc_info=True)
        raise ValidationError("Cannot resolve repository for project") from exc

    return await service.delete_tool(
        project_id=project_id,
        tool_id=tool_id,
        github_user_id=session.github_user_id,
        confirm=confirm,
        owner=owner,
        repo=repo,
        access_token=session.access_token,
    )
