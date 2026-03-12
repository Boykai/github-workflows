"""FastAPI application entry point."""

import asyncio
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings, setup_logging
from src.exceptions import AppException, RateLimitError
from src.logging_utils import get_logger
from src.middleware.request_id import request_id_var

logger = get_logger(__name__)


async def _auto_start_copilot_polling() -> bool:
    """Resume Copilot polling after a restart using a persisted session.

    The copilot polling loop is an in-memory ``asyncio.Task`` that is
    normally started when a user selects a project in the UI.  After a
    container restart the task is lost.  This helper finds the most
    recently updated session that already has a ``selected_project_id``
    and automatically re-starts the polling loop so agent pipelines
    continue without manual intervention.

    **Fallback (no sessions):** When no user sessions exist (e.g. fresh
    container, sessions expired), the system falls back to the
    ``GITHUB_WEBHOOK_TOKEN`` and discovers the ``project_id`` from the
    persisted ``project_settings`` table.  This ensures agent pipelines
    (including Copilot Review) keep running even without an active UI
    session.
    """
    from src.services.copilot_polling import ensure_polling_started, get_polling_status
    from src.services.database import get_db
    from src.services.session_store import get_session
    from src.utils import resolve_repository

    correlation_token = request_id_var.set(f"bg-copilot-{uuid.uuid4().hex[:8]}")
    try:
        polling_status = get_polling_status()
        if polling_status["is_running"]:
            return False

        db = get_db()

        # ── Strategy 1: Use a persisted user session ──
        cursor = await db.execute(
            """
            SELECT session_id FROM user_sessions
            WHERE selected_project_id IS NOT NULL
            ORDER BY updated_at DESC
            LIMIT 1
            """,
        )
        row = await cursor.fetchone()

        if row is not None:
            session = await get_session(db, row["session_id"])
            if session and session.selected_project_id:
                try:
                    owner, repo = await resolve_repository(
                        session.access_token, session.selected_project_id
                    )
                except Exception as e:
                    logger.warning(
                        "Could not resolve repo for project %s — trying webhook token fallback: %s",
                        session.selected_project_id,
                        e,
                    )
                else:
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
                    return started

        # ── Strategy 2: Webhook token + project_settings fallback ──
        # When no UI session exists, use GITHUB_WEBHOOK_TOKEN and discover
        # the project_id from the persisted workflow configuration.
        settings = get_settings()
        token = settings.github_webhook_token
        owner_name = settings.default_repo_owner
        repo_name = settings.default_repo_name

        if not token or not owner_name or not repo_name:
            logger.info(
                "No active session and no GITHUB_WEBHOOK_TOKEN/DEFAULT_REPOSITORY "
                "configured — polling not auto-started"
            )
            return False

        # Prefer explicit DEFAULT_PROJECT_ID if configured.
        project_id: str | None = settings.default_project_id

        if not project_id:
            # Find the most recently updated project_settings row whose
            # workflow_config contains the default repository name.
            import json

            cursor2 = await db.execute(
                """
                SELECT project_id, workflow_config FROM project_settings
                WHERE workflow_config IS NOT NULL
                ORDER BY updated_at DESC
                """,
            )
            owner_only_fallback: str | None = None
            for ps_row in await cursor2.fetchall():
                try:
                    wf = json.loads(ps_row["workflow_config"])
                    wf_repo = wf.get("repository_name", "")
                    wf_owner = wf.get("repository_owner", "")

                    # Exact match: both owner and repo name match
                    if wf_repo == repo_name and (not wf_owner or wf_owner == owner_name):
                        project_id = ps_row["project_id"]
                        break

                    # Owner-only match: repo name is empty/unset but owner matches.
                    # Use as fallback if no exact match is found.
                    if not wf_repo and wf_owner == owner_name and not owner_only_fallback:
                        owner_only_fallback = ps_row["project_id"]
                except (json.JSONDecodeError, TypeError):
                    continue

            if not project_id:
                project_id = owner_only_fallback

        if not project_id:
            logger.info(
                "No project_settings entry found for %s/%s — polling not auto-started",
                owner_name,
                repo_name,
            )
            return False

        started = await ensure_polling_started(
            access_token=token,
            project_id=project_id,
            owner=owner_name,
            repo=repo_name,
            caller="webhook_token_fallback",
        )
        if started:
            logger.info(
                "Auto-started Copilot polling via webhook token for project %s (%s/%s)",
                project_id,
                owner_name,
                repo_name,
            )
        return started
    finally:
        request_id_var.reset(correlation_token)


async def _startup_agent_mcp_sync(db: object) -> None:
    """Run agent MCP sync on startup to reconcile drift (FR-009).

    Uses the most recent user session to obtain credentials and project
    context.  If no session is available, the sync is silently skipped.
    """
    from src.services.agents.agent_mcp_sync import sync_agent_mcps
    from src.services.session_store import get_session
    from src.utils import resolve_repository

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
        logger.debug("No user session found — skipping startup agent MCP sync")
        return

    session = await get_session(db, row["session_id"])
    if not session or not session.selected_project_id:
        return

    try:
        owner, repo = await resolve_repository(session.access_token, session.selected_project_id)
    except Exception as e:
        logger.debug("Could not resolve repo for startup MCP sync: %s", e)
        return

    await sync_agent_mcps(
        owner=owner,
        repo=repo,
        project_id=session.selected_project_id,
        access_token=session.access_token,
        trigger="startup",
        db=db,
    )
    logger.info(
        "Startup agent MCP sync completed for %s/%s",
        owner,
        repo,
    )


async def _polling_watchdog_loop() -> None:
    """Watchdog task: restart the Copilot polling loop if it stops unexpectedly.

    Runs every 30 seconds and calls ``_auto_start_copilot_polling()`` whenever
    ``is_running`` is False.  This ensures the agent pipeline always recovers
    after crashes, task cancellations, or unexpected asyncio exits — without
    manual intervention.

    Uses a short fixed interval (30 s) so issues blocked by a stopped polling
    loop are unblocked within at most one minute.
    """
    from src.services.copilot_polling import get_polling_status

    consecutive_failures = 0

    while True:
        token = request_id_var.set(f"bg-polling-{uuid.uuid4().hex[:8]}")
        try:
            await asyncio.sleep(30)

            status = get_polling_status()
            if not status["is_running"]:
                logger.warning(
                    "Polling watchdog: polling loop is stopped "
                    "(errors=%d, last_error=%r) — attempting restart",
                    status.get("errors_count", 0),
                    status.get("last_error"),
                )
                try:
                    restarted = await _auto_start_copilot_polling()
                    if restarted:
                        logger.info("Polling watchdog: polling loop restarted successfully")
                    consecutive_failures = 0
                except Exception as e:
                    consecutive_failures += 1
                    logger.exception(
                        "Polling watchdog: restart attempt #%d failed: %s",
                        consecutive_failures,
                        e,
                    )
        except asyncio.CancelledError:
            logger.debug("Polling watchdog task cancelled")
            break
        except Exception as e:
            logger.exception("Unexpected error in polling watchdog: %s", e)
        finally:
            request_id_var.reset(token)


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
        token = request_id_var.set(f"bg-cleanup-{uuid.uuid4().hex[:8]}")
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
        except Exception as e:
            consecutive_failures += 1
            logger.exception(
                "Error in session cleanup task (consecutive_failures=%d): %s",
                consecutive_failures,
                e,
            )
        finally:
            request_id_var.reset(token)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan handler.

    The entire startup sequence is wrapped in ``try / finally`` so that
    resources are always cleaned up — even when a later startup step
    raises before ``yield``.  Each resource is guarded by a
    ``None``/flag check so cleanup only tears down what was actually
    initialised.
    """
    settings = get_settings()
    setup_logging(settings.debug, structured=not settings.debug)
    logger.info("Starting Agent Projects API")

    from src.services.database import close_database, init_database, seed_global_settings

    # Start Signal WebSocket listener for inbound messages
    from src.services.signal_bridge import start_signal_ws_listener, stop_signal_ws_listener

    # Track which resources were successfully initialised so the finally
    # block only tears down what actually started.
    db = None
    cleanup_task: asyncio.Task | None = None
    watchdog_task: asyncio.Task | None = None
    signal_started = False

    try:
        # Install a global asyncio exception handler so unhandled async
        # errors are logged with context instead of silently swallowed.
        loop = asyncio.get_running_loop()

        def _asyncio_exception_handler(_loop: asyncio.AbstractEventLoop, context: dict) -> None:
            exc = context.get("exception")
            msg = context.get("message", "Unhandled async exception")
            logger.error(
                "Async exception: %s — %s",
                msg,
                exc,
                exc_info=(
                    (type(exc), exc, getattr(exc, "__traceback__", None))
                    if exc is not None
                    else None
                ),
            )

        loop.set_exception_handler(_asyncio_exception_handler)

        # Initialize SQLite database, run migrations, seed global settings
        db = await init_database()
        await seed_global_settings(db)
        _app.state.db = db

        # Load persisted pipeline state from SQLite into L1 caches
        from src.services.pipeline_state_store import init_pipeline_state_store

        await init_pipeline_state_store(db)

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
        except Exception as e:
            logger.exception("Failed to auto-start Copilot polling (non-fatal): %s", e)

        # Agent MCP sync on startup — reconcile any drift between Tools page
        # state and agent files (FR-009).  Uses the most recent user session.
        # Run as a background task so it does not block app startup.
        async def _run_startup_agent_mcp_sync_background() -> None:
            try:
                await _startup_agent_mcp_sync(db)
            except Exception as e:
                logger.warning("Startup agent MCP sync failed (non-fatal): %s", e)

        asyncio.create_task(_run_startup_agent_mcp_sync_background())

        # Start polling watchdog — restarts polling if it stops unexpectedly.
        # This is the primary guarantee that the agent pipeline "always recovers".
        watchdog_task = asyncio.create_task(_polling_watchdog_loop())

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

        if watchdog_task is not None:
            watchdog_task.cancel()
            try:
                await watchdog_task
            except asyncio.CancelledError:
                pass

        # Stop Copilot polling if it was auto-started or started via the UI
        try:
            from src.services.copilot_polling import get_polling_status, stop_polling

            if get_polling_status()["is_running"]:
                stop_polling()
        except Exception as e:
            logger.warning("Error stopping Copilot polling during shutdown: %s", e, exc_info=True)

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
        docs_url="/api/docs" if settings.enable_docs else None,
        redoc_url="/api/redoc" if settings.enable_docs else None,
    )

    # CORS middleware — explicit methods and headers reduce attack surface.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "X-Request-ID",
            "X-Requested-With",
        ],
    )

    # Request-ID middleware (must be added after CORS — Starlette LIFO order)
    from src.middleware.request_id import RequestIDMiddleware

    app.add_middleware(RequestIDMiddleware)

    # Content Security Policy middleware
    from src.middleware.csp import CSPMiddleware

    app.add_middleware(CSPMiddleware)

    # Rate limiting — slowapi state + exception handler
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded

    from src.middleware.rate_limit import limiter

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

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
        from src.middleware.request_id import request_id_var

        rid = request_id_var.get("")
        logger.exception(
            "Unhandled exception: %s | request_id=%s method=%s path=%s",
            type(exc).__name__,
            rid,
            _request.method,
            _request.url.path,
        )
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
