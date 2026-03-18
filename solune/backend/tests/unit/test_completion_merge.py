"""Tests for _merge_child_pr_if_applicable — child PR merge workflow.

Covers the 6-step workflow: find linked PRs, filter child candidates,
verify target branch, handle drafts, merge, and return result.
"""

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_GPS = "src.services.copilot_polling.github_projects_service"
_GET_LINKED = "src.services.copilot_polling._get_linked_prs_including_sub_issues"
_UPDATE_SHA = "src.services.copilot_polling.update_issue_main_branch_sha"


@pytest.fixture
def mock_gps():
    mock = AsyncMock(name="GitHubProjectsService")
    mock.check_copilot_finished_events = MagicMock(return_value=False)
    return mock


def _make_linked_pr(number, *, state="OPEN", author="copilot[bot]"):
    return {"number": number, "state": state, "author": author}


def _make_pr_details(*, base_ref="copilot/branch", is_draft=False, head_ref="child-branch"):
    return {
        "id": "PR_node_child",
        "base_ref": base_ref,
        "is_draft": is_draft,
        "head_ref": head_ref,
    }


def _patches(mock_gps, linked_prs):
    """Stack context managers for gps + _get_linked_prs + update_sha."""
    stack = ExitStack()
    stack.enter_context(patch(_GPS, mock_gps))
    stack.enter_context(patch(_GET_LINKED, AsyncMock(return_value=linked_prs)))
    stack.enter_context(patch(_UPDATE_SHA, MagicMock()))
    return stack


class TestNoApplicableChildPR:
    """Cases where no child PR qualifies for merge."""

    @pytest.mark.asyncio
    async def test_no_linked_prs_returns_none(self, mock_gps):
        with _patches(mock_gps, []):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_main_pr_skipped(self, mock_gps):
        with _patches(mock_gps, [_make_linked_pr(1)]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_non_copilot_author_skipped(self, mock_gps):
        with _patches(mock_gps, [_make_linked_pr(2, author="human-user")]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_closed_pr_skipped(self, mock_gps):
        with _patches(mock_gps, [_make_linked_pr(2, state="CLOSED")]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is None

    @pytest.mark.asyncio
    async def test_wrong_target_branch_skipped(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(base_ref="some-other-branch")
        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is None


class TestSuccessfulMerge:
    """Cases where a child PR is found and merged."""

    @pytest.mark.asyncio
    async def test_merge_success_returns_merged_dict(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details()
        mock_gps.merge_pull_request.return_value = {"merge_commit": "sha_merge"}
        mock_gps.delete_branch.return_value = True

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is not None
        assert result["status"] == "merged"
        assert result["pr_number"] == 2
        assert result["merge_commit"] == "sha_merge"
        assert result["branch_deleted"] == "child-branch"

    @pytest.mark.asyncio
    async def test_draft_pr_marked_ready_before_merge(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(is_draft=True)
        mock_gps.merge_pull_request.return_value = {"merge_commit": "sha_merge"}
        mock_gps.delete_branch.return_value = True

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result["status"] == "merged"
        mock_gps.mark_pr_ready_for_review.assert_called_once()

    @pytest.mark.asyncio
    async def test_retarget_from_main_then_merge(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(base_ref="main")
        mock_gps.update_pr_base.return_value = True
        mock_gps.merge_pull_request.return_value = {"merge_commit": "sha_merge"}
        mock_gps.delete_branch.return_value = True

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result["status"] == "merged"
        mock_gps.update_pr_base.assert_called_once()

    @pytest.mark.asyncio
    async def test_retarget_fails_skips_pr(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details(base_ref="main")
        mock_gps.update_pr_base.return_value = False

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is None


class TestMergeFailure:
    """Cases where merge is attempted but fails."""

    @pytest.mark.asyncio
    async def test_merge_fails_returns_merge_failed(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr_details()
        mock_gps.merge_pull_request.return_value = None

        with _patches(mock_gps, [_make_linked_pr(2)]):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is not None
        assert result["status"] == "merge_failed"

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, mock_gps):
        with (
            patch(_GPS, mock_gps),
            patch(_GET_LINKED, AsyncMock(side_effect=RuntimeError("API error"))),
        ):
            from src.services.copilot_polling.completion import (
                _merge_child_pr_if_applicable,
            )

            result = await _merge_child_pr_if_applicable(
                access_token="tok",
                owner="o",
                repo="r",
                issue_number=10,
                main_branch="copilot/branch",
                main_pr_number=1,
                completed_agent="speckit.implement",
            )

        assert result is None
