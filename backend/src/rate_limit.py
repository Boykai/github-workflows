"""Shared rate limiter for sensitive API endpoints.

Uses :mod:`slowapi` with per-user key extraction (session cookie),
falling back to remote IP for unauthenticated requests.
"""

from __future__ import annotations

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.constants import SESSION_COOKIE_NAME


def _rate_limit_key(request: Request) -> str:
    """Extract per-user key from session cookie, fallback to IP."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        return session_id
    return get_remote_address(request)


limiter = Limiter(key_func=_rate_limit_key)


def _ip_key(request: Request) -> str:
    """Use remote IP as key (for unauthenticated endpoints like OAuth callback)."""
    return get_remote_address(request)
