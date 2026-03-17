"""Unit tests for copilot_polling.state_validation — label vs tracking table reconciliation."""

from dataclasses import dataclass
from unittest.mock import AsyncMock, patch

import pytest

from src.services.agent_tracking import STATE_ACTIVE, STATE_PENDING


# Lightweight stand-in for AgentStep to avoid coupling to its full definition.
@dataclass
class _FakeStep:
    agent_name: str
    state: str


# Common call kwargs shared by all tests.
_CALL_KWARGS = {
    "access_token": "tok",
    "owner": "o",
    "repo": "r",
    "issue_number": 42,
}


class TestValidatePipelineLabels:
    """Tests for validate_pipeline_labels()."""

    @pytest.fixture(autouse=True)
    def _patch_service(self):
        """Patch the GitHub projects service used by state_validation."""
        with patch("src.services.copilot_polling.github_projects_service") as mock_svc:
            mock_svc.update_issue_state = AsyncMock()
            self.mock_svc = mock_svc
            yield

    async def _call(self, labels, tracking_steps, pipeline_config_name=None):
        # Import inside method so the patch is active.
        from src.services.copilot_polling.state_validation import (
            validate_pipeline_labels,
        )

        return await validate_pipeline_labels(
            **_CALL_KWARGS,
            labels=labels,
            tracking_steps=tracking_steps,
            pipeline_config_name=pipeline_config_name,
        )

    # ── Consistent: no corrections ──────────────────────────────────────

    @pytest.mark.asyncio
    async def test_both_none_no_correction(self):
        """No agent label, no active step → consistent → no-op."""
        ok, msgs = await self._call(labels=[], tracking_steps=[])
        assert ok is False
        assert msgs == []
        self.mock_svc.update_issue_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_both_agree_no_correction(self):
        """Label and table point to the same agent → no-op."""
        labels = [{"name": "agent:speckit.specify"}]
        steps = [_FakeStep(agent_name="speckit.specify", state=STATE_ACTIVE)]
        ok, msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is False
        assert msgs == []

    # ── Disagree: table wins ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_label_and_table_disagree_swaps_label(self):
        """Label says agent-A, table says agent-B → swap label to B."""
        labels = [{"name": "agent:speckit.specify"}]
        steps = [_FakeStep(agent_name="speckit.plan", state=STATE_ACTIVE)]
        ok, msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is True
        assert len(msgs) == 1
        assert "speckit.plan" in msgs[0]
        self.mock_svc.update_issue_state.assert_awaited_once()
        call_kw = self.mock_svc.update_issue_state.call_args.kwargs
        assert "agent:speckit.plan" in call_kw["labels_add"]
        assert "agent:speckit.specify" in call_kw["labels_remove"]

    # ── Label missing, table has agent → add label ──────────────────────

    @pytest.mark.asyncio
    async def test_missing_label_adds_from_table(self):
        """No agent label but table has active agent → add label."""
        labels = []
        steps = [_FakeStep(agent_name="speckit.tasks", state=STATE_ACTIVE)]
        ok, msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is True
        assert any("speckit.tasks" in m for m in msgs)
        call_kw = self.mock_svc.update_issue_state.call_args.kwargs
        assert "agent:speckit.tasks" in call_kw["labels_add"]

    @pytest.mark.asyncio
    async def test_missing_label_uses_pending_when_no_active(self):
        """No active step but a pending step exists → add pending agent label."""
        labels = []
        steps = [_FakeStep(agent_name="speckit.plan", state=STATE_PENDING)]
        ok, _msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is True
        call_kw = self.mock_svc.update_issue_state.call_args.kwargs
        assert "agent:speckit.plan" in call_kw["labels_add"]

    # ── Label present, table empty → remove label ───────────────────────

    @pytest.mark.asyncio
    async def test_stale_label_removed_when_no_active_agent(self):
        """Agent label present but no active/pending step → remove label."""
        labels = [{"name": "agent:speckit.specify"}]
        steps: list = []
        ok, msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is True
        assert any("Removed" in m for m in msgs)
        call_kw = self.mock_svc.update_issue_state.call_args.kwargs
        assert "agent:speckit.specify" in call_kw["labels_remove"]

    # ── Error handling ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_service_error_still_returns_correction_message(self):
        """If the REST call to fix labels raises, error is captured in msgs."""
        self.mock_svc.update_issue_state.side_effect = RuntimeError("API boom")
        labels = [{"name": "agent:speckit.specify"}]
        steps: list = []
        ok, msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is True
        assert any("Failed" in m for m in msgs)

    @pytest.mark.asyncio
    async def test_swap_error_captured(self):
        """Error during label swap is recorded."""
        self.mock_svc.update_issue_state.side_effect = RuntimeError("oops")
        labels = [{"name": "agent:speckit.specify"}]
        steps = [_FakeStep(agent_name="speckit.plan", state=STATE_ACTIVE)]
        ok, msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is True
        assert any("Failed" in m for m in msgs)

    @pytest.mark.asyncio
    async def test_add_label_error_captured(self):
        """Error during label add is recorded."""
        self.mock_svc.update_issue_state.side_effect = RuntimeError("oops")
        labels = []
        steps = [_FakeStep(agent_name="speckit.plan", state=STATE_ACTIVE)]
        ok, msgs = await self._call(labels=labels, tracking_steps=steps)
        assert ok is True
        assert any("Failed" in m for m in msgs)
