"""FastAPI application entry point."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings, setup_logging
from src.exceptions import AppException

logger = logging.getLogger(__name__)


async def _session_cleanup_loop() -> None:
    """Periodic background task to purge expired sessions."""
    from src.services.database import get_db
    from src.services.session_store import purge_expired_sessions

    settings = get_settings()
    interval = settings.session_cleanup_interval

    while True:
        try:
            await asyncio.sleep(interval)
            db = get_db()
            count = await purge_expired_sessions(db)
            if count > 0:
                logger.info("Periodic cleanup: purged %d expired sessions", count)
        except asyncio.CancelledError:
            logger.debug("Session cleanup task cancelled")
            break
        except Exception:
            logger.exception("Error in session cleanup task")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    setup_logging(settings.debug)
    logger.info("Starting Agent Projects API")

    # Initialize SQLite database, run migrations, seed global settings
    from src.services.database import close_database, init_database, seed_global_settings

    db = await init_database()
    await seed_global_settings(db)
    _app.state.db = db

    # Register singleton services on app.state for DI (see dependencies.py)
    from src.services.github_projects import github_projects_service
    from src.services.websocket import connection_manager

    _app.state.github_service = github_projects_service
    _app.state.connection_manager = connection_manager

    # Start periodic session cleanup
    cleanup_task = asyncio.create_task(_session_cleanup_loop())

    yield

    # Shutdown: cancel cleanup task, close database
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
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

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "details": exc.details,
            },
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
