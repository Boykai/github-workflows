"""Tests for _filter_events_after — pure timeline event filtering.

Covers timezone handling, missing/unparseable timestamps, and conservative
inclusion of events that cannot be definitively excluded.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_gps():
    mock = AsyncMock(name="GitHubProjectsService")
    mock.check_copilot_finished_events = MagicMock(return_value=False)
    return mock


def _patch_gps(mock):
    return patch("src.services.copilot_polling.github_projects_service", mock)


def _import_filter(mock_gps):
    """Import _filter_events_after with patched module context."""
    with _patch_gps(mock_gps):
        from src.services.copilot_polling.completion import _filter_events_after
    return _filter_events_after


class TestFilterEventsAfter:
    """_filter_events_after returns events with created_at > cutoff."""

    def test_events_after_cutoff_included(self, mock_gps):
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        events = [
            {"type": "a", "created_at": "2025-06-01T13:00:00Z"},
            {"type": "b", "created_at": "2025-06-02T00:00:00Z"},
        ]
        result = fn(events, cutoff)
        assert len(result) == 2

    def test_events_before_cutoff_excluded(self, mock_gps):
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        events = [
            {"type": "old", "created_at": "2025-06-01T11:00:00Z"},
            {"type": "ancient", "created_at": "2025-01-01T00:00:00Z"},
        ]
        result = fn(events, cutoff)
        assert result == []

    def test_mixed_events_correct_subset(self, mock_gps):
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        events = [
            {"type": "before", "created_at": "2025-06-01T11:00:00Z"},
            {"type": "after", "created_at": "2025-06-01T13:00:00Z"},
            {"type": "exact", "created_at": "2025-06-01T12:00:00Z"},
        ]
        result = fn(events, cutoff)
        assert len(result) == 1
        assert result[0]["type"] == "after"

    def test_missing_created_at_included(self, mock_gps):
        """Events without created_at are conservatively included."""
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        events = [{"type": "no_ts"}]
        result = fn(events, cutoff)
        assert len(result) == 1

    def test_empty_string_created_at_included(self, mock_gps):
        """Events with empty created_at are conservatively included."""
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        events = [{"type": "empty", "created_at": ""}]
        result = fn(events, cutoff)
        assert len(result) == 1

    def test_unparseable_timestamp_included(self, mock_gps):
        """Events with unparseable timestamps are conservatively included."""
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        events = [{"type": "bad_ts", "created_at": "not-a-date"}]
        result = fn(events, cutoff)
        assert len(result) == 1

    def test_naive_cutoff_with_utc_events(self, mock_gps):
        """Timezone-naive cutoff is converted to match event timezone."""
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0)  # naive
        events = [
            {"type": "after", "created_at": "2025-06-01T13:00:00+00:00"},
            {"type": "before", "created_at": "2025-06-01T11:00:00+00:00"},
        ]
        result = fn(events, cutoff)
        assert len(result) == 1
        assert result[0]["type"] == "after"

    def test_empty_events_returns_empty(self, mock_gps):
        fn = _import_filter(mock_gps)
        cutoff = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
        result = fn([], cutoff)
        assert result == []
