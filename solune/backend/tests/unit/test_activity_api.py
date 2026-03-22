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

    @pytest.mark.anyio
    @pytest.mark.parametrize(
        "cursor",
        [
            _encode_cursor_payload("0z"),
            _encode_cursor_payload([1, 2]),
            _encode_cursor_payload(["2024-01-02T00:00:00Z"]),
        ],
    )
    async def test_malformed_cursor_payloads_do_not_filter_real_results(self, mock_db, cursor: str):
        await mock_db.execute(
            """
            INSERT INTO activity_events (
                id, event_type, entity_type, entity_id, project_id,
                actor, action, summary, detail, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "evt-1",
                "pipeline_run",
                "pipeline",
                "pipe-1",
                "PVT_test",
                "alice",
                "updated",
                "Pipeline updated",
                None,
                "2024-01-02T00:00:00Z",
            ),
        )
        await mock_db.commit()

        result = await _query_events(mock_db, project_id="PVT_test", cursor=cursor)

        assert [item["id"] for item in result["items"]] == ["evt-1"]
        assert result["has_more"] is False
        assert result["next_cursor"] is None
