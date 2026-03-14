"""Tests for polling_loop.py — PollStep, stop_polling, get_polling_status (T103)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from src.services.copilot_polling.polling_loop import (
    POLL_STEPS,
    PollStep,
    get_polling_status,
    stop_polling,
)


class TestPollStep:
    """PollStep is a frozen dataclass describing a single polling step."""

    def test_default_not_expensive(self):
        async def noop():
            return []

        step = PollStep(name="test", execute=noop)
        assert step.name == "test"
        assert step.is_expensive is False

    def test_expensive(self):
        async def noop():
            return []

        step = PollStep(name="test", execute=noop, is_expensive=True)
        assert step.is_expensive is True

    def test_frozen(self):
        async def noop():
            return []

        step = PollStep(name="test", execute=noop)
        try:
            step.name = "other"  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except AttributeError:
            pass


class TestPollSteps:
    """POLL_STEPS is the ordered list of polling steps."""

    def test_has_expected_count(self):
        assert len(POLL_STEPS) == 7

    def test_all_are_poll_step_instances(self):
        for step in POLL_STEPS:
            assert isinstance(step, PollStep)

    def test_expensive_steps(self):
        expensive = [s.name for s in POLL_STEPS if s.is_expensive]
        assert "Step 0: agent outputs" in expensive
        assert "Step 5: stalled recovery" in expensive

    def test_all_steps_have_execute_callable(self):
        for step in POLL_STEPS:
            assert callable(step.execute)


class TestStopPolling:
    """stop_polling() sets is_running=False and cancels any active task."""

    def test_sets_is_running_false(self):
        with (
            patch("src.services.copilot_polling.polling_loop._polling_state") as mock_state,
            patch("src.services.copilot_polling.polling_loop._cp") as mock_cp,
        ):
            mock_state.is_running = True
            mock_cp._polling_task = None
            stop_polling()
            assert mock_state.is_running is False

    def test_cancels_active_task(self):
        mock_task = MagicMock()
        mock_task.done.return_value = False
        with (
            patch("src.services.copilot_polling.polling_loop._polling_state") as mock_state,
            patch("src.services.copilot_polling.polling_loop._cp") as mock_cp,
        ):
            mock_cp._polling_task = mock_task
            stop_polling()
            mock_task.cancel.assert_called_once()
            assert mock_state.is_running is False

    def test_skips_cancel_when_task_done(self):
        mock_task = MagicMock()
        mock_task.done.return_value = True
        with (
            patch("src.services.copilot_polling.polling_loop._polling_state") as mock_state,
            patch("src.services.copilot_polling.polling_loop._cp") as mock_cp,
        ):
            mock_cp._polling_task = mock_task
            stop_polling()
            mock_task.cancel.assert_not_called()
            assert mock_state.is_running is False


class TestGetPollingStatus:
    """get_polling_status() returns a dict of current polling state."""

    def test_default_state(self):
        with (
            patch("src.services.copilot_polling.polling_loop._polling_state") as mock_state,
            patch(
                "src.services.copilot_polling.polling_loop._processed_issue_prs",
                new=set(),
            ),
            patch("src.services.copilot_polling.polling_loop._cp") as mock_cp,
        ):
            mock_state.is_running = False
            mock_state.last_poll_time = None
            mock_state.poll_count = 0
            mock_state.errors_count = 0
            mock_state.last_error = None
            mock_cp.github_projects_service.get_last_rate_limit.return_value = None

            status = get_polling_status()
            assert status["is_running"] is False
            assert status["last_poll_time"] is None
            assert status["poll_count"] == 0
            assert status["rate_limit"] is None

    def test_with_rate_limit_info(self):
        with (
            patch("src.services.copilot_polling.polling_loop._polling_state") as mock_state,
            patch(
                "src.services.copilot_polling.polling_loop._processed_issue_prs",
                new={"1:2", "3:4"},
            ),
            patch("src.services.copilot_polling.polling_loop._cp") as mock_cp,
        ):
            mock_state.is_running = True
            mock_state.last_poll_time = datetime(2024, 6, 15, 10, 0, tzinfo=UTC)
            mock_state.poll_count = 5
            mock_state.errors_count = 1
            mock_state.last_error = "timeout"
            mock_cp.github_projects_service.get_last_rate_limit.return_value = {
                "limit": 5000,
                "remaining": 4500,
                "used": 500,
                "reset_at": 1718445600,
            }

            status = get_polling_status()
            assert status["is_running"] is True
            assert status["poll_count"] == 5
            assert status["errors_count"] == 1
            assert status["last_error"] == "timeout"
            assert status["processed_issues_count"] == 2
            assert status["rate_limit"]["remaining"] == 4500
