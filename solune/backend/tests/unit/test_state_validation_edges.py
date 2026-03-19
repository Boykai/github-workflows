"""Edge-case tests for copilot_polling/state_validation.py.

Covers all branches of validate_pipeline_labels: consistent labels,
label→table mismatch, missing label, stale label, and API failures.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.services.copilot_polling.state_validation import validate_pipeline_labels

# Minimal Step stub with .agent_name and .state
_STATE_ACTIVE = "🔄 Active"
_STATE_PENDING = "⏳ Pending"
_STATE_DONE = "✅ Done"


def _step(agent_name: str, state: str) -> SimpleNamespace:
    return SimpleNamespace(agent_name=agent_name, state=state)


_BASE_KWARGS = {
    "access_token": "tok",
    "owner": "owner",
    "repo": "repo",
    "issue_number": 42,
}

_GPS = "src.services.copilot_polling.github_projects_service"


class TestLabelAndTableConsistent:
    """When label_agent == table_agent, no corrections are needed."""

    @pytest.mark.asyncio
    async def test_both_none(self):
        """No label, no active step → consistent → no corrections."""
        labels: list[dict[str, str]] = []
        steps = [_step("planner", _STATE_DONE)]
        changed, corrections = await validate_pipeline_labels(
            **_BASE_KWARGS, labels=labels, tracking_steps=steps
        )
        assert changed is False
        assert corrections == []

    @pytest.mark.asyncio
    async def test_both_same_active(self):
        """Label and active step agree → no corrections."""
        labels = [{"name": "agent:builder"}]
        steps = [_step("builder", _STATE_ACTIVE)]
        with patch(
            "src.services.copilot_polling.state_validation.find_agent_label", return_value="builder"
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )
        assert changed is False
        assert corrections == []


class TestLabelMissing:
    """Label is absent but tracking table has an active agent → add label."""

    @pytest.mark.asyncio
    async def test_adds_missing_label(self):
        labels: list[dict[str, str]] = []
        steps = [_step("builder", _STATE_ACTIVE)]

        mock_gps = AsyncMock()
        with (
            patch(
                "src.services.copilot_polling.state_validation.find_agent_label", return_value=None
            ),
            patch(_GPS, mock_gps),
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )

        assert changed is True
        assert len(corrections) == 1
        assert "Added missing" in corrections[0]
        mock_gps.update_issue_state.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_adds_label_from_pending_step(self):
        """Pending step is used when no active step exists."""
        labels: list[dict[str, str]] = []
        steps = [_step("planner", _STATE_PENDING)]

        mock_gps = AsyncMock()
        with (
            patch(
                "src.services.copilot_polling.state_validation.find_agent_label", return_value=None
            ),
            patch(_GPS, mock_gps),
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )

        assert changed is True
        assert "planner" in corrections[0]


class TestStaleLabel:
    """Label present but table has no active/pending agent → remove label."""

    @pytest.mark.asyncio
    async def test_removes_stale_label(self):
        labels = [{"name": "agent:old-agent"}]
        steps = [_step("builder", _STATE_DONE)]

        mock_gps = AsyncMock()
        with (
            patch(
                "src.services.copilot_polling.state_validation.find_agent_label",
                return_value="old-agent",
            ),
            patch(_GPS, mock_gps),
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )

        assert changed is True
        assert "Removed stale" in corrections[0]
        mock_gps.update_issue_state.assert_awaited_once()


class TestLabelTableDisagree:
    """Both label and table are present but disagree → table wins."""

    @pytest.mark.asyncio
    async def test_swaps_label_to_match_table(self):
        labels = [{"name": "agent:wrong-agent"}]
        steps = [_step("correct-agent", _STATE_ACTIVE)]

        mock_gps = AsyncMock()
        with (
            patch(
                "src.services.copilot_polling.state_validation.find_agent_label",
                return_value="wrong-agent",
            ),
            patch(_GPS, mock_gps),
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )

        assert changed is True
        assert "swapped" in corrections[0]
        # Should have added new label and removed old one
        call_kwargs = mock_gps.update_issue_state.call_args.kwargs
        assert "labels_add" in call_kwargs
        assert "labels_remove" in call_kwargs


class TestApiFailures:
    """API failures should be caught and reported, not propagated."""

    @pytest.mark.asyncio
    async def test_add_label_failure_reported(self):
        labels: list[dict[str, str]] = []
        steps = [_step("builder", _STATE_ACTIVE)]

        mock_gps = AsyncMock()
        mock_gps.update_issue_state.side_effect = Exception("API error")
        with (
            patch(
                "src.services.copilot_polling.state_validation.find_agent_label", return_value=None
            ),
            patch(_GPS, mock_gps),
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )

        assert changed is True
        assert "Failed to add" in corrections[0]

    @pytest.mark.asyncio
    async def test_swap_label_failure_reported(self):
        labels = [{"name": "agent:wrong"}]
        steps = [_step("correct", _STATE_ACTIVE)]

        mock_gps = AsyncMock()
        mock_gps.update_issue_state.side_effect = RuntimeError("Network error")
        with (
            patch("src.constants.find_agent_label", return_value="wrong"),
            patch(_GPS, mock_gps),
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )

        assert changed is True
        assert "Failed to correct" in corrections[0]

    @pytest.mark.asyncio
    async def test_remove_stale_failure_reported(self):
        labels = [{"name": "agent:stale"}]
        steps = [_step("done-agent", _STATE_DONE)]

        mock_gps = AsyncMock()
        mock_gps.update_issue_state.side_effect = Exception("rate limited")
        with (
            patch("src.constants.find_agent_label", return_value="stale"),
            patch(_GPS, mock_gps),
        ):
            changed, corrections = await validate_pipeline_labels(
                **_BASE_KWARGS, labels=labels, tracking_steps=steps
            )

        assert changed is True
        assert "Failed to remove" in corrections[0]
