"""In-memory cache service with TTL."""

import hashlib
import json
from datetime import timedelta
from typing import Any

from src.config import get_settings
from src.logging_utils import get_logger
from src.utils import utcnow

logger = get_logger(__name__)


class CacheEntry[T]:
    """Cache entry with expiration and optional ETag support."""

    def __init__(
        self,
        value: T,
        ttl_seconds: int,
        etag: str | None = None,
        last_modified: str | None = None,
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
            self._cache.pop(key, None)
            logger.debug("Cache miss (expired): %s", key)
            return None

        logger.debug("Cache hit: %s", key)
        return entry.value

    def get_stale(self, key: str) -> Any | None:
        """
        Get cached value even when expired.

        Useful as a degraded-mode fallback when an upstream dependency
        (e.g. GitHub API) is temporarily unavailable or rate limited.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        entry = self._cache.get(key)
        if entry is None:
            return None
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

    def get_entry(self, key: str) -> CacheEntry[Any] | None:
        """
        Get the full cache entry (including ETag metadata).

        Args:
            key: Cache key

        Returns:
            CacheEntry or None if not found (does not check expiry)
        """
        return self._cache.get(key)

    def refresh_ttl(self, key: str, ttl_seconds: int | None = None) -> bool:
        """
        Refresh TTL of an existing cache entry without replacing the value.

        Args:
            key: Cache key
            ttl_seconds: New TTL in seconds (defaults to config value)

        Returns:
            True if entry existed and was refreshed
        """
        entry = self._cache.get(key)
        if entry is None:
            return False
        ttl = ttl_seconds or self._settings.cache_ttl_seconds
        entry.expires_at = utcnow() + timedelta(seconds=ttl)
        logger.debug("Cache TTL refreshed: %s (TTL: %ds)", key, ttl)
        return True

    def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed
        """
        if self._cache.pop(key, None) is not None:
            logger.debug("Cache delete: %s", key)
            return True
        return False

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        logger.debug("Cache cleared")

    def clear_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed
        """
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        removed = 0
        for key in expired_keys:
            # Use pop to avoid KeyError if another caller already removed it
            if self._cache.pop(key, None) is not None:
                removed += 1

        if removed:
            logger.debug("Cleared %d expired cache entries", removed)

        return removed


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


def get_sub_issues_cache_key(owner: str, repo: str, issue_number: int) -> str:
    """Get cache key for sub-issues of a specific issue."""
    from src.constants import CACHE_PREFIX_SUB_ISSUES

    return f"{CACHE_PREFIX_SUB_ISSUES}:{owner}/{repo}#{issue_number}"


def get_repo_agents_cache_key(owner: str, repo: str) -> str:
    """Get cache key for repo-backed agents from the default branch."""
    from src.constants import CACHE_PREFIX_REPO_AGENTS

    return get_cache_key(CACHE_PREFIX_REPO_AGENTS, f"{owner}/{repo}")


def compute_data_hash(data: Any) -> str:
    """Compute a stable SHA-256 hash of serializable data for change detection."""
    serialized = json.dumps(data, sort_keys=True, default=str).encode()
    return hashlib.sha256(serialized).hexdigest()
