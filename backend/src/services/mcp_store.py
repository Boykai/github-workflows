"""MCP configuration CRUD operations and SSRF URL validation."""

import ipaddress
import logging
import uuid
from urllib.parse import urlparse

import aiosqlite

from src.exceptions import McpLimitExceededError, McpValidationError
from src.models.mcp import (
    McpConfigurationCreate,
    McpConfigurationListResponse,
    McpConfigurationResponse,
)
from src.utils import utcnow

logger = logging.getLogger(__name__)

MAX_MCPS_PER_USER = 25

# ── SSRF Validation ──


def validate_url_not_ssrf(url: str) -> str:
    """Validate that a URL does not point to private/reserved IP ranges.

    Args:
        url: The endpoint URL to validate.

    Returns:
        The validated URL string.

    Raises:
        ValueError: If the URL is invalid, uses a non-HTTP(S) scheme,
            or resolves to a private/reserved IP address.
    """
    parsed = urlparse(url)

    # Enforce HTTP(S) scheme
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("URL must have a valid hostname")

    # Normalize hostname for consistent checks (strip whitespace, lowercase,
    # remove trailing dot so "localhost." is treated the same as "localhost").
    normalized_host = hostname.strip().lower().rstrip(".")

    # Try to parse as IP address and check for private/reserved/unspecified ranges
    try:
        ip = ipaddress.ip_address(normalized_host)
    except ValueError as exc:
        # Not an IP address — it's a hostname; check common localhost-style names.
        # Matching on the first DNS label catches "localhost", "localhost.localdomain", etc.
        labels = normalized_host.split(".") if normalized_host else []
        if labels and labels[0] == "localhost":
            raise ValueError("URL points to a private or reserved IP address") from exc
    else:
        if (
            ip.is_private
            or ip.is_reserved
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_unspecified
        ):
            raise ValueError("URL points to a private or reserved IP address")

    return url


# ── CRUD Operations ──


async def list_mcps(db: aiosqlite.Connection, github_user_id: str) -> McpConfigurationListResponse:
    """List all MCP configurations for a user.

    Args:
        db: Database connection.
        github_user_id: The authenticated user's GitHub ID.

    Returns:
        McpConfigurationListResponse with all user's MCPs.
    """
    cursor = await db.execute(
        "SELECT id, name, endpoint_url, is_active, created_at, updated_at "
        "FROM mcp_configurations WHERE github_user_id = ? ORDER BY created_at DESC",
        (github_user_id,),
    )
    rows = await cursor.fetchall()

    mcps = [
        McpConfigurationResponse(
            id=row["id"],
            name=row["name"],
            endpoint_url=row["endpoint_url"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]

    return McpConfigurationListResponse(mcps=mcps, count=len(mcps))


async def create_mcp(
    db: aiosqlite.Connection,
    github_user_id: str,
    data: McpConfigurationCreate,
) -> McpConfigurationResponse:
    """Create a new MCP configuration for a user.

    Args:
        db: Database connection.
        github_user_id: The authenticated user's GitHub ID.
        data: MCP creation data (name, endpoint_url).

    Returns:
        The newly created McpConfigurationResponse.

    Raises:
        ValueError: If SSRF validation fails or user limit exceeded.
    """
    # Validate URL against SSRF
    try:
        validate_url_not_ssrf(data.endpoint_url)
    except ValueError as exc:
        raise McpValidationError(str(exc)) from exc

    # Check per-user limit
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM mcp_configurations WHERE github_user_id = ?",
        (github_user_id,),
    )
    row = await cursor.fetchone()
    if row and row["cnt"] >= MAX_MCPS_PER_USER:
        raise McpLimitExceededError(
            f"Maximum of {MAX_MCPS_PER_USER} MCP configurations per user reached"
        )

    now = utcnow().isoformat()
    mcp_id = str(uuid.uuid4())

    await db.execute(
        "INSERT INTO mcp_configurations (id, github_user_id, name, endpoint_url, is_active, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, 1, ?, ?)",
        (mcp_id, github_user_id, data.name, data.endpoint_url, now, now),
    )
    await db.commit()

    logger.info("Created MCP %s for user %s", mcp_id, github_user_id)

    return McpConfigurationResponse(
        id=mcp_id,
        name=data.name,
        endpoint_url=data.endpoint_url,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


async def delete_mcp(
    db: aiosqlite.Connection,
    github_user_id: str,
    mcp_id: str,
) -> bool:
    """Delete an MCP configuration owned by the user.

    Args:
        db: Database connection.
        github_user_id: The authenticated user's GitHub ID.
        mcp_id: The MCP configuration ID to delete.

    Returns:
        True if deleted, False if not found.
    """
    cursor = await db.execute(
        "DELETE FROM mcp_configurations WHERE id = ? AND github_user_id = ?",
        (mcp_id, github_user_id),
    )
    await db.commit()

    deleted = cursor.rowcount > 0
    if deleted:
        logger.info("Deleted MCP %s for user %s", mcp_id, github_user_id)
    else:
        logger.warning("MCP %s not found for user %s", mcp_id, github_user_id)

    return deleted
