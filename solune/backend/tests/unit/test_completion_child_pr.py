"""Tests for _find_completed_child_pr — child PR completion detection.

Covers early return for copilot-review, claim tracking, MERGED/non-draft/
timeline-based completion, and the title-based fallback.
"""

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_GPS = "src.services.copilot_polling.github_projects_service"
_GET_LINKED = "src.services.copilot_polling._get_linked_prs_including_sub_issues"


@pytest.fixture
def mock_gps():
    mock = AsyncMock(name="GitHubProjectsService")
    mock.check_copilot_finished_events = MagicMock(return_value=False)
    return mock


def _make_linked_pr(number, *, state="OPEN", author="copilot[bot]"):
    return {"number": number, "state": state, "author": author}


def _make_pr_details(
    *,
    base_ref="copilot/branch",
    is_draft=True,
    title="[WIP] Implement feature",
    commits=1,
    changed_files=5,
    head_ref="child-branch",
    state="OPEN",
):
    return {
        "id": "PR_node_child",
        "base_ref": base_ref,
        "is_draft": is_draft,
        "head_ref": head_ref,
        "title": title,
        "commits": commits,
        "changed_files": changed_files,
        "state": state,
        "last_commit": {"sha": "abc123"},
    }


def _patches(mock_gps, linked_prs):
    stack = ExitStack()
    stack.enter_context(patch(_GPS, mock_gps))
    stack.enter_context(patch(_GET_LINKED, AsyncMock(return_value=linked_prs)))
    return stack


class TestEarlyReturns:
    """Cases that return None immediately without checking PRs."""

    @pytest.mark.asyncio
    async def test_copilot_review_returns_none(self, mock_gps):
        """copilot-review never creates child PRs."""
        with patch(_GPS, mock_gps):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="copilot-review",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_no_linked_prs_returns_none(self, mock_gps):
        with _patches(mock_gps, []):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        assert result is None


class TestMergedPR:
    """MERGED child PRs are treated as completed."""

    @pytest.mark.asyncio
    async def test_merged_pr_with_changes_returns_completed(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(changed_files=3, state="MERGED")
        with _patches(mock_gps, [_make_linked_pr(2, state="MERGED")]):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        assert result is not None
        assert result["copilot_finished"] is True
        assert result["is_merged"] is True

    @pytest.mark.asyncio
    async def test_merged_pr_zero_changes_skipped(self, mock_gps):
        """MERGED with 0 changed files is a false positive."""
        mock_gps.get_pull_request.return_value = _make_pr_details(changed_files=0, state="MERGED")
        with _patches(mock_gps, [_make_linked_pr(2, state="MERGED")]):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        assert result is None


class TestNonDraftPR:
    """Non-draft child PRs are completed (with WIP guard)."""

    @pytest.mark.asyncio
    async def test_non_draft_returns_completed(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(
            is_draft=False, title="Implement feature", commits=3
        )
        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        assert result is not None
        assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_non_draft_wip_title_single_commit_falls_through(self, mock_gps):
        """Non-draft but [WIP] title + 1 commit -> falls to timeline check."""
        mock_gps.get_pull_request.return_value = _make_pr_details(
            is_draft=False, title="[WIP] Initial plan", commits=1
        )
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        # Falls through to timeline -> no events -> title still [WIP] -> no completion
        assert result is None


class TestTimelineCompletion:
    """Timeline event-based completion detection."""

    @pytest.mark.asyncio
    async def test_timeline_finished_events_returns_completed(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details()
        mock_gps.get_pr_timeline_events.return_value = [
            {"type": "copilot_work_finished"},
        ]
        mock_gps.check_copilot_finished_events.return_value = True

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        assert result is not None
        assert result["copilot_finished"] is True

    @pytest.mark.asyncio
    async def test_title_fallback_no_wip_no_events(self, mock_gps):
        """No timeline events + title without [WIP] -> completed (fallback)."""
        mock_gps.get_pull_request.return_value = _make_pr_details(title="Implement feature")
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        assert result is not None
        assert result["copilot_finished"] is True


class TestClaimTracking:
    """Claimed child PRs are skipped for other agents."""

    @pytest.mark.asyncio
    async def test_claimed_by_other_agent_skipped(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(
            is_draft=False, title="Done", commits=3
        )
        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.state import _claimed_child_prs

            _claimed_child_prs.add("10:2:speckit.specify")
            try:
                from src.services.copilot_polling.completion import (
                    _find_completed_child_pr,
                )

                result = await _find_completed_child_pr(
                    access_token="tok",
                    owner="o",
                    repo="r",
                    issue_number=10,
                    main_branch="copilot/branch",
                    main_pr_number=1,
                    agent_name="speckit.implement",
                )
            finally:
                _claimed_child_prs.discard("10:2:speckit.specify")

        assert result is None

    @pytest.mark.asyncio
    async def test_claimed_by_same_agent_not_skipped(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(
            is_draft=False, title="Done", commits=3
        )
        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.state import _claimed_child_prs

            _claimed_child_prs.add("10:2:speckit.implement")
            try:
                from src.services.copilot_polling.completion import (
                    _find_completed_child_pr,
                )

                result = await _find_completed_child_pr(
                    access_token="tok",
                    owner="o",
                    repo="r",
                    issue_number=10,
                    main_branch="copilot/branch",
                    main_pr_number=1,
                    agent_name="speckit.implement",
                )
            finally:
                _claimed_child_prs.discard("10:2:speckit.implement")

        assert result is not None
        assert result["copilot_finished"] is True


class TestExceptionHandling:
    """Exceptions are caught and None is returned."""

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, mock_gps):
        with (
            patch(_GPS, mock_gps),
            patch(_GET_LINKED, AsyncMock(side_effect=RuntimeError("API error"))),
        ):
            from src.services.copilot_polling.completion import (
                _find_completed_child_pr,
            )

            result = await _find_completed_child_pr(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                agent_name="speckit.implement",
            )

        assert result is None
