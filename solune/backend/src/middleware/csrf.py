"""CSRF protection middleware — double-submit cookie pattern.

State-changing requests (POST, PUT, PATCH, DELETE) must include an
``X-CSRF-Token`` header whose value matches the ``csrf_token`` cookie.
GET/HEAD/OPTIONS and webhook/OAuth callback paths are exempt.
"""

from __future__ import annotations

import secrets

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.logging_utils import get_logger

logger = get_logger(__name__)

# Paths exempt from CSRF validation (webhooks, OAuth callback).
_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/api/v1/auth/github/callback",
    "/api/v1/webhooks/",
)

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_CSRF_COOKIE = "csrf_token"
_CSRF_HEADER = "x-csrf-token"


class CSRFMiddleware(BaseHTTPMiddleware):
    """Double-submit cookie CSRF protection.

    Disabled when the ``TESTING`` environment variable is set.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        import os

        if os.environ.get("TESTING"):
            return await call_next(request)

        # Ensure every response has a CSRF cookie.
        csrf_cookie = request.cookies.get(_CSRF_COOKIE)
        if not csrf_cookie:
            csrf_cookie = secrets.token_hex(32)

        # Validate state-changing requests.
        if request.method not in _SAFE_METHODS and not self._is_exempt(request.url.path):
            header_token = request.headers.get(_CSRF_HEADER, "")
            if not header_token or not secrets.compare_digest(header_token, csrf_cookie):
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid"},
                )

        response = await call_next(request)

        # Set / refresh the cookie so the client always has a token.
        from src.config import get_settings

        settings = get_settings()
        response.set_cookie(
            key=_CSRF_COOKIE,
            value=csrf_cookie,
            httponly=False,  # Must be readable by JS
            samesite="lax",
            secure=settings.effective_cookie_secure,
            max_age=settings.cookie_max_age,
            path="/",
        )
        return response

    @staticmethod
    def _is_exempt(path: str) -> bool:
        return any(path.startswith(p) for p in _EXEMPT_PREFIXES)
