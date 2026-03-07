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
    """Extract a per-user rate-limit key from the session cookie.

    Falls back to the remote IP address when no session cookie is present
    (e.g. unauthenticated OAuth callback requests).
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        return f"user:{session_id}"
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_key)
