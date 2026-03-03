"""Counter — count-based trigger evaluation for chores."""

from __future__ import annotations

from src.models.chores import Chore


def evaluate_count_trigger(chore: Chore, current_count: int) -> bool:
    """Check whether a count-based chore has reached its threshold.

    Args:
        chore: The chore to evaluate.
        current_count: Number of qualifying parent issues created since
            the chore's last trigger count.

    Returns:
        True if `current_count` meets or exceeds `schedule_value`.
    """
    if chore.schedule_type != "count" or chore.schedule_value is None:
        return False

    issues_since = current_count - chore.last_triggered_count
    return issues_since >= chore.schedule_value
