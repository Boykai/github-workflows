"""Rate limiting middleware using slowapi.

Provides per-user and per-IP rate limiting for sensitive/expensive endpoints.
"""

from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from src.constants import SESSION_COOKIE_NAME
from src.logging_utils import get_logger

logger = get_logger(__name__)


def get_user_key(request: Request) -> str:
    """Extract a compound rate-limit key from request context.

    Priority order:
    1. ``github_user_id`` stored on ``request.state`` by middleware
       (resolves from session store — most reliable)
    2. Session cookie value as fallback (quick, no DB lookup)
    3. Remote IP address for unauthenticated requests

    The compound key prevents bypass via cookie clearing — authenticated
    users keep the same rate-limit bucket across sessions.
    """
    # Prefer github_user_id if resolved by middleware.
    github_user_id = getattr(request.state, "rate_limit_key", None)
    if github_user_id:
        return github_user_id

    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        return f"user:{session_id}"
    return f"ip:{get_remote_address(request)}"


def _is_rate_limiting_enabled() -> bool:
    """Check if rate limiting should be active.

    Disabled when the ``TESTING`` environment variable is set to avoid
    interfering with test suites.
    """
    import os

    if os.environ.get("TESTING"):
        return False
    return True


limiter = Limiter(
    key_func=get_user_key,
    enabled=_is_rate_limiting_enabled(),
)


class RateLimitKeyMiddleware:
    """Pre-resolve ``github_user_id`` for the rate-limit key.

    Sets ``request.state.rate_limit_key`` to ``user:{user_id}`` when
    the session cookie maps to a valid session, allowing the rate limiter
    to track users across sessions.  Falls back silently — the key_func
    will use the session cookie or IP.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request as _Request

        request = _Request(scope)
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if session_id:
            try:
                from src.services.database import get_db
                from src.services.session_store import get_session

                db = get_db()
                session = await get_session(db, session_id)
                if session and session.github_user_id:
                    request.state.rate_limit_key = f"user:{session.github_user_id}"
            except Exception:
                logger.debug("Rate limit key resolution failed", exc_info=True)

        await self.app(scope, receive, send)
