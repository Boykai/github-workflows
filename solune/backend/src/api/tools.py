"""Tools API endpoints — CRUD and sync for MCP tool configurations."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.auth import get_session_dep
from src.dependencies import verify_project_access
from src.exceptions import AppException, GitHubAPIError, NotFoundError, ValidationError
from src.logging_utils import get_logger, handle_service_error
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
from src.services.activity_logger import log_event
from src.services.database import get_db
from src.services.tools.presets import list_mcp_presets
from src.services.tools.service import (
    DuplicateToolNameError,
    DuplicateToolServerNameError,
    ToolsService,
)
from src.utils import resolve_repository

logger = get_logger(__name__)
router = APIRouter()


def _get_service() -> ToolsService:
    """Instantiate ToolsService with the current DB connection and GitHub service."""
    from src.services.github_projects import github_projects_service

    return ToolsService(get_db(), github_service=github_projects_service)


@router.get("/presets", response_model=McpPresetListResponse)
async def list_presets() -> McpPresetListResponse:
    """List static MCP presets for quick tool creation."""
    return list_mcp_presets()


# ── List Tools ──


@router.get(
    "/{project_id}",
    dependencies=[Depends(verify_project_access)],
)
async def list_tools(
    project_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
    limit: Annotated[int | None, Query(ge=1, le=100, description="Items per page")] = None,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
) -> McpToolConfigListResponse | dict:
    """List all MCP tool configurations for a project."""
    service = _get_service()
    result = await service.list_tools(
        project_id=project_id,
        github_user_id=session.github_user_id,
    )

    if limit is not None or cursor is not None:
        from src.services.pagination import apply_pagination

        try:
            paginated = apply_pagination(
                result.tools, limit=limit or 25, cursor=cursor, key_fn=lambda t: t.id
            )
        except ValueError as exc:
            from src.exceptions import ValidationError

            raise ValidationError(str(exc)) from exc
        return {
            "tools": [t.model_dump() for t in paginated.items],
            "count": result.count,
            "next_cursor": paginated.next_cursor,
            "has_more": paginated.has_more,
            "total_count": paginated.total_count,
        }

    return result


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

    # HTTPException kept as-is: MCP framework expects {"detail": ...} response shape
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
        handle_service_error(exc, "fetch repository MCP config", GitHubAPIError)


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
        handle_service_error(exc, "resolve repository for project", ValidationError)

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
    except RuntimeError as exc:
        handle_service_error(exc, "update repository MCP server", GitHubAPIError)


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
        handle_service_error(exc, "resolve repository for project", ValidationError)

    try:
        return await service.delete_repo_mcp_server(
            owner=owner,
            repo=repo,
            access_token=session.access_token,
            server_name=server_name,
        )
    except LookupError as exc:
        raise NotFoundError(str(exc)) from exc
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc
    except RuntimeError as exc:
        handle_service_error(exc, "delete repository MCP server", GitHubAPIError)


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
        handle_service_error(exc, "resolve repository for project", ValidationError)

    try:
        result = await service.create_tool(
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

    await log_event(
        get_db(),
        event_type="tool_crud",
        entity_type="tool",
        entity_id=result.id,
        project_id=project_id,
        actor=session.github_username,
        action="created",
        summary=f"Tool '{data.name}' created",
        detail={"entity_name": data.name},
    )

    return result


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
        handle_service_error(exc, "resolve repository for project", ValidationError)

    try:
        result = await service.update_tool(
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

    await log_event(
        get_db(),
        event_type="tool_crud",
        entity_type="tool",
        entity_id=tool_id,
        project_id=project_id,
        actor=session.github_username,
        action="updated",
        summary=f"Tool '{tool_id}' updated",
        detail={"entity_name": tool_id},
    )

    return result


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
        handle_service_error(exc, "resolve repository for project", ValidationError)

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
        handle_service_error(exc, "resolve repository for project", ValidationError)

    result = await service.delete_tool(
        project_id=project_id,
        tool_id=tool_id,
        github_user_id=session.github_user_id,
        confirm=confirm,
        owner=owner,
        repo=repo,
        access_token=session.access_token,
    )

    await log_event(
        get_db(),
        event_type="tool_crud",
        entity_type="tool",
        entity_id=tool_id,
        project_id=project_id,
        actor=session.github_username,
        action="deleted",
        summary=f"Tool '{tool_id}' deleted",
        detail={"entity_name": tool_id},
    )

    return result
