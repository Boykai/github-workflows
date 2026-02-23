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

from fastapi import Request

if TYPE_CHECKING:
    import aiosqlite

    from src.services.github_projects import GitHubProjectsService
    from src.services.websocket import ConnectionManager


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
