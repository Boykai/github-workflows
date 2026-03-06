"""Scheduler — time-based trigger evaluation for chores."""

from __future__ import annotations

from datetime import UTC, datetime

from src.models.chores import Chore


def evaluate_time_trigger(chore: Chore) -> bool:
    """Check whether a time-based chore is due for triggering.

    Uses ``last_triggered_at`` if the chore has been triggered before,
    otherwise falls back to ``created_at``.  Returns ``True`` when at
    least ``schedule_value`` days have elapsed since the reference time.
    """
    if chore.schedule_type != "time" or chore.schedule_value is None:
        return False

    base_iso = chore.last_triggered_at or chore.created_at
    if base_iso.endswith("Z"):
        base_iso = f"{base_iso[:-1]}+00:00"
    base = datetime.fromisoformat(base_iso)
    now = datetime.now(UTC)

    elapsed_days = (now - base).total_seconds() / 86_400
    return elapsed_days >= chore.schedule_value
