"""Shared utility functions for the backend application."""

from __future__ import annotations

from collections import OrderedDict
from collections.abc import ItemsView, Iterator, KeysView, ValuesView
from datetime import UTC, datetime
from typing import Generic, TypeVar, overload

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


class BoundedSet(Generic[T]):
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


class BoundedDict(Generic[K, V]):
    """Dict with a maximum capacity that evicts oldest entries (FIFO).

    Backed by an ``OrderedDict`` to maintain insertion order.
    """

    def __init__(self, maxlen: int) -> None:
        if maxlen <= 0:
            raise ValueError("maxlen must be > 0")
        self._maxlen = maxlen
        self._data: OrderedDict[K, V] = OrderedDict()

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
            self._data.popitem(last=False)
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

    Lookup order:
    1. Project items (via GitHub Projects GraphQL API)
    2. Workflow configuration (in-memory/DB)
    3. Default repository from app settings (.env)

    Args:
        access_token: GitHub access token.
        project_id: GitHub Project node ID.

    Returns:
        ``(owner, repo_name)`` tuple.

    Raises:
        src.exceptions.ValidationError: If no repository can be resolved.
    """
    from src.exceptions import ValidationError
    from src.services.github_projects import github_projects_service
    from src.services.workflow_orchestrator import get_workflow_config

    # 1. Try project items
    repo_info = await github_projects_service.get_project_repository(access_token, project_id)
    if repo_info:
        return repo_info

    # 2. Try workflow config
    config = await get_workflow_config(project_id)
    if config and config.repository_owner and config.repository_name:
        return config.repository_owner, config.repository_name

    # 3. Fall back to default repository from settings
    from src.config import get_settings

    settings = get_settings()
    if settings.default_repo_owner and settings.default_repo_name:
        return settings.default_repo_owner, settings.default_repo_name

    raise ValidationError(
        "No repository found for this project. Configure DEFAULT_REPOSITORY in .env "
        "or ensure the project has at least one linked issue."
    )
