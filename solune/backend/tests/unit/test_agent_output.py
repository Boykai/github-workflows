"""Tests for agent_output.py dataclasses, helpers, and _post_markdown_outputs (T098)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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


# ---------------------------------------------------------------------------
# Functional tests for _post_markdown_outputs
# ---------------------------------------------------------------------------

_GPS = "src.services.copilot_polling.github_projects_service"
_OUTPUT_FILES = "src.services.copilot_polling.AGENT_OUTPUT_FILES"
_GET_SUB_ISSUES = "src.services.copilot_polling.get_issue_sub_issues"


@pytest.fixture
def mock_gps():
    mock = AsyncMock(name="GitHubProjectsService")
    mock.check_copilot_finished_events = MagicMock(return_value=False)
    return mock


def _make_pipeline(agent_name, sub_issue_number=99):
    """Create a minimal pipeline-like object with agent_sub_issues."""
    return SimpleNamespace(
        agent_sub_issues={agent_name: {"number": sub_issue_number}},
    )


def _cp_patches(mock_gps, output_files, sub_issues=None):
    """Stack context managers for gps + AGENT_OUTPUT_FILES + get_issue_sub_issues."""
    from contextlib import ExitStack

    stack = ExitStack()
    stack.enter_context(patch(_GPS, mock_gps))
    stack.enter_context(patch(_OUTPUT_FILES, output_files))
    stack.enter_context(patch(_GET_SUB_ISSUES, MagicMock(return_value=sub_issues or {})))
    return stack


class TestPostMarkdownOutputs:
    """Functional tests for _post_markdown_outputs."""

    @pytest.mark.asyncio
    async def test_expected_file_posted_successfully(self, mock_gps):
        """Expected output file posted -> count = 1."""
        mock_gps.get_file_content_from_ref.return_value = "# Spec\nContent"
        mock_gps.create_issue_comment.return_value = {"id": "IC_1"}

        with _cp_patches(mock_gps, {"speckit.specify": ["spec.md"]}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=_make_pipeline("speckit.specify"),
                pr_number=1,
                head_ref="branch",
                pr_files=[{"filename": "docs/spec.md", "status": "added"}],
            )

        assert result == 1

    @pytest.mark.asyncio
    async def test_expected_file_comment_fails_count_zero(self, mock_gps):
        """Expected file comment creation fails (None) -> count = 0."""
        mock_gps.get_file_content_from_ref.return_value = "content"
        mock_gps.create_issue_comment.return_value = None

        with _cp_patches(mock_gps, {"speckit.specify": ["spec.md"]}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=_make_pipeline("speckit.specify"),
                pr_number=1,
                head_ref="branch",
                pr_files=[{"filename": "spec.md", "status": "added"}],
            )

        assert result == 0

    @pytest.mark.asyncio
    async def test_other_md_file_posted(self, mock_gps):
        """Non-expected .md file IS posted (other .md posting loop)."""
        mock_gps.get_file_content_from_ref.return_value = "readme content"
        mock_gps.create_issue_comment.return_value = {"id": "IC_2"}

        with _cp_patches(mock_gps, {"speckit.specify": ["spec.md"]}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=_make_pipeline("speckit.specify"),
                pr_number=1,
                head_ref="branch",
                pr_files=[{"filename": "README.md", "status": "added"}],
            )

        assert result == 1

    @pytest.mark.asyncio
    async def test_other_md_comment_fails_count_zero(self, mock_gps):
        """Bug fix verification: other .md comment fails -> count = 0."""
        mock_gps.get_file_content_from_ref.return_value = "content"
        mock_gps.create_issue_comment.return_value = None

        with _cp_patches(mock_gps, {"speckit.specify": ["spec.md"]}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=_make_pipeline("speckit.specify"),
                pr_number=1,
                head_ref="branch",
                pr_files=[{"filename": "CHANGELOG.md", "status": "modified"}],
            )

        assert result == 0

    @pytest.mark.asyncio
    async def test_no_sub_issue_returns_zero(self, mock_gps):
        """No sub-issue found -> returns 0 without posting."""
        with _cp_patches(mock_gps, {"speckit.specify": []}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            pipeline = SimpleNamespace(agent_sub_issues={})
            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=pipeline,
                pr_number=1,
                head_ref="branch",
                pr_files=[{"filename": "spec.md", "status": "added"}],
            )

        assert result == 0
        mock_gps.create_issue_comment.assert_not_called()

    @pytest.mark.asyncio
    async def test_content_fetch_fails_skips_file(self, mock_gps):
        """Content fetch returns None -> no comment posted."""
        mock_gps.get_file_content_from_ref.return_value = None

        with _cp_patches(mock_gps, {"speckit.specify": ["spec.md"]}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=_make_pipeline("speckit.specify"),
                pr_number=1,
                head_ref="branch",
                pr_files=[{"filename": "spec.md", "status": "added"}],
            )

        assert result == 0
        mock_gps.create_issue_comment.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_md_other_file_skipped(self, mock_gps):
        """Non-.md files in the 'other' loop are skipped."""
        mock_gps.get_file_content_from_ref.return_value = "content"

        with _cp_patches(mock_gps, {"speckit.specify": []}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=_make_pipeline("speckit.specify"),
                pr_number=1,
                head_ref="branch",
                pr_files=[{"filename": "app.py", "status": "added"}],
            )

        assert result == 0

    @pytest.mark.asyncio
    async def test_mixed_expected_and_other_md(self, mock_gps):
        """Both expected and other .md files are posted."""
        mock_gps.get_file_content_from_ref.return_value = "content"
        mock_gps.create_issue_comment.return_value = {"id": "IC_ok"}

        with _cp_patches(mock_gps, {"speckit.specify": ["spec.md"]}):
            from src.services.copilot_polling.agent_output import (
                _post_markdown_outputs,
            )

            result = await _post_markdown_outputs(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                current_agent="speckit.specify",
                pipeline=_make_pipeline("speckit.specify"),
                pr_number=1,
                head_ref="branch",
                pr_files=[
                    {"filename": "spec.md", "status": "added"},
                    {"filename": "CHANGELOG.md", "status": "modified"},
                ],
            )

        assert result == 2
