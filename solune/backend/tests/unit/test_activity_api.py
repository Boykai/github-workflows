"""Unit tests for activity feed pagination helpers."""

from __future__ import annotations

import base64
import json

import pytest

from src.api.activity import _query_events


def _encode_cursor_payload(payload: object) -> str:
    raw = json.dumps(payload)
    return base64.urlsafe_b64encode(raw.encode()).decode()


class TestQueryEvents:
    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "cursor",
        [
            "ab",
            _encode_cursor_payload({"created_at": "2024-01-01T00:00:00Z", "id": "evt-1"}),
            _encode_cursor_payload(None),
        ],
    )
    async def test_invalid_cursor_shapes_are_ignored(self, mock_db, cursor: str):
        result = await _query_events(mock_db, project_id="PVT_test", cursor=cursor)

        assert result["items"] == []
        assert result["has_more"] is False
        assert result["next_cursor"] is None
        assert result["total_count"] is None
