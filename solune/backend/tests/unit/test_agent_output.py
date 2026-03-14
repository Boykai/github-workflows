"""Tests for agent_output.py dataclasses and helpers (T098)."""

from src.services.copilot_polling.agent_output import CommentScanResult


class TestCommentScanResult:
    """CommentScanResult is a frozen dataclass with sensible defaults."""

    def test_defaults(self):
        result = CommentScanResult(has_done_marker=False)
        assert result.has_done_marker is False
        assert result.done_comment_id is None
        assert result.agent_output_files == []
        assert result.merge_candidates == []

    def test_with_done_marker(self):
        result = CommentScanResult(
            has_done_marker=True,
            done_comment_id="IC_123",
            agent_output_files=["output.md"],
            merge_candidates=["pr-branch"],
        )
        assert result.has_done_marker is True
        assert result.done_comment_id == "IC_123"
        assert result.agent_output_files == ["output.md"]
        assert result.merge_candidates == ["pr-branch"]

    def test_frozen(self):
        result = CommentScanResult(has_done_marker=True)
        try:
            result.has_done_marker = False  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except AttributeError:
            pass

    def test_equality(self):
        a = CommentScanResult(has_done_marker=True, done_comment_id="IC_1")
        b = CommentScanResult(has_done_marker=True, done_comment_id="IC_1")
        assert a == b

    def test_inequality(self):
        a = CommentScanResult(has_done_marker=True)
        b = CommentScanResult(has_done_marker=False)
        assert a != b
