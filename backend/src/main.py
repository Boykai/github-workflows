"""FastAPI application entry point."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings, setup_logging
from src.exceptions import AppException, RateLimitError

logger = logging.getLogger(__name__)


async def _auto_start_copilot_polling() -> None:
    """Resume Copilot polling after a restart using a persisted session.

    The copilot polling loop is an in-memory ``asyncio.Task`` that is
    normally started when a user selects a project in the UI.  After a
    container restart the task is lost.  This helper finds the most
    recently updated session that already has a ``selected_project_id``
    and automatically re-starts the polling loop so agent pipelines
    continue without manual intervention.
    """
    from src.services.copilot_polling import ensure_polling_started, get_polling_status
    from src.services.database import get_db
    from src.services.session_store import get_session
    from src.utils import resolve_repository

    db = get_db()

    # Find the most recently updated session with a selected project
    cursor = await db.execute(
        """
        SELECT session_id FROM user_sessions
        WHERE selected_project_id IS NOT NULL
        ORDER BY updated_at DESC
        LIMIT 1
        """,
    )
    row = await cursor.fetchone()
    if row is None:
        logger.info("No active session with a selected project — polling not auto-started")
        return

    session = await get_session(db, row["session_id"])
    if session is None or not session.selected_project_id:
        logger.info("Session expired or missing project — polling not auto-started")
        return

    status = get_polling_status()
    if status["is_running"]:
        return

    try:
        owner, repo = await resolve_repository(session.access_token, session.selected_project_id)
    except Exception:
        logger.warning(
            "Could not resolve repo for project %s — polling not auto-started",
            session.selected_project_id,
        )
        return

    started = await ensure_polling_started(
        access_token=session.access_token,
        project_id=session.selected_project_id,
        owner=owner,
        repo=repo,
        caller="lifespan_auto_start",
    )
    if started:
        logger.info(
            "Auto-started Copilot polling for project %s (%s/%s)",
            session.selected_project_id,
            owner,
            repo,
        )


async def _session_cleanup_loop() -> None:
    """Periodic background task to purge expired sessions.

    Uses exponential backoff on consecutive failures so transient DB
    errors don't spin-loop, while preserving the configured base
    interval on the success path.  The backoff cap is never lower than
    the base interval itself.
    """
    from src.services.database import get_db
    from src.services.session_store import purge_expired_sessions

    settings = get_settings()
    interval = settings.session_cleanup_interval
    consecutive_failures = 0

    while True:
        try:
            # On the success path keep the configured cadence; only apply
            # capped exponential backoff when there have been failures.
            if consecutive_failures == 0:
                sleep_time = interval
            else:
                backoff = interval * (2**consecutive_failures)
                cap = max(interval, 300)
                sleep_time = min(backoff, cap)

            await asyncio.sleep(sleep_time)
            db = get_db()
            count = await purge_expired_sessions(db)
            if count > 0:
                logger.info("Periodic cleanup: purged %d expired sessions", count)
            consecutive_failures = 0
        except asyncio.CancelledError:
            logger.debug("Session cleanup task cancelled")
            break
        except Exception:
            consecutive_failures += 1
            logger.exception(
                "Error in session cleanup task (consecutive_failures=%d)",
                consecutive_failures,
            )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler.

    The entire startup sequence is wrapped in ``try / finally`` so that
    resources are always cleaned up — even when a later startup step
    raises before ``yield``.  Each resource is guarded by a
    ``None``/flag check so cleanup only tears down what was actually
    initialised.
    """
    settings = get_settings()
    setup_logging(settings.debug)
    logger.info("Starting Agent Projects API")

    from src.services.database import close_database, init_database, seed_global_settings

    # Start Signal WebSocket listener for inbound messages
    from src.services.signal_bridge import start_signal_ws_listener, stop_signal_ws_listener

    # Track which resources were successfully initialised so the finally
    # block only tears down what actually started.
    db = None
    cleanup_task: asyncio.Task | None = None
    signal_started = False

    try:
        # Initialize SQLite database, run migrations, seed global settings
        db = await init_database()
        await seed_global_settings(db)
        _app.state.db = db

        # Initialize housekeeping seed templates
        from src.services.housekeeping.service import HousekeepingService

        housekeeping_svc = HousekeepingService(db)
        await housekeeping_svc.initialize()

        # Register singleton services on app.state for DI (see dependencies.py)
        from src.services.github_projects import github_projects_service
        from src.services.websocket import connection_manager

        _app.state.github_service = github_projects_service
        _app.state.connection_manager = connection_manager

        # Start periodic session cleanup
        cleanup_task = asyncio.create_task(_session_cleanup_loop())

        # Start Signal WebSocket listener for inbound messages
        await start_signal_ws_listener()
        signal_started = True

        # Auto-resume Copilot polling so agent pipelines survive restarts
        try:
            await _auto_start_copilot_polling()
        except Exception:
            logger.exception("Failed to auto-start Copilot polling (non-fatal)")

        yield
    finally:
        # Shutdown: stop Signal listener, cancel cleanup task, stop polling,
        # close database.  Guards ensure we only tear down resources that
        # were initialised.
        if signal_started:
            await stop_signal_ws_listener()
        if cleanup_task is not None:
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        # Stop Copilot polling if it was auto-started or started via the UI
        try:
            from src.services.copilot_polling import get_polling_status, stop_polling

            if get_polling_status()["is_running"]:
                stop_polling()
        except Exception:
            pass

        if db is not None:
            await close_database()
        logger.info("Shutting down Agent Projects API")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Agent Projects API",
        description="REST API for Agent Projects",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request-ID middleware (must be added after CORS — Starlette LIFO order)
    from src.middleware.request_id import RequestIDMiddleware

    app.add_middleware(RequestIDMiddleware)

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        headers: dict[str, str] = {}
        if isinstance(exc, RateLimitError):
            headers["Retry-After"] = str(exc.retry_after)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
            },
            headers=headers or None,
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Internal server error"},
        )

    # Include API routes (imported here to avoid circular import)
    from src.api import router as api_router

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
