"""Additional boundary coverage for pipeline label validation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.services.copilot_polling.state_validation import validate_pipeline_labels

_GPS = "src.services.copilot_polling.github_projects_service"


def _step(agent_name: str, state: str) -> SimpleNamespace:
    return SimpleNamespace(agent_name=agent_name, state=state)


@pytest.mark.asyncio
async def test_active_step_wins_over_pending_steps_when_resolving_label_mismatch():
    mock_github = AsyncMock()

    with (
        patch(
            "src.services.copilot_polling.state_validation.find_agent_label", return_value="planner"
        ),
        patch(_GPS, mock_github),
    ):
        changed, corrections = await validate_pipeline_labels(
            access_token="tok",
            owner="octo",
            repo="repo",
            issue_number=42,
            labels=[{"name": "agent:planner"}],
            tracking_steps=[
                _step("reviewer", "⏳ Pending"),
                _step("builder", "🔄 Active"),
                _step("planner", "⏳ Pending"),
            ],
            pipeline_config_name="ignored",
        )

    assert changed is True
    assert "agent:planner" in corrections[0]
    assert "agent:builder" in corrections[0]


@pytest.mark.asyncio
async def test_first_pending_step_is_used_when_no_active_step_exists():
    mock_github = AsyncMock()

    with (
        patch("src.services.copilot_polling.state_validation.find_agent_label", return_value=None),
        patch(_GPS, mock_github),
    ):
        changed, corrections = await validate_pipeline_labels(
            access_token="tok",
            owner="octo",
            repo="repo",
            issue_number=42,
            labels=[],
            tracking_steps=[
                _step("builder", "invalid-state"),
                _step("planner", "⏳ Pending"),
                _step("reviewer", "⏳ Pending"),
            ],
        )

    assert changed is True
    assert corrections == ["Added missing agent:planner label to #42"]


@pytest.mark.asyncio
async def test_invalid_state_combinations_remove_stale_label():
    mock_github = AsyncMock()

    with (
        patch(
            "src.services.copilot_polling.state_validation.find_agent_label", return_value="builder"
        ),
        patch(_GPS, mock_github),
    ):
        changed, corrections = await validate_pipeline_labels(
            access_token="tok",
            owner="octo",
            repo="repo",
            issue_number=42,
            labels=[{"name": "agent:builder"}],
            tracking_steps=[
                _step("builder", "waiting"),
                _step("reviewer", "unknown"),
            ],
        )

    assert changed is True
    assert corrections == [
        "Removed stale agent:builder label from #42 (no active agent in tracking table)"
    ]
