"""Factory for creating and pooling authenticated GitHub SDK clients."""

from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING

import httpx
from githubkit import GitHub, TokenAuthStrategy
from githubkit.throttling import LocalThrottler

from src.models.rate_limit import RateLimitState
from src.utils import BoundedDict

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class _RateLimitTransport(httpx.AsyncBaseTransport):
    """Async transport wrapper that captures rate limit headers."""

    def __init__(
        self,
        factory: GitHubClientFactory,
        *,
        verify: bool = True,
    ) -> None:
        self._factory = factory
        self._inner = httpx.AsyncHTTPTransport(verify=verify)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = await self._inner.handle_async_request(request)
        self._factory._capture_rate_limit(response)
        return response

    async def aclose(self) -> None:
        await self._inner.aclose()


class GitHubClientFactory:
    """Factory for creating and pooling authenticated GitHub SDK clients.

    Manages a bounded pool of GitHub client instances keyed by token hash.
    Provides rate limit visibility to consumers without exposing SDK internals.
    """

    def __init__(self, max_pool_size: int = 50) -> None:
        """Initialize the factory with a bounded client pool.

        Args:
            max_pool_size: Maximum number of pooled clients.  Oldest evicted
                when capacity is reached.  Default: 50.
        """
        self._pool: BoundedDict[str, GitHub] = BoundedDict(maxlen=max_pool_size)
        self._max_pool_size = max_pool_size
        self._rate_limit: RateLimitState | None = None

    # ------------------------------------------------------------------
    # Client management
    # ------------------------------------------------------------------

    def get_client(self, token: str) -> GitHub:
        """Get or create a pooled GitHub client for the given access token.

        If a client already exists for this token (matched by SHA-256 hash
        prefix), it is returned from the pool.  Otherwise a new client is
        created with built-in retry, HTTP caching, and throttling.
        """
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        existing = self._pool.get(token_hash)
        if existing is not None:
            return existing

        client = GitHub(
            TokenAuthStrategy(token),
            auto_retry=True,
            http_cache=True,
            throttler=LocalThrottler(100),
            async_transport=_RateLimitTransport(self),
        )
        self._pool[token_hash] = client
        return client

    # ------------------------------------------------------------------
    # Rate limit visibility
    # ------------------------------------------------------------------

    def _capture_rate_limit(self, response: httpx.Response) -> None:
        """Extract rate limit headers from an httpx response."""
        try:
            limit = response.headers.get("X-RateLimit-Limit")
            remaining = response.headers.get("X-RateLimit-Remaining")
            reset_at = response.headers.get("X-RateLimit-Reset")
            if limit and remaining and reset_at:
                self._rate_limit = RateLimitState(
                    limit=int(limit),
                    remaining=int(remaining),
                    reset_at=int(reset_at),
                    used=int(limit) - int(remaining),
                )
        except (ValueError, TypeError):
            pass

    def get_rate_limit(self) -> RateLimitState | None:
        """Return the most recent rate limit state from any API response.

        Returns ``None`` if no API calls have been made yet.
        """
        return self._rate_limit

    def clear_rate_limit(self) -> None:
        """Clear the cached rate limit state."""
        self._rate_limit = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close all pooled clients and release resources."""
        for client in list(self._pool.values()):
            try:
                await client.aclose()
            except Exception:  # noqa: BLE001
                logger.debug("Error closing pooled GitHub client", exc_info=True)
        self._pool.clear()
