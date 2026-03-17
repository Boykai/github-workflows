"""Unit tests for copilot_polling.state module — dataclass, constants, and globals."""

from datetime import UTC, datetime

from src.services.copilot_polling.state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS,
    MAX_POLL_INTERVAL_SECONDS,
    POST_ACTION_DELAY_SECONDS,
    RATE_LIMIT_PAUSE_THRESHOLD,
    RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD,
    RATE_LIMIT_SLOW_THRESHOLD,
    RECOVERY_COOLDOWN_SECONDS,
    PollingState,
    _claimed_child_prs,
    _consecutive_idle_polls,
    _copilot_review_first_detected,
    _copilot_review_requested_at,
    _pending_agent_assignments,
    _polling_state,
    _polling_task,
    _posted_agent_outputs,
    _processed_issue_prs,
    _recovery_last_attempt,
    _system_marked_ready_prs,
)
from src.utils import BoundedDict, BoundedSet


class TestPollingStateDataclass:
    """PollingState dataclass creation and defaults."""

    def test_default_values(self):
        state = PollingState()
        assert state.is_running is False
        assert state.last_poll_time is None
        assert state.poll_count == 0
        assert state.errors_count == 0
        assert state.last_error is None
        assert isinstance(state.processed_issues, BoundedDict)

    def test_custom_values(self):
        now = datetime.now(UTC)
        state = PollingState(
            is_running=True,
            last_poll_time=now,
            poll_count=5,
            errors_count=2,
            last_error="timeout",
        )
        assert state.is_running is True
        assert state.last_poll_time == now
        assert state.poll_count == 5
        assert state.errors_count == 2
        assert state.last_error == "timeout"

    def test_processed_issues_default_is_bounded_dict(self):
        state = PollingState()
        assert isinstance(state.processed_issues, BoundedDict)

    def test_each_instance_gets_own_processed_issues(self):
        s1 = PollingState()
        s2 = PollingState()
        s1.processed_issues[1] = datetime.now(UTC)
        assert 1 not in s2.processed_issues


class TestConstants:
    """Verify constants have documented expected values."""

    def test_assignment_grace_period(self):
        assert ASSIGNMENT_GRACE_PERIOD_SECONDS == 120

    def test_rate_limit_pause_threshold(self):
        assert RATE_LIMIT_PAUSE_THRESHOLD == 50

    def test_rate_limit_slow_threshold(self):
        assert RATE_LIMIT_SLOW_THRESHOLD == 200

    def test_rate_limit_skip_expensive_threshold(self):
        assert RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD == 100

    def test_max_poll_interval(self):
        assert MAX_POLL_INTERVAL_SECONDS == 300

    def test_recovery_cooldown(self):
        assert RECOVERY_COOLDOWN_SECONDS == 300

    def test_post_action_delay(self):
        assert POST_ACTION_DELAY_SECONDS == 2.0

    def test_copilot_review_confirmation_delay(self):
        assert COPILOT_REVIEW_CONFIRMATION_DELAY_SECONDS == 30.0


class TestGlobalInstances:
    """Module-level singletons are initialised with the correct types."""

    def test_polling_state_is_instance(self):
        assert isinstance(_polling_state, PollingState)

    def test_polling_task_initially_none(self):
        assert _polling_task is None

    def test_processed_issue_prs_is_bounded_set(self):
        assert isinstance(_processed_issue_prs, BoundedSet)

    def test_posted_agent_outputs_is_bounded_set(self):
        assert isinstance(_posted_agent_outputs, BoundedSet)

    def test_claimed_child_prs_is_bounded_set(self):
        assert isinstance(_claimed_child_prs, BoundedSet)

    def test_pending_agent_assignments_is_bounded_dict(self):
        assert isinstance(_pending_agent_assignments, BoundedDict)

    def test_system_marked_ready_prs_is_bounded_set(self):
        assert isinstance(_system_marked_ready_prs, BoundedSet)

    def test_copilot_review_first_detected_is_bounded_dict(self):
        assert isinstance(_copilot_review_first_detected, BoundedDict)

    def test_copilot_review_requested_at_is_bounded_dict(self):
        assert isinstance(_copilot_review_requested_at, BoundedDict)

    def test_recovery_last_attempt_is_bounded_dict(self):
        assert isinstance(_recovery_last_attempt, BoundedDict)

    def test_consecutive_idle_polls_starts_at_zero(self):
        assert _consecutive_idle_polls == 0
