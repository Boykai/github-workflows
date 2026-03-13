"""Factory for ``httpx.AsyncClient`` that propagates ``X-Request-ID``."""

from __future__ import annotations

import httpx

from src.middleware.request_id import request_id_var

_HEADER = "X-Request-ID"


async def _inject_request_id(request: httpx.Request) -> None:
    """Event hook that copies the current request-ID into outgoing headers."""
    rid = request_id_var.get("")
    if rid:
        request.headers[_HEADER] = rid


def create_client(**kwargs: object) -> httpx.AsyncClient:
    """Return an ``httpx.AsyncClient`` with ``X-Request-ID`` propagation.

    Any extra *kwargs* are forwarded to :class:`httpx.AsyncClient`.
    Drop-in replacement for ``httpx.AsyncClient(...)``.
    """
    hooks: dict = dict(kwargs.pop("event_hooks", {}) or {})  # type: ignore[arg-type]
    request_hooks: list = list(hooks.get("request") or [])
    request_hooks.insert(0, _inject_request_id)
    hooks["request"] = request_hooks
    return httpx.AsyncClient(event_hooks=hooks, **kwargs)  # type: ignore[arg-type]
