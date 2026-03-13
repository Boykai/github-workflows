"""Frontend error reporting endpoint (FR-015).

Receives JavaScript errors from the frontend for server-side logging.
Fire-and-forget: logs at ERROR level, returns 204, no persistence.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, Field

from src.logging_utils import get_logger
from src.middleware.rate_limit import limiter

logger = get_logger(__name__)
router = APIRouter()

_MAX_MESSAGE = 2_000
_MAX_STACK = 10_000


class FrontendError(BaseModel):
    """Payload sent by the frontend error boundary."""

    message: str = Field(..., max_length=_MAX_MESSAGE)
    stack: str = Field("", max_length=_MAX_STACK)
    url: str = Field("", max_length=2_000)
    timestamp: str = Field("", max_length=40)
    user_agent: str = Field("", max_length=500)


@router.post("/errors", status_code=204, response_class=Response)
@limiter.limit("10/minute")
async def report_frontend_error(request: Request, payload: FrontendError) -> Response:
    """Log a frontend error and return 204 No Content."""
    logger.error(
        "Frontend error: %s | url=%s | ua=%s",
        payload.message,
        payload.url,
        payload.user_agent,
        extra={"stack": payload.stack, "timestamp": payload.timestamp},
    )
    return Response(status_code=204)
