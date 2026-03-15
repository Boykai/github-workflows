"""Protocol types for service interfaces.

Protocols allow type-safe dependency injection and easier testing without
tight coupling to concrete implementations.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelProvider(Protocol):
    """Interface for AI model providers (Copilot, Azure OpenAI, etc.)."""

    async def fetch_models(self, token: str | None) -> list[Any]:
        """Return available models for this provider."""
        ...


@runtime_checkable
class CacheInvalidationPolicy(Protocol):
    """Interface for cache invalidation strategies."""

    def should_invalidate(self, key: str, age_seconds: float) -> bool:
        """Return True if the cache entry should be invalidated."""
        ...

    def on_write(self, key: str) -> None:
        """Called after a write operation that may affect cached data."""
        ...
