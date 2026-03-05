"""FastAPI dependency-injection helpers.

Provide singleton services stored on ``app.state`` to endpoint handlers via
``Depends()``.  The lifespan in ``main.py`` is responsible for registering
instances on ``app.state`` at startup.

All service access goes through ``app.state`` exclusively — there are no
module-global fallback variables.  This ensures clean test isolation via
``TestClient`` with custom ``app.state`` overrides.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status

if TYPE_CHECKING:
    import aiosqlite

    from src.models.user import UserSession
    from src.services.github_projects import GitHubProjectsService
    from src.services.websocket import ConnectionManager

logger = logging.getLogger(__name__)


def get_github_service(request: Request) -> GitHubProjectsService:
    """Return the singleton :class:`GitHubProjectsService`."""
    svc = getattr(request.app.state, "github_service", None)
    if svc is not None:
        return svc
    raise RuntimeError(
        "GitHubProjectsService not registered on app.state. "
        "In tests, register via app.state overrides or use the full application lifespan."
    )


def get_connection_manager(request: Request) -> ConnectionManager:
    """Return the singleton :class:`ConnectionManager`."""
    mgr = getattr(request.app.state, "connection_manager", None)
    if mgr is not None:
        return mgr
    raise RuntimeError(
        "ConnectionManager not registered on app.state. "
        "In tests, register via app.state overrides or use the full application lifespan."
    )


def get_database(request: Request) -> aiosqlite.Connection:
    """Return the application database connection."""
    db = getattr(request.app.state, "db", None)
    if db is not None:
        return db
    raise RuntimeError(
        "Database not registered on app.state. "
        "In tests, register via app.state overrides or use the full application lifespan."
    )


def _get_session_dep():
    """Lazy import to avoid circular imports with api.auth at module level."""
    from src.api.auth import get_session_dep

    return get_session_dep


async def require_admin(
    request: Request,
    session=Depends(_get_session_dep()),  # noqa: B008
) -> UserSession:
    """Verify the current session belongs to the admin user.

    Checks ``session.github_user_id`` against the
    ``admin_github_user_id`` column in ``global_settings``.
    If no admin has been set yet (NULL), the first authenticated user is
    auto-promoted and persisted.

    Returns the session if authorized; raises *403* otherwise.
    """
    db = get_database(request)
    cursor = await db.execute("SELECT admin_github_user_id FROM global_settings WHERE id = 1")
    row = await cursor.fetchone()

    if row is None:
        # The global_settings singleton row is missing; this is a server
        # misconfiguration — seed_global_settings() should have created it.
        logger.error(
            "global_settings row with id=1 is missing when verifying admin user "
            "(GitHub user id: %s)",
            session.github_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: admin settings are missing.",
        )

    admin_user_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]

    if admin_user_id is None:
        # Auto-promote first authenticated user atomically to prevent race conditions
        cursor = await db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1 AND admin_github_user_id IS NULL",
            (session.github_user_id,),
        )
        await db.commit()
        if cursor.rowcount > 0:
            logger.info(
                "Auto-promoted user %s (%s) as admin",
                session.github_username,
                session.github_user_id,
            )
            return session
        # Another user was promoted concurrently — re-read to check
        cursor = await db.execute("SELECT admin_github_user_id FROM global_settings WHERE id = 1")
        row = await cursor.fetchone()
        if row is None:
            # The global_settings singleton row is missing — this should
            # never happen since we just read it above.  Surface a clear
            # 500 rather than an opaque AttributeError.
            logger.error(
                "global_settings row with id=1 is missing when verifying "
                "admin user (GitHub user id: %s)",
                session.github_user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error: admin settings are missing.",
            )
        admin_user_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]

    if session.github_user_id != admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the session owner can modify settings",
        )

    return session
