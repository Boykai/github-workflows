"""ASGI middleware that assigns or propagates ``X-Request-ID`` per request.

The generated/propagated request ID is stored in a :class:`~contextvars.ContextVar`
so that any async handler or service can access it for logging or error
correlation without threading it through function arguments.

Usage in ``main.py``::

    from src.middleware.request_id import RequestIDMiddleware
    app.add_middleware(RequestIDMiddleware)

Reading the current request ID from anywhere::

    from src.middleware.request_id import request_id_var
    rid = request_id_var.get("")
"""

from __future__ import annotations

import contextvars
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

#: ContextVar holding the current request's correlation ID.
#: Defaults to ``""`` outside a request context.
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that propagates or generates ``X-Request-ID``.

    * If the incoming request contains an ``X-Request-ID`` header its value is
      reused (propagation).
    * Otherwise a new ``uuid4().hex`` value is generated.
    * The value is stored in :data:`request_id_var` for the duration of the
      request and added to the *response* headers.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = request.headers.get(_HEADER) or uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
            response.headers[_HEADER] = rid
            return response
        finally:
            request_id_var.reset(token)
