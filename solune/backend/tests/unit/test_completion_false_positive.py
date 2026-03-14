"""Tests for false-positive Signal 3 rejection in _check_main_pr_completion.

The pipeline must NOT advance when the agent is unassigned but the branch
HEAD SHA has not changed from agent_assigned_sha. This catches the scenario
where Copilot unassigns itself without pushing commits (timeout, failure, etc.).

Covers: FR-007, SC-003
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_gps():
    """AsyncMock of GitHubProjectsService for completion checks.

    check_copilot_finished_events is synchronous in the real service,
    so we override it with a regular MagicMock to avoid unawaited coroutine
    issues.
    """
    mock = AsyncMock(name="GitHubProjectsService")
    mock.check_copilot_finished_events = MagicMock(return_value=False)
    return mock


def _patch_gps(mock):
    """Return context manager that patches the service on the _cp module."""
    return patch(
        "src.services.copilot_polling.github_projects_service",
        mock,
    )


class TestSignal3FalsePositiveRejection:
    """Signal 3 must require SHA change before marking completion."""

    @pytest.mark.asyncio
    async def test_no_advance_when_sha_unchanged_and_agent_unassigned(self, mock_gps):
        """Pipeline must NOT advance when Copilot unassigns without pushing commits.

        Scenario: agent_assigned_sha == current HEAD SHA, Copilot is unassigned.
        Expected: return False (do not advance pipeline).
        """
        sha = "abc1234def5678"

        # PR details — same SHA as when agent was assigned
        mock_gps.get_pull_request.return_value = {
            "id": "PR_node_1",
            "state": "OPEN",
            "is_draft": True,
            "last_commit": {"sha": sha},
        }

        # Timeline events — no copilot_finished events
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False

        # Copilot unassigned itself (the false-positive trigger)
        mock_gps.is_copilot_assigned_to_issue.return_value = False

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                main_pr_number=42,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 1, 1, tzinfo=UTC),
                agent_assigned_sha=sha,
            )

        # Must NOT advance — no new commits were pushed
        assert result is False, (
            "Pipeline must not advance when SHA is unchanged even if Copilot unassigned"
        )

    @pytest.mark.asyncio
    async def test_advance_when_sha_changed_and_agent_unassigned(self, mock_gps):
        """Pipeline SHOULD advance when Copilot pushes commits and then unassigns.

        Scenario: current HEAD SHA != agent_assigned_sha, Copilot is unassigned.
        Expected: return True (advance pipeline).
        """
        assigned_sha = "abc1234def5678"
        new_sha = "new9876commit5432"

        mock_gps.get_pull_request.return_value = {
            "id": "PR_node_1",
            "state": "OPEN",
            "is_draft": True,
            "last_commit": {"sha": new_sha},
        }
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = False

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                main_pr_number=42,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 1, 1, tzinfo=UTC),
                agent_assigned_sha=assigned_sha,
            )

        # SHOULD advance — new commits exist and Copilot finished
        assert result is True

    @pytest.mark.asyncio
    async def test_no_advance_when_sha_unchanged_and_agent_still_assigned(self, mock_gps):
        """Pipeline must NOT advance when SHA unchanged and Copilot still assigned.

        Scenario: Same SHA, Copilot still working.
        Expected: return False.
        """
        sha = "abc1234def5678"

        mock_gps.get_pull_request.return_value = {
            "id": "PR_node_1",
            "state": "OPEN",
            "is_draft": True,
            "last_commit": {"sha": sha},
        }
        mock_gps.get_pr_timeline_events.return_value = []
        mock_gps.check_copilot_finished_events.return_value = False
        mock_gps.is_copilot_assigned_to_issue.return_value = True

        with _patch_gps(mock_gps):
            from src.services.copilot_polling.completion import (
                _check_main_pr_completion,
            )

            result = await _check_main_pr_completion(
                access_token="test-token",
                owner="test-owner",
                repo="test-repo",
                main_pr_number=42,
                issue_number=10,
                agent_name="speckit.implement",
                pipeline_started_at=datetime(2025, 1, 1, tzinfo=UTC),
                agent_assigned_sha=sha,
            )

        assert result is False
