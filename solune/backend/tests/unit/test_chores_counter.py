"""Unit tests for the chores counter (count-based trigger evaluation)."""

from __future__ import annotations

from datetime import UTC, datetime

from src.models.chores import Chore
from src.services.chores.counter import evaluate_count_trigger


def _make_chore(**overrides) -> Chore:
    """Create a Chore instance with sensible defaults."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    defaults = {
        "id": "chore-1",
        "project_id": "PVT_1",
        "name": "Test",
        "template_path": ".github/ISSUE_TEMPLATE/test.md",
        "template_content": "# Test",
        "schedule_type": "count",
        "schedule_value": 5,
        "status": "active",
        "last_triggered_at": None,
        "last_triggered_count": 0,
        "current_issue_number": None,
        "current_issue_node_id": None,
        "pr_number": None,
        "pr_url": None,
        "tracking_issue_number": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    return Chore(**defaults)


class TestEvaluateCountTrigger:
    """Tests for count-based trigger evaluation."""

    def test_triggers_when_threshold_met(self):
        """Trigger fires when issue count meets the threshold."""
        chore = _make_chore(schedule_value=5, last_triggered_count=0)
        assert evaluate_count_trigger(chore, current_count=5) is True

    def test_triggers_when_threshold_exceeded(self):
        """Trigger fires when issue count exceeds the threshold."""
        chore = _make_chore(schedule_value=5, last_triggered_count=0)
        assert evaluate_count_trigger(chore, current_count=8) is True

    def test_skips_when_below_threshold(self):
        """Trigger does not fire when below threshold."""
        chore = _make_chore(schedule_value=5, last_triggered_count=0)
        assert evaluate_count_trigger(chore, current_count=3) is False

    def test_accounts_for_last_triggered_count(self):
        """Issues since last trigger are counted, not total."""
        chore = _make_chore(schedule_value=5, last_triggered_count=10)
        # 14 total - 10 since last = 4, below 5 threshold
        assert evaluate_count_trigger(chore, current_count=14) is False
        # 15 total - 10 = 5, meets threshold
        assert evaluate_count_trigger(chore, current_count=15) is True

    def test_non_count_schedule_returns_false(self):
        """Time-based schedule returns False from count evaluator."""
        chore = _make_chore(schedule_type="time", schedule_value=7)
        assert evaluate_count_trigger(chore, current_count=100) is False

    def test_no_schedule_value_returns_false(self):
        """Chore with no schedule_value returns False."""
        chore = _make_chore(schedule_type="count", schedule_value=None)
        assert evaluate_count_trigger(chore, current_count=100) is False
