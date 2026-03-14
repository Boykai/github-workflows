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
    """Extract a rate-limit key from request context.

    Uses the session cookie value when present, falling back to the remote
    IP address for unauthenticated requests (e.g. OAuth callback).

    Note: this produces a **per-session** key, not per-user.  A single user
    with multiple sessions (different browsers/devices) accumulates separate
    quotas.  Switching to a per-*user* key (GitHub user ID) would require an
    async session-store lookup that slowapi's synchronous key_func cannot
    perform.  The practical risk is low: "bypassing" by creating a fresh
    session requires a full GitHub OAuth re-auth, and the auth endpoint
    itself is independently rate-limited by IP.
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        return f"user:{session_id}"
    return get_remote_address(request)


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
