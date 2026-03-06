"""Unit tests for the chores scheduler (time-based trigger evaluation)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.models.chores import Chore
from src.services.chores.scheduler import evaluate_time_trigger


def _make_chore(**overrides) -> Chore:
    """Create a Chore instance with sensible defaults."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    defaults = {
        "id": "chore-1",
        "project_id": "PVT_1",
        "name": "Test",
        "template_path": ".github/ISSUE_TEMPLATE/test.md",
        "template_content": "# Test",
        "schedule_type": "time",
        "schedule_value": 7,
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


class TestEvaluateTimeTrigger:
    """Tests for the time-based trigger evaluation."""

    def test_triggers_when_elapsed(self):
        """Trigger fires when enough days have elapsed since last trigger."""
        past = (datetime.now(UTC) - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        chore = _make_chore(schedule_value=7, last_triggered_at=past)
        assert evaluate_time_trigger(chore) is True

    def test_skips_when_not_due(self):
        """Trigger does not fire when not enough time has elapsed."""
        recent = (datetime.now(UTC) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
        chore = _make_chore(schedule_value=7, last_triggered_at=recent)
        assert evaluate_time_trigger(chore) is False

    def test_never_triggered_uses_created_at(self):
        """Chore that has never triggered uses created_at as baseline."""
        old = (datetime.now(UTC) - timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        chore = _make_chore(schedule_value=14, last_triggered_at=None, created_at=old)
        assert evaluate_time_trigger(chore) is True

    def test_never_triggered_not_due_yet(self):
        """Chore created recently with no triggers should not fire."""
        recent = (datetime.now(UTC) - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
        chore = _make_chore(schedule_value=7, last_triggered_at=None, created_at=recent)
        assert evaluate_time_trigger(chore) is False

    def test_exact_boundary(self):
        """Trigger fires at exactly the boundary (>= schedule_value days)."""
        exact = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        chore = _make_chore(schedule_value=7, last_triggered_at=exact)
        assert evaluate_time_trigger(chore) is True

    def test_z_suffix_timestamps_are_supported(self):
        """UTC timestamps stored with a trailing Z should parse on Python 3.12+."""
        past = (datetime.now(UTC) - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        chore = _make_chore(schedule_value=7, last_triggered_at=past)
        assert evaluate_time_trigger(chore) is True

    def test_non_time_schedule_returns_false(self):
        """Count-based schedule returns False from time evaluator."""
        chore = _make_chore(schedule_type="count", schedule_value=5)
        assert evaluate_time_trigger(chore) is False

    def test_no_schedule_value_returns_false(self):
        """Chore with no schedule_value returns False."""
        chore = _make_chore(schedule_type="time", schedule_value=None)
        assert evaluate_time_trigger(chore) is False
