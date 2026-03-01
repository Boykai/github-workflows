"""Count-based trigger evaluator for housekeeping tasks."""


def is_threshold_met(
    current_count: int,
    last_triggered_count: int,
    threshold: int,
) -> bool:
    """
    Evaluate whether the count-based trigger threshold has been met.

    Args:
        current_count: Current number of parent issues created in the project.
        last_triggered_count: Issue count baseline at last trigger.
        threshold: Number of new issues required to trigger.

    Returns:
        True if the threshold is met or exceeded.
    """
    if threshold <= 0:
        return False
    return (current_count - last_triggered_count) >= threshold
