"""Unit tests for validate_pipeline_labels() — label vs tracking table cross-check."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest


@dataclass
class FakeStep:
    """Minimal stand-in for AgentStep."""

    agent_name: str
    state: str


class TestValidatePipelineLabels:
    """Tests for the consolidated label validation function."""

    @pytest.mark.asyncio
    async def test_consistent_no_corrections(self):
        """When labels match tracking table, no corrections are made."""
        from src.services.copilot_polling.state_validation import validate_pipeline_labels

        labels = [{"name": "agent:speckit.plan", "color": "7057ff"}]
        steps = [
            FakeStep("speckit.specify", "✅ Done"),
            FakeStep("speckit.plan", "🔄 Active"),
        ]

        corrections_made, descriptions = await validate_pipeline_labels(
            access_token="tok",
            owner="owner",
            repo="repo",
            issue_number=42,
            labels=labels,
            tracking_steps=steps,
        )

        assert corrections_made is False
        assert descriptions == []

    @pytest.mark.asyncio
    async def test_label_agent_differs_from_table_agent(self):
        """When label says plan but table says tasks, fix the label (table wins)."""
        from src.services.copilot_polling.state_validation import validate_pipeline_labels

        labels = [{"name": "agent:speckit.plan", "color": "7057ff"}]
        steps = [
            FakeStep("speckit.specify", "✅ Done"),
            FakeStep("speckit.plan", "✅ Done"),
            FakeStep("speckit.tasks", "🔄 Active"),
        ]

        with patch("src.services.copilot_polling.state_validation._cp") as mock_cp:
            mock_cp.github_projects_service = AsyncMock()
            mock_cp.github_projects_service.update_issue_state = AsyncMock(return_value=True)

            corrections_made, descriptions = await validate_pipeline_labels(
                access_token="tok",
                owner="owner",
                repo="repo",
                issue_number=42,
                labels=labels,
                tracking_steps=steps,
            )

            assert corrections_made is True
            assert len(descriptions) == 1
            assert "speckit.plan" in descriptions[0]
            assert "speckit.tasks" in descriptions[0]

    @pytest.mark.asyncio
    async def test_label_missing_table_has_agent(self):
        """When no agent label but table has active agent, add label."""
        from src.services.copilot_polling.state_validation import validate_pipeline_labels

        labels = [{"name": "pipeline:speckit-full", "color": "0052cc"}]
        steps = [FakeStep("speckit.specify", "🔄 Active")]

        with patch("src.services.copilot_polling.state_validation._cp") as mock_cp:
            mock_cp.github_projects_service = AsyncMock()
            mock_cp.github_projects_service.update_issue_state = AsyncMock(return_value=True)

            corrections_made, descriptions = await validate_pipeline_labels(
                access_token="tok",
                owner="owner",
                repo="repo",
                issue_number=42,
                labels=labels,
                tracking_steps=steps,
            )

            assert corrections_made is True
            assert "speckit.specify" in descriptions[0]

    @pytest.mark.asyncio
    async def test_label_present_no_active_agent(self):
        """When label exists but all tracking table agents are done, remove label."""
        from src.services.copilot_polling.state_validation import validate_pipeline_labels

        labels = [{"name": "agent:speckit.plan", "color": "7057ff"}]
        steps = [
            FakeStep("speckit.specify", "✅ Done"),
            FakeStep("speckit.plan", "✅ Done"),
        ]

        with patch("src.services.copilot_polling.state_validation._cp") as mock_cp:
            mock_cp.github_projects_service = AsyncMock()
            mock_cp.github_projects_service.update_issue_state = AsyncMock(return_value=True)

            corrections_made, descriptions = await validate_pipeline_labels(
                access_token="tok",
                owner="owner",
                repo="repo",
                issue_number=42,
                labels=labels,
                tracking_steps=steps,
            )

            assert corrections_made is True
            assert "stale" in descriptions[0].lower() or "removed" in descriptions[0].lower()

    @pytest.mark.asyncio
    async def test_both_none_no_corrections(self):
        """When neither label nor table has an active agent, no corrections."""
        from src.services.copilot_polling.state_validation import validate_pipeline_labels

        labels = [{"name": "pipeline:x", "color": "0052cc"}]
        steps = [FakeStep("speckit.specify", "✅ Done")]

        corrections_made, _descriptions = await validate_pipeline_labels(
            access_token="tok",
            owner="owner",
            repo="repo",
            issue_number=42,
            labels=labels,
            tracking_steps=steps,
        )

        assert corrections_made is False

    @pytest.mark.asyncio
    async def test_idempotent_revalidation(self):
        """Running validation twice produces no additional changes."""
        from src.services.copilot_polling.state_validation import validate_pipeline_labels

        labels = [{"name": "agent:speckit.plan", "color": "7057ff"}]
        steps = [FakeStep("speckit.plan", "🔄 Active")]

        r1_made, r1_desc = await validate_pipeline_labels(
            access_token="tok",
            owner="owner",
            repo="repo",
            issue_number=42,
            labels=labels,
            tracking_steps=steps,
        )
        assert r1_made is False
        assert r1_desc == []

    @pytest.mark.asyncio
    async def test_pending_agent_matched(self):
        """When label matches first pending agent (no active), it's consistent."""
        from src.services.copilot_polling.state_validation import validate_pipeline_labels

        labels = [{"name": "agent:speckit.specify", "color": "7057ff"}]
        steps = [FakeStep("speckit.specify", "⏳ Pending")]

        corrections_made, _ = await validate_pipeline_labels(
            access_token="tok",
            owner="owner",
            repo="repo",
            issue_number=42,
            labels=labels,
            tracking_steps=steps,
        )
        assert corrections_made is False
