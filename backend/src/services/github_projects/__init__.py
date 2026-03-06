"""GitHub Projects V2 GraphQL service."""

import asyncio
import hashlib
import logging

from githubkit import GitHub, TokenAuthStrategy
from githubkit.retry import RETRY_RATE_LIMIT, RETRY_SERVER_ERROR, RetryChainDecision
from githubkit.throttling import LocalThrottler

from src.utils import BoundedDict

logger = logging.getLogger(__name__)


class GitHubClientFactory:
    """Creates and pools authenticated githubkit client instances."""

    def __init__(self, max_pool_size: int = 50) -> None:
        self._pool: BoundedDict[str, GitHub] = BoundedDict(maxlen=max_pool_size)
        self._auto_retry = RetryChainDecision(RETRY_RATE_LIMIT, RETRY_SERVER_ERROR)
        self._lock = asyncio.Lock()

    async def get_client(self, access_token: str) -> GitHub:
        """Return a pooled or newly created client for the given token."""
        key = hashlib.sha256(access_token.encode()).hexdigest()[:16]
        client = self._pool.get(key)
        if client is not None:
            return client
        async with self._lock:
            # Double-check after acquiring lock
            client = self._pool.get(key)
            if client is None:
                client = GitHub(
                    TokenAuthStrategy(access_token),
                    auto_retry=self._auto_retry,
                    http_cache=True,
                    throttler=LocalThrottler(100),
                    timeout=30.0,
                )
                self._pool[key] = client
        return client

    async def close_all(self) -> None:
        """Close all pooled clients. Called on application shutdown."""
        for client in self._pool.values():
            try:
                await client.__aexit__(None, None, None)
            except Exception:
                pass
        self._pool.clear()


from src.services.github_projects.service import (  # noqa: E402, F401
    GitHubProjectsService,
    github_projects_service,
)

__all__ = [
    "GitHubClientFactory",
    "GitHubProjectsService",
    "github_projects_service",
]
