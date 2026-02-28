"""MCP configuration API endpoints — list, create, delete.

Uses AppException subclasses (McpValidationError, McpLimitExceededError,
NotFoundError) so that error responses follow the standard
``{"error": "...", "details": {...}}`` shape handled by the global
exception handler in ``src.main``.  This keeps the format consistent
with the rest of the API and with the frontend ``ApiError`` parser.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.api.auth import get_session_dep
from src.exceptions import NotFoundError
from src.models.mcp import (
    McpConfigurationCreate,
    McpConfigurationListResponse,
    McpConfigurationResponse,
)
from src.models.user import UserSession
from src.services.database import get_db
from src.services.mcp_store import create_mcp, delete_mcp, list_mcps

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/mcps", response_model=McpConfigurationListResponse)
async def list_mcp_configurations(
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> McpConfigurationListResponse:
    """List all MCP configurations for the authenticated user."""
    db = get_db()
    return await list_mcps(db, session.github_user_id)


@router.post(
    "/mcps",
    response_model=McpConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mcp_configuration(
    body: McpConfigurationCreate,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> McpConfigurationResponse:
    """Add a new MCP configuration for the authenticated user."""
    db = get_db()
    # McpValidationError / McpLimitExceededError propagate to the global
    # AppException handler, which returns the correct status code and
    # ``{"error": "..."}`` payload automatically.
    result = await create_mcp(db, session.github_user_id, body)

    logger.info("User %s created MCP %s", session.github_username, result.id)
    return result


@router.delete("/mcps/{mcp_id}")
async def delete_mcp_configuration(
    mcp_id: str,
    session: Annotated[UserSession, Depends(get_session_dep)],
) -> dict:
    """Remove an MCP configuration. Only the owning user can delete."""
    db = get_db()
    deleted = await delete_mcp(db, session.github_user_id, mcp_id)

    if not deleted:
        raise NotFoundError("MCP configuration not found")

    logger.info("User %s deleted MCP %s", session.github_username, mcp_id)
    return {"message": "MCP configuration deleted"}
