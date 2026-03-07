"""Rate limiting middleware using slowapi.

Provides per-user and per-IP rate limiting for sensitive/expensive endpoints.
"""

from __future__ import annotations

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from src.constants import SESSION_COOKIE_NAME

logger = logging.getLogger(__name__)


def get_user_key(request: Request) -> str:
    """Extract a per-user rate-limit key from request context.

    Uses the session cookie value as a rate-limit identifier when present,
    and falls back to the remote IP address for unauthenticated requests
    (e.g. OAuth callback).
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
