"""Rate-limit tracking for GitHub API requests.

Encapsulates the extraction and storage of rate-limit headers from REST
and GraphQL responses.  Both a per-request context-var and a service-level
fallback are maintained so that callers outside an async request scope
(background tasks, polling loops) still get useful data.
"""

from __future__ import annotations

import contextvars
from typing import Any

from src.logging_utils import get_logger

logger = get_logger(__name__)

# Request-scoped storage for rate limit info.
_request_rate_limit: contextvars.ContextVar[dict[str, int] | None] = contextvars.ContextVar(
    "_request_rate_limit", default=None
)


class RateLimitManager:
    """Track and expose GitHub API rate-limit information.

    Extracts ``X-RateLimit-*`` headers from every REST response and makes
    the parsed values available to the polling loop, middleware, and API
    routes.

    Two storage layers are maintained:

    * A :class:`contextvars.ContextVar` that is scoped to the current
      async request — safe under concurrency.
    * An instance-level dict that serves as a fallback for callers
      outside an async request context (background tasks, CLI).

    .. note::
        This class is designed for single-threaded async (``asyncio``)
        usage.  The instance-level ``_last_rate_limit`` is a best-effort
        fallback and is not protected by a lock — safe in asyncio where
        coroutines yield cooperatively, but not suitable for multi-threaded
        environments.
    """

    def __init__(self) -> None:
        self._last_rate_limit: dict[str, int] | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_from_headers(self, headers: Any) -> dict[str, int] | None:
        """Parse rate-limit values from response headers.

        Args:
            headers: An object supporting ``.get(key)`` — typically an
                httpx or githubkit response headers mapping.

        Returns:
            A dict with ``limit``, ``remaining``, ``reset_at``, and
            ``used`` keys, or *None* if the headers do not contain
            valid rate-limit information.
        """
        try:
            limit = headers.get("X-RateLimit-Limit")
            remaining = headers.get("X-RateLimit-Remaining")
            reset_at = headers.get("X-RateLimit-Reset")
            if limit is not None and remaining is not None and reset_at is not None:
                info: dict[str, int] = {
                    "limit": int(limit),
                    "remaining": int(remaining),
                    "reset_at": int(reset_at),
                    "used": int(limit) - int(remaining),
                }
                _request_rate_limit.set(info)
                self._last_rate_limit = info
                return info
        except (ValueError, TypeError):
            pass
        return None

    def get(self) -> dict[str, int] | None:
        """Return the most recent rate-limit info.

        Prefers the request-scoped context var (safe under concurrency),
        falling back to the instance-level value for callers outside an
        async request context.
        """
        return _request_rate_limit.get() or self._last_rate_limit

    def clear(self) -> None:
        """Clear both the request-scoped contextvar and instance-level caches.

        Called by the polling loop when stale rate-limit data is detected
        (e.g. the reset window has already passed but the cached remaining
        count is still zero).
        """
        _request_rate_limit.set(None)
        self._last_rate_limit = None
