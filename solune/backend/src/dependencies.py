"""FastAPI dependency-injection helpers.

Provide singleton services stored on ``app.state`` to endpoint handlers via
``Depends()``.  The lifespan in ``main.py`` is responsible for registering
instances on ``app.state`` at startup.

During the transition period, each getter falls back to the module-level
global when ``app.state`` has not yet been populated (e.g. in tests that
don't go through the full lifespan).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, Request

from src.exceptions import AppException, AuthorizationError
from src.logging_utils import get_logger

if TYPE_CHECKING:
    import aiosqlite

    from src.models.user import UserSession
    from src.services.github_projects import GitHubProjectsService
    from src.services.websocket import ConnectionManager

logger = get_logger(__name__)


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
    If no admin has been set yet (NULL) and ``ADMIN_GITHUB_USER_ID`` is
    configured, only the designated user is allowed and the DB is seeded.
    In debug mode without an explicit admin, the first user is
    auto-promoted. In production without an explicit admin, a 500 is
    raised.

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
        raise AppException(
            message="Server configuration error: admin settings are missing.",
            status_code=500,
        )

    admin_user_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]

    if admin_user_id is None:
        from src.config import get_settings

        settings = get_settings()
        if settings.admin_github_user_id:
            # Explicit admin designation via ADMIN_GITHUB_USER_ID env var
            if str(session.github_user_id) != str(settings.admin_github_user_id):
                raise AuthorizationError("Admin access required")
            # Set the configured user as admin in the database
            await db.execute(
                "UPDATE global_settings SET admin_github_user_id = ? WHERE id = 1",
                (settings.admin_github_user_id,),
            )
            await db.commit()
            logger.info(
                "Set configured admin user %s (%s) from ADMIN_GITHUB_USER_ID env var",
                session.github_username,
                session.github_user_id,
            )
            return session
        # No ADMIN_GITHUB_USER_ID configured
        if not settings.debug:
            # Production: refuse to auto-promote — config validator should
            # have caught this at startup, but defend in depth.
            raise AppException(
                message="ADMIN_GITHUB_USER_ID must be set in production mode.",
                status_code=500,
            )
        # Debug mode only: auto-promote first user
        logger.warning(
            "ADMIN_GITHUB_USER_ID not set — auto-promoting first user %s (%s). "
            "This is only allowed in debug mode.",
            session.github_username,
            session.github_user_id,
        )
        # Auto-promote first authenticated user atomically to prevent race conditions
        from src.services.chat_store import transaction

        async with transaction(db):
            cursor = await db.execute(
                "UPDATE global_settings SET admin_github_user_id = ? "
                "WHERE id = 1 AND admin_github_user_id IS NULL",
                (session.github_user_id,),
            )
            promoted = cursor.rowcount > 0

        if promoted:
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
            raise AppException(
                message="Server configuration error: admin settings are missing.",
                status_code=500,
            )
        admin_user_id = row["admin_github_user_id"] if isinstance(row, dict) else row[0]

    if str(session.github_user_id) != str(admin_user_id):
        raise AuthorizationError("Admin access required")

    return session


async def verify_project_access(
    request: Request,
    project_id: str,
    session: UserSession = Depends(_get_session_dep()),  # noqa: B008
) -> None:
    """Verify the authenticated user has access to *project_id*.

    Fetches the user's project list and confirms *project_id* is included.
    Raises HTTP 403 if the user does not own or have access to the project.
    """
    svc = get_github_service(request)
    try:
        projects = await svc.list_user_projects(session.access_token, session.github_username)
        if any(p.project_id == project_id for p in projects):
            return
    except Exception as e:
        logger.warning(
            "Failed to verify project access for user=%s project=%s: %s",
            session.github_username,
            project_id,
            e,
            exc_info=True,
        )
        raise AuthorizationError("Unable to verify project access") from None

    raise AuthorizationError("You do not have access to this project")


def require_selected_project(session: UserSession) -> str:
    """Return the selected project ID or raise :class:`ValidationError`.

    Use this in any endpoint that requires a project to be selected,
    instead of repeating inline ``if not session.selected_project_id``
    guards with inconsistent error messages.

    Returns:
        The non-empty ``selected_project_id`` string.

    Raises:
        src.exceptions.ValidationError: If no project is selected.
    """
    from src.exceptions import ValidationError

    if not session.selected_project_id:
        raise ValidationError("No project selected. Please select a project first.")
    return session.selected_project_id
