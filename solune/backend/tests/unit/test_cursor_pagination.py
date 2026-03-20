"""Unit tests for the cursor-based pagination utility (apply_pagination)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from src.models.pagination import PaginatedResponse, PaginationParams
from src.services.pagination import _decode_cursor, _encode_cursor, apply_pagination

# ── Helper model ──


class FakeItem(BaseModel):
    id: str
    name: str


def _make_items(n: int) -> list[FakeItem]:
    return [FakeItem(id=f"item-{i:03d}", name=f"Item {i}") for i in range(1, n + 1)]


# ── PaginationParams validation ──


class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams()
        assert p.limit == 25
        assert p.cursor is None

    def test_custom_values(self):
        p = PaginationParams(limit=10, cursor="abc")
        assert p.limit == 10
        assert p.cursor == "abc"

    def test_limit_minimum(self):
        with pytest.raises(ValidationError):
            PaginationParams(limit=0)

    def test_limit_maximum(self):
        with pytest.raises(ValidationError):
            PaginationParams(limit=101)

    def test_limit_edge_values(self):
        assert PaginationParams(limit=1).limit == 1
        assert PaginationParams(limit=100).limit == 100


# ── PaginatedResponse ──


class TestPaginatedResponse:
    def test_defaults(self):
        r: PaginatedResponse[FakeItem] = PaginatedResponse()
        assert r.items == []
        assert r.next_cursor is None
        assert r.has_more is False
        assert r.total_count is None


# ── Cursor encoding ──


class TestCursorEncoding:
    def test_roundtrip(self):
        original = "item-042"
        encoded = _encode_cursor(original)
        assert isinstance(encoded, str)
        assert encoded != original
        assert _decode_cursor(encoded) == original

    def test_invalid_cursor(self):
        with pytest.raises(ValueError, match="Invalid pagination cursor"):
            _decode_cursor("!!not-valid-base64!!")


# ── apply_pagination ──


class TestApplyPagination:
    def test_empty_list(self):
        result = apply_pagination([], limit=25)
        assert result.items == []
        assert result.has_more is False
        assert result.next_cursor is None
        assert result.total_count == 0

    def test_list_smaller_than_limit(self):
        items = _make_items(5)
        result = apply_pagination(items, limit=25)
        assert len(result.items) == 5
        assert result.has_more is False
        assert result.next_cursor is None
        assert result.total_count == 5

    def test_list_equal_to_limit(self):
        items = _make_items(10)
        result = apply_pagination(items, limit=10)
        assert len(result.items) == 10
        assert result.has_more is False
        assert result.next_cursor is None
        assert result.total_count == 10

    def test_list_larger_than_limit(self):
        items = _make_items(30)
        result = apply_pagination(items, limit=10)
        assert len(result.items) == 10
        assert result.has_more is True
        assert result.next_cursor is not None
        assert result.total_count == 30
        assert result.items[0].id == "item-001"
        assert result.items[-1].id == "item-010"

    def test_cursor_navigation_second_page(self):
        items = _make_items(30)
        page1 = apply_pagination(items, limit=10)
        assert page1.next_cursor is not None

        page2 = apply_pagination(items, limit=10, cursor=page1.next_cursor)
        assert len(page2.items) == 10
        assert page2.items[0].id == "item-011"
        assert page2.items[-1].id == "item-020"
        assert page2.has_more is True
        assert page2.total_count == 30

    def test_cursor_navigation_last_page(self):
        items = _make_items(25)
        page1 = apply_pagination(items, limit=10)
        page2 = apply_pagination(items, limit=10, cursor=page1.next_cursor)
        page3 = apply_pagination(items, limit=10, cursor=page2.next_cursor)

        assert len(page3.items) == 5
        assert page3.has_more is False
        assert page3.next_cursor is None
        assert page3.items[0].id == "item-021"
        assert page3.items[-1].id == "item-025"

    def test_full_traversal_no_duplicates_or_skips(self):
        items = _make_items(53)
        all_ids: list[str] = []
        cursor = None

        while True:
            page = apply_pagination(items, limit=10, cursor=cursor)
            all_ids.extend(item.id for item in page.items)
            if not page.has_more:
                break
            cursor = page.next_cursor

        expected_ids = [f"item-{i:03d}" for i in range(1, 54)]
        assert all_ids == expected_ids

    def test_invalid_cursor_raises(self):
        items = _make_items(10)
        bad_cursor = _encode_cursor("nonexistent-id")
        with pytest.raises(ValueError, match="Cursor target not found"):
            apply_pagination(items, limit=5, cursor=bad_cursor)

    def test_custom_key_fn(self):
        items = _make_items(10)
        result = apply_pagination(items, limit=5, key_fn=lambda x: x.name)
        assert len(result.items) == 5
        assert result.has_more is True

    def test_dict_items(self):
        items = [{"id": f"d-{i}", "value": i} for i in range(20)]
        result = apply_pagination(items, limit=5)
        assert len(result.items) == 5
        assert result.has_more is True
        assert result.total_count == 20

    def test_limit_one(self):
        items = _make_items(3)
        page1 = apply_pagination(items, limit=1)
        assert len(page1.items) == 1
        assert page1.has_more is True
        assert page1.items[0].id == "item-001"

        page2 = apply_pagination(items, limit=1, cursor=page1.next_cursor)
        assert len(page2.items) == 1
        assert page2.items[0].id == "item-002"

    def test_single_item_list(self):
        items = _make_items(1)
        result = apply_pagination(items, limit=25)
        assert len(result.items) == 1
        assert result.has_more is False
        assert result.next_cursor is None
        assert result.total_count == 1
