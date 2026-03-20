"""Pagination utility — cursor-based pagination for in-memory lists."""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

from src.models.pagination import PaginatedResponse


def _encode_cursor(value: str) -> str:
    """Encode a cursor value to an opaque base64 string."""
    return base64.urlsafe_b64encode(value.encode()).decode()


def _decode_cursor(cursor: str) -> str:
    """Decode an opaque base64 cursor back to a string value."""
    try:
        return base64.urlsafe_b64decode(cursor.encode()).decode()
    except Exception as exc:
        raise ValueError(f"Invalid pagination cursor: {cursor}") from exc


def apply_pagination[T](
    items: list[T],
    limit: int = 25,
    cursor: str | None = None,
    key_fn: Callable[[T], str] | None = None,
) -> PaginatedResponse[T]:
    """Paginate a list using cursor-based navigation.

    Args:
        items: The full list of items to paginate.
        limit: Maximum number of items per page.
        cursor: Opaque cursor from a previous response's ``next_cursor``.
        key_fn: Function to extract a unique key from each item.
                Defaults to using the ``id`` attribute.

    Returns:
        A ``PaginatedResponse`` containing the current page.
    """
    if key_fn is None:
        key_fn = _default_key_fn

    total_count = len(items)

    if not items:
        return PaginatedResponse(
            items=[],
            next_cursor=None,
            has_more=False,
            total_count=total_count,
        )

    start_index = 0
    if cursor is not None:
        decoded = _decode_cursor(cursor)
        # Find the first item after the cursor position
        for i, item in enumerate(items):
            if key_fn(item) == decoded:
                start_index = i + 1
                break
        else:
            raise ValueError(f"Cursor target not found: {decoded}")

    end_index = start_index + limit
    page_items = items[start_index:end_index]
    has_more = end_index < total_count

    next_cursor: str | None = None
    if has_more and page_items:
        next_cursor = _encode_cursor(key_fn(page_items[-1]))

    return PaginatedResponse(
        items=page_items,
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total_count,
    )


def _default_key_fn(item: Any) -> str:
    """Extract a key from an item using its ``id`` attribute."""
    if hasattr(item, "id"):
        return str(item.id)
    if isinstance(item, dict) and "id" in item:
        return str(item["id"])
    raise TypeError(f"Cannot extract key from {type(item).__name__}; provide a key_fn")
