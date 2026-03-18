"""Tests for recovery.py — self-healing stalled pipeline detection.

Covers _should_skip_recovery, _validate_and_reconcile_tracking_table,
_detect_stalled_issue, and _check_copilot_session_health.
"""

from __future__ import annotations

from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

_CP = "src.services.copilot_polling"
_REC = f"{_CP}.recovery"

# Patch targets for module-level state imported by recovery.py
_RECOVERY_LAST = f"{_REC}._recovery_last_attempt"
_RECOVERY_COOLDOWN = f"{_REC}.RECOVERY_COOLDOWN_SECONDS"


def _utcnow():
    return datetime.now(UTC)


# ── _should_skip_recovery ─────────────────────────────────────────


class TestShouldSkipRecovery:
    async def test_returns_false_when_no_prior_attempt(self):
        with patch(_RECOVERY_LAST, {}):
            from src.services.copilot_polling.recovery import _should_skip_recovery

            result = await _should_skip_recovery(42, "o", "r", _utcnow())
        assert result is False

    async def test_returns_true_when_within_cooldown(self):
        now = _utcnow()
        recent = now - timedelta(seconds=10)
        with ExitStack() as stack:
            stack.enter_context(patch(_RECOVERY_LAST, {42: recent}))
            stack.enter_context(patch(_RECOVERY_COOLDOWN, 300))
            from src.services.copilot_polling.recovery import _should_skip_recovery

            result = await _should_skip_recovery(42, "o", "r", now)
        assert result is True

    async def test_returns_false_when_cooldown_expired(self):
        now = _utcnow()
        old = now - timedelta(seconds=600)
        with ExitStack() as stack:
            stack.enter_context(patch(_RECOVERY_LAST, {42: old}))
            stack.enter_context(patch(_RECOVERY_COOLDOWN, 300))
            from src.services.copilot_polling.recovery import _should_skip_recovery

            result = await _should_skip_recovery(42, "o", "r", now)
        assert result is False


# ── _validate_and_reconcile_tracking_table ─────────────────────────


class TestValidateAndReconcileTrackingTable:
    """Tests for tracking table reconciliation against GitHub ground truth."""

    def _make_step(self, agent_name: str, state: str):
        return SimpleNamespace(agent_name=agent_name, state=state)

    async def test_no_corrections_when_table_matches_github(self):
        """When all steps match GitHub, returns unchanged body and False."""
        step = self._make_step("implement", "✅ Done")

        with ExitStack() as stack:
            check_done = AsyncMock(return_value=True)
            stack.enter_context(patch(f"{_CP}._check_agent_done_on_sub_or_parent", check_done))
            stack.enter_context(patch(f"{_CP}.github_projects_service", MagicMock()))

            from src.services.copilot_polling.recovery import (
                _validate_and_reconcile_tracking_table,
            )

            body, _steps, corrected = await _validate_and_reconcile_tracking_table(
                "tok", "o", "r", 1, "original body", [step], None
            )

        assert body == "original body"
        assert corrected is False

    async def test_corrects_active_step_to_done_when_github_says_done(self):
        """When GitHub shows Done but table shows Active, corrects to Done."""
        step = self._make_step("implement", "🔄 Active")

        rebuilt_body = "rebuilt body with done"

        with ExitStack() as stack:
            check_done = AsyncMock(return_value=True)
            stack.enter_context(patch(f"{_CP}._check_agent_done_on_sub_or_parent", check_done))
            stack.enter_context(
                patch(
                    "src.services.agent_tracking.replace_tracking_section",
                    return_value=rebuilt_body,
                )
            )
            mock_gps = MagicMock()
            mock_gps.update_issue_body = AsyncMock()
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))

            from src.services.copilot_polling.recovery import (
                _validate_and_reconcile_tracking_table,
            )

            body, _steps, corrected = await _validate_and_reconcile_tracking_table(
                "tok", "o", "r", 1, "old body", [step], None
            )

        assert corrected is True
        assert body == rebuilt_body
        mock_gps.update_issue_body.assert_awaited_once()

    async def test_returns_corrected_state_even_when_api_push_fails(self):
        """When GitHub body update fails, in-memory state is still corrected."""
        step = self._make_step("implement", "🔄 Active")

        rebuilt_body = "rebuilt"

        with ExitStack() as stack:
            check_done = AsyncMock(return_value=True)
            stack.enter_context(patch(f"{_CP}._check_agent_done_on_sub_or_parent", check_done))
            stack.enter_context(
                patch(
                    "src.services.agent_tracking.replace_tracking_section",
                    return_value=rebuilt_body,
                )
            )
            mock_gps = MagicMock()
            mock_gps.update_issue_body = AsyncMock(side_effect=RuntimeError("API error"))
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))

            from src.services.copilot_polling.recovery import (
                _validate_and_reconcile_tracking_table,
            )

            body, _steps, corrected = await _validate_and_reconcile_tracking_table(
                "tok", "o", "r", 1, "old body", [step], None
            )

        # Still reports corrected=True and returns rebuilt body
        assert corrected is True
        assert body == rebuilt_body

    async def test_leaves_pending_step_unchanged_when_github_not_done(self):
        """Steps that GitHub says are not done should not be corrected."""
        step = self._make_step("implement", "⏳ Pending")

        with ExitStack() as stack:
            check_done = AsyncMock(return_value=False)
            stack.enter_context(patch(f"{_CP}._check_agent_done_on_sub_or_parent", check_done))
            stack.enter_context(patch(f"{_CP}.github_projects_service", MagicMock()))

            from src.services.copilot_polling.recovery import (
                _validate_and_reconcile_tracking_table,
            )

            _, _, corrected = await _validate_and_reconcile_tracking_table(
                "tok", "o", "r", 1, "body", [step], None
            )

        assert corrected is False


# ── _detect_stalled_issue ──────────────────────────────────────────


class TestDetectStalledIssue:
    """Tests for _detect_stalled_issue — checks if a coding agent is stalled."""

    def _make_pipeline(self, agent_subs=None):
        return SimpleNamespace(agent_sub_issues=agent_subs or {})

    async def test_copilot_assigned_on_sub_issue(self):
        """When copilot is assigned to sub-issue, returns True for copilot_assigned."""
        mock_gps = MagicMock()
        mock_gps.is_copilot_assigned_to_issue = AsyncMock(return_value=True)
        mock_gps.get_linked_pull_requests = AsyncMock(return_value=[])

        pipeline = self._make_pipeline({"agent": {"number": 99}})

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))
            stack.enter_context(patch(f"{_REC}._get_sub_issue_number", return_value=99))
            stack.enter_context(patch(f"{_CP}.get_issue_main_branch", return_value=None))

            from src.services.copilot_polling.recovery import _detect_stalled_issue

            assigned, has_wip, _wip_pr = await _detect_stalled_issue(
                "tok", "o", "r", 42, "agent", pipeline
            )

        assert assigned is True
        assert has_wip is False

    async def test_copilot_not_assigned_anywhere(self):
        """When copilot not assigned to sub-issue or parent, returns False."""
        mock_gps = MagicMock()
        mock_gps.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_gps.get_linked_pull_requests = AsyncMock(return_value=[])

        pipeline = self._make_pipeline()

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))
            # sub-issue same as parent → skip sub-issue check
            stack.enter_context(patch(f"{_REC}._get_sub_issue_number", return_value=42))
            stack.enter_context(patch(f"{_CP}.get_issue_main_branch", return_value=None))

            from src.services.copilot_polling.recovery import _detect_stalled_issue

            assigned, has_wip, _wip_pr = await _detect_stalled_issue(
                "tok", "o", "r", 42, "agent", pipeline
            )

        assert assigned is False
        assert has_wip is False

    async def test_detects_wip_pr_when_no_main_branch(self):
        """When no main branch info, any open copilot PR counts as WIP."""
        mock_gps = MagicMock()
        mock_gps.is_copilot_assigned_to_issue = AsyncMock(return_value=True)
        mock_gps.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 100, "state": "OPEN", "author": "copilot[bot]"},
            ]
        )
        mock_gps.get_pull_request = AsyncMock(return_value={"is_draft": True, "base_ref": "main"})

        pipeline = self._make_pipeline()

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))
            stack.enter_context(patch(f"{_REC}._get_sub_issue_number", return_value=42))
            stack.enter_context(patch(f"{_CP}.get_issue_main_branch", return_value=None))

            from src.services.copilot_polling.recovery import _detect_stalled_issue

            assigned, has_wip, wip_pr = await _detect_stalled_issue(
                "tok", "o", "r", 42, "agent", pipeline
            )

        assert assigned is True
        assert has_wip is True
        assert wip_pr == 100

    async def test_skips_closed_prs(self):
        """Closed PRs should not count as WIP."""
        mock_gps = MagicMock()
        mock_gps.is_copilot_assigned_to_issue = AsyncMock(return_value=False)
        mock_gps.get_linked_pull_requests = AsyncMock(
            return_value=[
                {"number": 100, "state": "CLOSED", "author": "copilot[bot]"},
            ]
        )

        pipeline = self._make_pipeline()

        with ExitStack() as stack:
            stack.enter_context(patch(f"{_CP}.github_projects_service", mock_gps))
            stack.enter_context(patch(f"{_REC}._get_sub_issue_number", return_value=42))
            stack.enter_context(patch(f"{_CP}.get_issue_main_branch", return_value=None))

            from src.services.copilot_polling.recovery import _detect_stalled_issue

            _assigned, has_wip, wip_pr = await _detect_stalled_issue(
                "tok", "o", "r", 42, "agent", pipeline
            )

        assert has_wip is False
        assert wip_pr is None


# ── _check_copilot_session_health ──────────────────────────────────


class TestCheckCopilotSessionHealth:
    async def test_returns_true_when_no_wip_pr(self):
        from src.services.copilot_polling.recovery import _check_copilot_session_health

        result = await _check_copilot_session_health("tok", "o", "r", 42, "agent", None)
        assert result is True

    async def test_returns_true_when_session_not_errored(self):
        mock_gps = MagicMock()
        mock_gps.check_copilot_session_error = AsyncMock(return_value=False)

        with patch(f"{_CP}.github_projects_service", mock_gps):
            from src.services.copilot_polling.recovery import _check_copilot_session_health

            result = await _check_copilot_session_health("tok", "o", "r", 42, "agent", 100)
        assert result is True

    async def test_returns_false_when_session_errored(self):
        mock_gps = MagicMock()
        mock_gps.check_copilot_session_error = AsyncMock(return_value=True)

        with patch(f"{_CP}.github_projects_service", mock_gps):
            from src.services.copilot_polling.recovery import _check_copilot_session_health

            result = await _check_copilot_session_health("tok", "o", "r", 42, "agent", 100)
        assert result is False

    async def test_returns_true_on_api_exception(self):
        """On exception, assume healthy (optimistic fallback)."""
        mock_gps = MagicMock()
        mock_gps.check_copilot_session_error = AsyncMock(side_effect=RuntimeError("err"))

        with patch(f"{_CP}.github_projects_service", mock_gps):
            from src.services.copilot_polling.recovery import _check_copilot_session_health

            result = await _check_copilot_session_health("tok", "o", "r", 42, "agent", 100)
        assert result is True
