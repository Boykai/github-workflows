"""FastAPI application entry point."""

import logging
import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import get_settings, setup_logging
from src.exceptions import AppException

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter for GitHub API calls."""

    def __init__(self, max_requests: int = 4000, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {session_id: [(timestamp, count)]}
        self._requests: dict[str, list[tuple[float, int]]] = defaultdict(list)
        # Track GitHub API remaining limit per session
        self._github_remaining: dict[str, int] = {}

    def check_limit(self, session_id: str) -> tuple[bool, int]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old entries
        self._requests[session_id] = [
            (ts, count) for ts, count in self._requests[session_id] if ts > window_start
        ]

        # Count requests in window
        total = sum(count for _, count in self._requests[session_id])

        if total >= self.max_requests:
            return False, 0

        return True, self.max_requests - total

    def record_request(self, session_id: str, count: int = 1) -> None:
        """Record a request for rate limiting."""
        self._requests[session_id].append((time.time(), count))

    def update_github_remaining(self, session_id: str, remaining: int) -> None:
        """Update GitHub API remaining limit from response headers."""
        self._github_remaining[session_id] = remaining

    def get_github_remaining(self, session_id: str) -> int | None:
        """Get last known GitHub API remaining limit."""
        return self._github_remaining.get(session_id)


# Global rate limiter instance
rate_limiter = RateLimiter()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    settings = get_settings()
    setup_logging(settings.debug)
    logger.info("Starting Agent Projects API")
    yield
    logger.info("Shutting down Agent Projects API")
    # Clean up CopilotCompletionProvider cached clients to avoid resource leaks
    try:
        from src.services.ai_agent import _ai_agent_service_instance

        if _ai_agent_service_instance is not None:
            provider = _ai_agent_service_instance._provider
            if hasattr(provider, "cleanup"):
                await provider.cleanup()
                logger.info("Cleaned up AI completion provider")
    except Exception as e:
        logger.warning("Error during completion provider cleanup: %s", e)


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
