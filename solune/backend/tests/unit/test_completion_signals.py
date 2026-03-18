"""Tests for all 3 completion signals + safety net in _check_main_pr_completion.

Existing test_completion_false_positive.py covers Signal 3 false-positive
rejection.  This file covers positive paths for all signals and the
safety-net fallback.

Covers: FR-007, SC-003
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_gps():
    """AsyncMock of GitHubProjectsService for completion checks."""
    mock = AsyncMock(name="GitHubProjectsService")
    mock.check_copilot_finished_events = MagicMock(return_value=False)
    return mock


def _patch_gps(mock):
    return patch("src.services.copilot_polling.github_projects_service", mock)


def _make_pr(*, is_draft=True, state="OPEN", sha="abc123"):
    return {
        "id": "PR_node_1",
        "state": state,
        "is_draft": is_draft,
        "last_commit": {"sha": sha},
    }


class TestSignal1NonDraft:
    """Signal 1: PR no longer a draft → completion detected."""

    @pytest.mark.asyncio
    async def test_non_draft_pr_returns_true(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr(is_draft=False)
        mock_gps.get_pr_timeline_events.return_value = []

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_non_draft_pr_in_system_marked_ready_skips_signal1(self, mock_gps):
        """If our system marked the PR ready, Signal 1 is ignored."""
        mock_gps.get_pull_request.return_value = _make_pr(is_draft=False)
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = True  # still assigned → no signal 3

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )
            from src.services.copilot_polling.state import _system_marked_ready_prs

            _system_marked_ready_prs.add(1)
            try:
                result = await _check_main_pr_completion(
                    access_token="tok",
                    owner="o",
                    repo="r",
                    main_pr_number=1,
                    issue_number=10,
                    agent_name="speckit.implement",
                    agent_assigned_sha="abc123",
                )
            finally:
                _system_marked_ready_prs.discard(1)

        assert result is False


class TestSignal2TimelineEvents:
    """Signal 2: Fresh copilot_work_finished events after pipeline start."""

    @pytest.mark.asyncio
    async def test_fresh_finished_event_returns_true(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr()
        mock_gps.get_pr_timeline_events.return_value = [
            {"type": "copilot_work_finished", "created_at": "2025-06-02T00:00:00Z"},
        ]
        # check_copilot_finished_events is called with filtered events
        mock_gps.check_copilot_finished_events.return_value = True

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 6, 1, tzinfo=UTC),
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_events_before_pipeline_start_filtered_out(self, mock_gps):
        """Events before pipeline_started_at do not trigger Signal 2."""
        mock_gps.get_pull_request.return_value = _make_pr()
        mock_gps.get_pr_timeline_events.return_value = [
            {"type": "copilot_work_finished", "created_at": "2025-05-01T00:00:00Z"},
        ]
        # After filtering, the fresh events have no completed event
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = True

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 6, 1, tzinfo=UTC),
                agent_assigned_sha="abc123",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_no_pipeline_start_uses_all_events(self, mock_gps):
        """Without pipeline_started_at, all events are used (less safe)."""
        mock_gps.get_pull_request.return_value = _make_pr()
        mock_gps.get_pr_timeline_events.return_value = [
            {"type": "copilot_work_finished", "created_at": "2025-01-01T00:00:00Z"},
        ]
        mock_gps.check_copilot_finished_events.return_value = True

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=None,
            )

        assert result is True


class TestSignal3CommitBased:
    """Signal 3: SHA changed AND Copilot unassigned."""

    @pytest.mark.asyncio
    async def test_sha_changed_and_unassigned_returns_true(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr(sha="new_sha")
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = False

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 1, 1, tzinfo=UTC),
                agent_assigned_sha="old_sha",
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_sha_changed_but_still_assigned_returns_false(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr(sha="new_sha")
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = True

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 1, 1, tzinfo=UTC),
                agent_assigned_sha="old_sha",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_sub_issue_number_used_for_assignment_check(self, mock_gps):
        """When sub_issue_number is provided, assignment check uses it."""
        mock_gps.get_pull_request.return_value = _make_pr(sha="new_sha")
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = False

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 1, 1, tzinfo=UTC),
                agent_assigned_sha="old_sha",
                sub_issue_number=99,
            )

        assert result is True
        # Verify the assignment check used sub_issue_number, not issue_number
        call_kwargs = mock_gps.is_copilot_assigned_to_issue.call_args[1]
        assert call_kwargs["issue_number"] == 99


class TestSafetyNet:
    """Safety net: unfiltered timeline + Copilot unassigned as last resort."""

    @pytest.mark.asyncio
    async def test_safety_net_fires_when_not_subsequent(self, mock_gps):
        """Safety net returns True when all signals fail but unfiltered
        timeline has completion events and Copilot is unassigned.

        To reach the safety net we must pass through the 'no agent_assigned_sha'
        else-branch without returning.  We do this by omitting committed_date
        from last_commit so the fresh-commit double-check falls through.
        """
        mock_gps.get_pull_request.return_value = {
            "id": "PR_node_1",
            "state": "OPEN",
            "is_draft": True,
            "last_commit": {"sha": "abc123"},  # no committed_date
        }
        mock_gps.get_pr_timeline_events.return_value = [
            {"type": "copilot_work_finished", "created_at": "2025-05-01T00:00:00Z"},
        ]
        # Signal 2 (fresh_events filtered to empty): False
        # Safety net (all events): True
        mock_gps.check_copilot_finished_events.side_effect = [False, True]
        mock_gps.is_copilot_assigned_to_issue.return_value = False

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 6, 1, tzinfo=UTC),
                agent_assigned_sha="",  # skip SHA-based Signal 3 block
                is_subsequent_agent=False,
            )

        assert result is True

    @pytest.mark.asyncio
    async def test_safety_net_skipped_for_subsequent_agent(self, mock_gps):
        """Safety net is skipped when is_subsequent_agent=True."""
        mock_gps.get_pull_request.return_value = _make_pr()
        mock_gps.get_pr_timeline_events.return_value = [
            {"type": "copilot_work_finished", "created_at": "2025-05-01T00:00:00Z"},
        ]
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = True

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 6, 1, tzinfo=UTC),
                agent_assigned_sha="abc123",
                is_subsequent_agent=True,
            )

        assert result is False


class TestEdgeCases:
    """Edge cases: PR not found, not OPEN, exceptions."""

    @pytest.mark.asyncio
    async def test_pr_not_found_returns_false(self, mock_gps):
        mock_gps.get_pull_request.return_value = None

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_pr_not_open_returns_false(self, mock_gps):
        mock_gps.get_pull_request.return_value = _make_pr(state="MERGED")

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
            )

        assert result is False

    @pytest.mark.asyncio
    async def test_exception_returns_false(self, mock_gps):
        mock_gps.get_pull_request.side_effect = RuntimeError("API down")

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="tok",
                owner="o",
                repo="r",
                main_pr_number=1,
                issue_number=10,
                agent_name="speckit.implement",
            )

        assert result is False
