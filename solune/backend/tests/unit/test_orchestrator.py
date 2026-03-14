"""Tests for pipeline.py helpers — _derive_pipeline_started_at (T099)."""

from datetime import UTC, datetime
from unittest.mock import patch

from src.services.copilot_polling.pipeline import _derive_pipeline_started_at


class TestDerivePipelineStartedAt:
    """Priority chain: last_done_timestamp > latest Done! comment > issue created_at > utcnow()."""

    def test_uses_last_done_timestamp_when_valid(self):
        ts = "2024-06-15T10:30:00+00:00"
        result = _derive_pipeline_started_at(ts, None)
        assert result == datetime.fromisoformat(ts)

    def test_ignores_invalid_last_done_timestamp(self):
        # Falls through to utcnow() when everything else is missing
        sentinel = datetime(2024, 1, 1, tzinfo=UTC)
        with patch("src.services.copilot_polling.pipeline.utcnow", return_value=sentinel):
            result = _derive_pipeline_started_at("not-a-date", None)
        assert result == sentinel

    def test_uses_latest_done_comment(self):
        issue_data = {
            "comments": [
                {"body": "agent-a: Done!", "created_at": "2024-06-10T08:00:00+00:00"},
                {"body": "agent-b: Done!", "created_at": "2024-06-12T09:00:00+00:00"},
                {"body": "no marker here", "created_at": "2024-06-13T10:00:00+00:00"},
            ],
        }
        result = _derive_pipeline_started_at(None, issue_data)
        assert result == datetime.fromisoformat("2024-06-12T09:00:00+00:00")

    def test_uses_issue_created_at_when_no_done_comments(self):
        issue_data = {
            "comments": [{"body": "just a comment", "created_at": "2024-06-10T08:00:00+00:00"}],
            "created_at": "2024-06-01T00:00:00+00:00",
        }
        result = _derive_pipeline_started_at(None, issue_data)
        assert result == datetime.fromisoformat("2024-06-01T00:00:00+00:00")

    def test_falls_back_to_utcnow(self):
        sentinel = datetime(2024, 7, 1, tzinfo=UTC)
        with patch("src.services.copilot_polling.pipeline.utcnow", return_value=sentinel):
            result = _derive_pipeline_started_at(None, None)
        assert result == sentinel

    def test_multiline_comment_with_done_marker(self):
        """A Done! marker on any line of a multi-line comment body counts."""
        issue_data = {
            "comments": [
                {
                    "body": "Progress update\nagent-x: Done!\nMore text",
                    "created_at": "2024-06-20T12:00:00+00:00",
                },
            ],
        }
        result = _derive_pipeline_started_at(None, issue_data)
        assert result == datetime.fromisoformat("2024-06-20T12:00:00+00:00")

    def test_empty_comments_list(self):
        sentinel = datetime(2024, 1, 1, tzinfo=UTC)
        issue_data = {"comments": [], "created_at": ""}
        with patch("src.services.copilot_polling.pipeline.utcnow", return_value=sentinel):
            result = _derive_pipeline_started_at(None, issue_data)
        assert result == sentinel

    def test_none_issue_data_with_none_timestamp(self):
        sentinel = datetime(2024, 1, 1, tzinfo=UTC)
        with patch("src.services.copilot_polling.pipeline.utcnow", return_value=sentinel):
            result = _derive_pipeline_started_at(None, None)
        assert result == sentinel
