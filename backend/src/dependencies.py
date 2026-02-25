"""FastAPI dependency-injection helpers.

Provide singleton services stored on ``app.state`` to endpoint handlers via
``Depends()``.  The lifespan in ``main.py`` is responsible for registering
instances on ``app.state`` at startup.

During the transition period, each getter falls back to the module-level
global when ``app.state`` has not yet been populated (e.g. in tests that
don't go through the full lifespan).
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
    # Fallback to module-level global during transition
    from src.services.github_projects import github_projects_service

    return github_projects_service


def get_connection_manager(request: Request) -> ConnectionManager:
    """Return the singleton :class:`ConnectionManager`."""
    mgr = getattr(request.app.state, "connection_manager", None)
    if mgr is not None:
        return mgr
    from src.services.websocket import connection_manager

    return connection_manager


def get_database(request: Request) -> aiosqlite.Connection:
    """Return the application database connection."""
    db = getattr(request.app.state, "db", None)
    if db is not None:
        return db
    from src.services.database import get_db

    return get_db()


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
        admin_user_id = None
    else:
        admin_user_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]

    if admin_user_id is None:
        # Auto-promote first authenticated user
        await db.execute(
            "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
            (session.github_user_id,),
        )
        await db.commit()
        logger.info(
            "Auto-promoted user %s (%s) as admin",
            session.github_username,
            session.github_user_id,
        )
        return session

    if session.github_user_id != admin_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the session owner can modify settings",
        )

    return session
