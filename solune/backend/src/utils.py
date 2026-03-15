"""Shared utility functions for the backend application."""

from __future__ import annotations

import hashlib
from collections import OrderedDict
from collections.abc import Awaitable, Callable, ItemsView, Iterator, KeysView, ValuesView
from datetime import UTC, datetime
from typing import TypeVar, overload

from src.logging_utils import get_logger

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

logger = get_logger(__name__)


class BoundedSet[T]:
    """Set with a maximum capacity that evicts oldest entries (FIFO).

    Backed by an ``OrderedDict`` to maintain insertion order. When the
    capacity is reached, the oldest entries are evicted automatically.
    """

    def __init__(self, maxlen: int) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be > 0")
        self._maxlen = maxlen
        self._data: OrderedDict[T, None] = OrderedDict()

    @property
    def maxlen(self) -> int:
        """Maximum capacity."""
        return self._maxlen

    # --- set-like interface ---------------------------------------------------

    def add(self, item: T) -> None:
        """Add *item*, evicting the oldest entry if at capacity."""
        if item in self._data:
            self._data.move_to_end(item)
            return
        if len(self._data) >= self._maxlen:
            self._data.popitem(last=False)
        self._data[item] = None

    def discard(self, item: T) -> None:
        self._data.pop(item, None)

    def __contains__(self, item: object) -> bool:
        return item in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[T]:
        return iter(self._data)

    def clear(self) -> None:
        self._data.clear()

    def __repr__(self) -> str:
        return f"BoundedSet(maxlen={self._maxlen}, size={len(self._data)})"


class BoundedDict[K, V]:
    """Dict with a maximum capacity that evicts oldest entries (FIFO).

    Backed by an ``OrderedDict`` to maintain insertion order.

    An optional *on_evict* callback is called with ``(key, value)`` just
    before an entry is evicted to make room for a new one.
    """

    def __init__(
        self,
        maxlen: int,
        on_evict: Callable[[K, V], object] | None = None,
    ) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be > 0")
        self._maxlen = maxlen
        self._data: OrderedDict[K, V] = OrderedDict()
        self._on_evict = on_evict

    @property
    def maxlen(self) -> int:
        """Maximum capacity."""
        return self._maxlen

    def __setitem__(self, key: K, value: V) -> None:
        if key in self._data:
            self._data.move_to_end(key)
            self._data[key] = value
            return
        if len(self._data) >= self._maxlen:
            evicted_key, evicted_value = self._data.popitem(last=False)
            if self._on_evict is not None:
                try:
                    self._on_evict(evicted_key, evicted_value)
                except Exception:
                    pass
        self._data[key] = value

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __delitem__(self, key: K) -> None:
        del self._data[key]

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator[K]:
        return iter(self._data)

    @overload
    def get(self, key: K) -> V | None: ...
    @overload
    def get(self, key: K, default: V) -> V: ...
    def get(self, key: K, default: V | None = None) -> V | None:
        return self._data.get(key, default)

    @overload
    def pop(self, key: K) -> V: ...
    @overload
    def pop(self, key: K, default: V) -> V: ...
    @overload
    def pop(self, key: K, default: None) -> V | None: ...
    def pop(self, key: K, *args: object) -> V | None:  # type: ignore[misc]
        return self._data.pop(key, *args)  # type: ignore[arg-type]

    def keys(self) -> KeysView[K]:
        return self._data.keys()

    def values(self) -> ValuesView[V]:
        return self._data.values()

    def items(self) -> ItemsView[K, V]:
        return self._data.items()

    def clear(self) -> None:
        self._data.clear()

    def __repr__(self) -> str:
        return f"BoundedDict(maxlen={self._maxlen}, size={len(self._data)})"


def utcnow() -> datetime:
    """Return the current UTC time as a timezone-aware datetime.

    Single chokepoint replacing deprecated ``datetime.utcnow()`` calls.
    Returns an aware datetime with ``tzinfo=UTC``.
    """
    return datetime.now(UTC)


async def resolve_repository(access_token: str, project_id: str) -> tuple[str, str]:
    """Resolve repository owner and name for a project using 3-step fallback.

    Results are cached in the global cache to avoid redundant GitHub API
    calls when multiple handlers in the same request (or closely-spaced
    requests) resolve the same project.

    Lookup order:
    1. In-memory cache (short TTL)
    2. Project items (via GitHub Projects GraphQL API)
    3. Workflow configuration (in-memory/DB)
    4. Default repository from app settings (.env)

    Args:
        access_token: GitHub access token.
        project_id: GitHub Project node ID.

    Returns:
        ``(owner, repo_name)`` tuple.

    Raises:
        src.exceptions.ValidationError: If no repository can be resolved.
    """
    from src.exceptions import ValidationError
    from src.services.cache import cache
    from src.services.github_projects import github_projects_service
    from src.services.workflow_orchestrator import get_workflow_config

    # Check cache first to avoid repeated API calls for the same project.
    # Include a hash of the access token so cached results are scoped to the
    # caller — prevents a user without project access from reading a cache
    # entry populated by another user.
    token_hash = hashlib.sha256(access_token.encode()).hexdigest()[:16]
    cache_key = f"resolve_repo:{token_hash}:{project_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # 1. Try project items
    repo_info = await github_projects_service.get_project_repository(access_token, project_id)
    if repo_info:
        cache.set(cache_key, repo_info, ttl_seconds=300)
        return repo_info

    # 2. Try workflow config
    config = await get_workflow_config(project_id)
    if config and config.repository_owner and config.repository_name:
        result = (config.repository_owner, config.repository_name)
        cache.set(cache_key, result, ttl_seconds=300)
        return result

    # 3. Fall back to default repository from settings
    from src.config import get_settings

    settings = get_settings()
    if settings.default_repo_owner and settings.default_repo_name:
        result = (settings.default_repo_owner, settings.default_repo_name)
        cache.set(cache_key, result, ttl_seconds=300)
        return result

    raise ValidationError(
        "No repository found for this project. Configure DEFAULT_REPOSITORY in .env "
        "or ensure the project has at least one linked issue."
    )


async def cached_fetch[R](
    cache_key: str,
    fetch_fn: Callable[..., Awaitable[R]],
    *args: object,
    refresh: bool = False,
) -> R:
    """Check cache, call *fetch_fn* on miss, and store the result.

    This is the canonical cache-or-fetch pattern used by API endpoints that
    back GitHub data with an in-memory cache.

    Args:
        cache_key: Cache key to check / store under.
        fetch_fn: Async callable that produces the value on cache miss.
        *args: Positional arguments forwarded to *fetch_fn*.
        refresh: When ``True`` the cache is bypassed and *fetch_fn* is
            always called.

    Returns:
        The cached or freshly fetched value.
    """
    from src.services.cache import cache

    if not refresh:
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug("Cache hit for %s", cache_key)
            return cached  # type: ignore[return-value]

    result = await fetch_fn(*args)
    cache.set(cache_key, result)
    logger.debug("Cache set for %s", cache_key)
    return result
