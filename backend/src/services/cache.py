"""In-memory cache service with TTL."""

import logging
from datetime import timedelta
from typing import Any, Generic, TypeVar

from src.config import get_settings
from src.utils import utcnow

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheEntry(Generic[T]):
    """Cache entry with expiration and optional ETag support."""

    def __init__(
        self, value: T, ttl_seconds: int, etag: str | None = None, last_modified: str | None = None
    ):
        self.value = value
        self.expires_at = utcnow() + timedelta(seconds=ttl_seconds)
        self.etag = etag
        self.last_modified = last_modified

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        return utcnow() > self.expires_at


class InMemoryCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: dict[str, CacheEntry[Any]] = {}
        self._settings = get_settings()

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if entry.is_expired:
            del self._cache[key]
            logger.debug("Cache miss (expired): %s", key)
            return None

        logger.debug("Cache hit: %s", key)
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (defaults to config value)
            etag: Optional ETag from API response
            last_modified: Optional Last-Modified header from API response
        """
        ttl = ttl_seconds or self._settings.cache_ttl_seconds
        self._cache[key] = CacheEntry(value, ttl, etag=etag, last_modified=last_modified)
        logger.debug("Cache set: %s (TTL: %ds)", key, ttl)

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug("Cache delete: %s", key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.debug("Cache cleared")


# Global cache instance
cache = InMemoryCache()


# Convenience functions for project caching
def get_cache_key(prefix: str, identifier: str) -> str:
    """Generate a cache key with consistent format."""
    return f"{prefix}:{identifier}"


def get_user_projects_cache_key(user_id: str) -> str:
    """Get cache key for user's projects list."""
    from src.constants import CACHE_PREFIX_PROJECTS

    return get_cache_key(CACHE_PREFIX_PROJECTS, user_id)


def get_project_items_cache_key(project_id: str) -> str:
    """Get cache key for project items."""
    from src.constants import CACHE_PREFIX_PROJECT_ITEMS

    return get_cache_key(CACHE_PREFIX_PROJECT_ITEMS, project_id)
