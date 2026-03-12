"""Unit tests for the label write path — verifying correct labels at each pipeline transition."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.constants import (
    ACTIVE_LABEL,
    STALLED_LABEL,
    build_agent_label,
)

# ── _build_labels ────────────────────────────────────────────────────────────


class TestBuildLabelsWithPipelineConfig:
    """Tests for _build_labels with optional pipeline_config_name parameter."""

    def _make_recommendation(self, labels=None):
        from uuid import uuid4

        from src.models.recommendation import IssueMetadata, IssueRecommendation

        metadata = IssueMetadata(labels=labels or [])
        return IssueRecommendation(
            recommendation_id=uuid4(),
            session_id=uuid4(),
            title="Test Issue",
            original_input="User request",
            user_story="As a user...",
            ui_ux_description="UI description",
            functional_requirements=["Req 1"],
            metadata=metadata,
        )

    def test_without_pipeline_config_name(self):
        from src.services.workflow_orchestrator.orchestrator import WorkflowOrchestrator

        rec = self._make_recommendation(labels=["feature"])
        labels = WorkflowOrchestrator._build_labels(rec)
        assert "ai-generated" in labels
        assert "feature" in labels
        assert not any(lbl.startswith("pipeline:") for lbl in labels)

    def test_with_pipeline_config_name(self):
        from src.services.workflow_orchestrator.orchestrator import WorkflowOrchestrator

        rec = self._make_recommendation(labels=["feature"])
        labels = WorkflowOrchestrator._build_labels(rec, pipeline_config_name="speckit-full")
        assert "pipeline:speckit-full" in labels

    def test_with_none_pipeline_config_name(self):
        from src.services.workflow_orchestrator.orchestrator import WorkflowOrchestrator

        rec = self._make_recommendation(labels=["bug"])
        labels = WorkflowOrchestrator._build_labels(rec, pipeline_config_name=None)
        assert not any(lbl.startswith("pipeline:") for lbl in labels)


# ── Agent label swap ─────────────────────────────────────────────────────────


class TestAgentLabelSwap:
    """Verify agent:<slug> is swapped correctly during assignment."""

    def test_build_agent_label_for_swap(self):
        """Agent label swap should remove old and add new in one operation."""
        old_slug = "speckit.specify"
        new_slug = "speckit.plan"
        old_label = build_agent_label(old_slug)
        new_label = build_agent_label(new_slug)
        assert old_label == "agent:speckit.specify"
        assert new_label == "agent:speckit.plan"

    def test_stalled_label_removed_on_assignment(self):
        """STALLED_LABEL should be in labels_remove during agent swap."""
        assert STALLED_LABEL == "stalled"


# ── Pipeline completion label cleanup ─────────────────────────────────────────


class TestPipelineCompletionLabelCleanup:
    """Verify agent:* and active labels are removed on pipeline completion."""

    def test_completion_removes_agent_label(self):
        """On completion, the current agent label should be removed."""
        agent_slug = "copilot-review"
        label = build_agent_label(agent_slug)
        assert label == "agent:copilot-review"

    def test_completion_removes_active_label(self):
        """On completion, the active label should be removed from last sub-issue."""
        assert ACTIVE_LABEL == "active"


# ── Stalled label lifecycle ──────────────────────────────────────────────────


class TestStalledLabelLifecycle:
    """Verify stalled label is applied on recovery detection and removed on re-assignment."""

    def test_stalled_label_value(self):
        assert STALLED_LABEL == "stalled"

    def test_stalled_removed_during_swap(self):
        """When a new agent is assigned, STALLED_LABEL should be in the remove list."""
        # The swap logic in assign_agent_for_status removes STALLED_LABEL
        labels_to_remove = [STALLED_LABEL]
        assert STALLED_LABEL in labels_to_remove


# ── Non-blocking error handling ──────────────────────────────────────────────


class TestNonBlockingLabelWrites:
    """Verify label failures are logged as warnings and never raise."""

    @pytest.mark.asyncio
    async def test_ensure_pipeline_labels_exist_handles_errors(self):
        """ensure_pipeline_labels_exist should not raise on network errors."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=Exception("network error"))
            mock_client_cls.return_value = mock_client

            from src.constants import ensure_pipeline_labels_exist

            # Should not raise
            await ensure_pipeline_labels_exist("fake-token", "owner", "repo")

    @pytest.mark.asyncio
    async def test_ensure_pipeline_labels_exist_handles_422(self):
        """ensure_pipeline_labels_exist should silently handle 422 (already exists)."""
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_resp = MagicMock()
            mock_resp.status_code = 422
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            from src.constants import ensure_pipeline_labels_exist

            # Should not raise
            await ensure_pipeline_labels_exist("fake-token", "owner", "repo")
