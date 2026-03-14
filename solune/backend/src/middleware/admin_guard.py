"""Admin guard middleware — intercepts file operations and blocks access to protected paths.

Evaluates each target file path before allowing file system access.
Returns 403 with explanation for blocked/locked paths.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.logging_utils import get_logger
from src.services.guard_service import check_guard

logger = get_logger(__name__)


class AdminGuardMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces guard rules on agent file operations.

    Only applies to requests that include a ``X-Target-Paths`` header
    (comma-separated list of file paths the operation targets).
    Normal API requests pass through unchanged.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        target_paths_header = request.headers.get("X-Target-Paths")
        if not target_paths_header:
            return await call_next(request)

        file_paths = [p.strip() for p in target_paths_header.split(",") if p.strip()]
        if not file_paths:
            return await call_next(request)

        elevated = request.headers.get("X-Guard-Elevated", "").lower() == "true"
        result = check_guard(file_paths, elevated=elevated)

        if result.locked:
            logger.warning(
                "Guard BLOCKED (adminlock): %s paths locked",
                len(result.locked),
            )
            return Response(
                content=(
                    f"Access denied: {len(result.locked)} path(s) are permanently locked "
                    f"(@adminlock). Locked paths: {', '.join(result.locked)}"
                ),
                status_code=403,
                media_type="text/plain",
            )

        if result.admin_blocked:
            logger.warning(
                "Guard BLOCKED (admin): %s paths require elevation",
                len(result.admin_blocked),
            )
            return Response(
                content=(
                    f"Access denied: {len(result.admin_blocked)} path(s) require elevated "
                    f"permissions (@admin). Blocked paths: {', '.join(result.admin_blocked)}. "
                    "Set X-Guard-Elevated: true to override."
                ),
                status_code=403,
                media_type="text/plain",
            )

        return await call_next(request)
