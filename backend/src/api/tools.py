"""Tools API endpoints — CRUD and sync for MCP tool configurations."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.auth import get_session_dep
from src.dependencies import verify_project_access
from src.exceptions import AppException, GitHubAPIError, NotFoundError, ValidationError
from src.models.tools import (
    McpPresetListResponse,
    McpToolConfigCreate,
    McpToolConfigListResponse,
    McpToolConfigResponse,
    McpToolConfigSyncResult,
    McpToolConfigUpdate,
    RepoMcpConfigResponse,
    RepoMcpServerConfig,
    RepoMcpServerUpdate,
    ToolDeleteResult,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.services.tools.presets import list_mcp_presets
from src.services.tools.service import (
    DuplicateToolNameError,
    DuplicateToolServerNameError,
    ToolsService,
)
from src.utils import resolve_repository

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_service() -> ToolsService:
    """Instantiate ToolsService with the current DB connection."""
    return ToolsService(get_db())


@router.get("/presets", response_model=McpPresetListResponse)
async def list_presets() -> McpPresetListResponse:
    """List static MCP presets for quick tool creation."""
    return list_mcp_presets()


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


@router.get(
    "/{project_id}/repo-config",
    response_model=RepoMcpConfigResponse,
    dependencies=[Depends(verify_project_access)],
)
async def get_repo_config(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> RepoMcpConfigResponse:
    """Read repository MCP configuration from supported GitHub paths."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resolve repository: {exc}",
        ) from exc

    try:
        return await service.get_repo_mcp_config(
            owner=owner,
            repo=repo,
            access_token=session.access_token,
        )
    except Exception as exc:
        logger.exception(
            "Failed to fetch repository MCP config for project %s (%s/%s)",
            project_id,
            owner,
            repo,
        )
        raise GitHubAPIError("Failed to fetch repository MCP config") from exc


@router.put(
    "/{project_id}/repo-config/{server_name}",
    response_model=RepoMcpServerConfig,
    dependencies=[Depends(verify_project_access)],
)
async def update_repo_server(
    project_id: str,
    server_name: str,
    data: RepoMcpServerUpdate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> RepoMcpServerConfig:
    """Update an existing repository MCP server directly in repo config files."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s", project_id, exc_info=True)
        raise ValidationError("Cannot resolve repository for project") from exc

    try:
        return await service.update_repo_mcp_server(
            owner=owner,
            repo=repo,
            access_token=session.access_token,
            server_name=server_name,
            data=data,
        )
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


@router.delete(
    "/{project_id}/repo-config/{server_name}",
    response_model=RepoMcpServerConfig,
    dependencies=[Depends(verify_project_access)],
)
async def delete_repo_server(
    project_id: str,
    server_name: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> RepoMcpServerConfig:
    """Delete an existing repository MCP server directly from repo config files."""
    service = _get_service()

    try:
        owner, repo = await resolve_repository(session.access_token, project_id)
    except Exception as exc:
        logger.error("Failed to resolve repository for project %s", project_id, exc_info=True)
        raise ValidationError("Cannot resolve repository for project") from exc

    try:
        return await service.delete_repo_mcp_server(
            owner=owner,
            repo=repo,
            access_token=session.access_token,
            server_name=server_name,
        )
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc


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
    except (DuplicateToolNameError, DuplicateToolServerNameError) as exc:
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
    except (DuplicateToolNameError, DuplicateToolServerNameError) as exc:
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
