"""Time-based trigger scheduler with cron expression parsing."""

from datetime import UTC, datetime

# Named preset mappings to cron expressions
CRON_PRESETS: dict[str, str] = {
    "daily": "0 0 * * *",
    "weekly": "0 0 * * 1",
    "monthly": "0 0 1 * *",
}


def is_task_due(trigger_value: str, last_triggered_at: str | None) -> bool:
    """
    Determine if a time-based task is due for execution.

    Args:
        trigger_value: Cron expression or named preset (daily/weekly/monthly).
        last_triggered_at: ISO timestamp of last trigger, or None if never triggered.

    Returns:
        True if the task should be triggered now.
    """
    # Resolve named presets
    cron_expr = CRON_PRESETS.get(trigger_value.lower(), trigger_value)

    # If never triggered, it's due
    if not last_triggered_at:
        return True

    try:
        last = datetime.fromisoformat(last_triggered_at)
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return True

    now = datetime.now(UTC)
    elapsed_seconds = (now - last).total_seconds()

    # Simple interval calculation based on cron expression
    interval = _cron_to_interval_seconds(cron_expr)
    return elapsed_seconds >= interval


def _cron_to_interval_seconds(cron_expr: str) -> int:
    """
    Convert a simplified cron expression to an approximate interval in seconds.

    Supports standard 5-field cron: minute hour day-of-month month day-of-week.
    Returns the minimum interval that should pass between triggers.
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        # Fallback: treat as daily if unparseable
        return 86400

    minute, hour, dom, month, dow = parts

    # Monthly: day-of-month is specific
    if dom != "*" and month == "*":
        return 28 * 86400  # ~28 days minimum

    # Weekly: day-of-week is specific
    if dow != "*" and dom == "*":
        return 7 * 86400  # 7 days

    # Daily: hour is specific
    if hour != "*" and dom == "*" and dow == "*":
        return 86400  # 24 hours

    # Hourly: minute is specific, hour is *
    if minute != "*" and hour == "*":
        return 3600  # 1 hour

    # Every N minutes (e.g., */15)
    if minute.startswith("*/"):
        try:
            n = int(minute[2:])
            return n * 60
        except ValueError:
            pass

    # Default: daily
    return 86400
