"""Polling lifecycle — start, stop, tick, and status reporting."""

import asyncio
import logging
from typing import Any

import src.services.copilot_polling as _cp
from src.utils import utcnow

from .state import (
    MAX_POLL_INTERVAL_SECONDS,
    RATE_LIMIT_PAUSE_THRESHOLD,
    RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD,
    RATE_LIMIT_SLOW_THRESHOLD,
    _polling_state,
    _processed_issue_prs,
)

logger = logging.getLogger(__name__)


# ── Rate-limit helpers ──────────────────────────────────────────


async def _check_rate_limit_budget() -> tuple[int | None, int | None]:
    """Read the latest rate-limit info and return (remaining, reset_at).

    Returns (None, None) when no rate-limit data is available yet.
    """
    rl = _cp.github_projects_service.get_last_rate_limit()
    if rl is None:
        return None, None
    return rl.get("remaining"), rl.get("reset_at")


async def _pause_if_rate_limited(step_name: str) -> bool:
    """If remaining quota is at or below the pause threshold, sleep until reset.

    Returns True if the loop should abort the current cycle (quota exhausted).

    **Stale-data guard**: if ``reset_at`` is in the past, the rate-limit
    window has already rolled over but no fresh API call has updated the
    cached headers.  In that case we clear the stale data and allow the
    cycle to proceed — the next API call will populate up-to-date headers.
    This prevents an infinite sleep-10s loop where the polling never makes
    a single request because it keeps re-reading the same stale remaining=0.
    """
    remaining, reset_at = await _check_rate_limit_budget()
    if remaining is None:
        return False

    if remaining <= RATE_LIMIT_PAUSE_THRESHOLD:
        now_ts = int(utcnow().timestamp())

        # If the reset window has already passed, the cached data is stale.
        # Clear it so the next cycle proceeds and fetches fresh headers.
        if reset_at is not None and reset_at <= now_ts:
            logger.info(
                "Rate-limit reset window has passed (reset_at=%d <= now=%d) "
                "but cached remaining=%d after %s. Clearing stale data — "
                "next API call will refresh headers.",
                reset_at,
                now_ts,
                remaining,
                step_name,
            )
            # Clear both request-scoped contextvar and instance-level
            # caches so get_last_rate_limit() returns None on the next
            # call, allowing the cycle to proceed with a fresh API request.
            _cp.github_projects_service.clear_last_rate_limit()
            return False  # allow the cycle to proceed

        wait = max((reset_at or now_ts) - now_ts, 10)
        # Cap wait to 15 minutes to prevent pathological sleeps
        wait = min(wait, 900)
        logger.warning(
            "Rate limit nearly exhausted after %s (remaining=%d). "
            "Pausing polling for %d seconds until reset.",
            step_name,
            remaining,
            wait,
        )
        await asyncio.sleep(wait)
        return True  # abort this cycle — start fresh

    if remaining <= RATE_LIMIT_SLOW_THRESHOLD:
        logger.info(
            "Rate limit getting low after %s (remaining=%d). Proceeding cautiously.",
            step_name,
            remaining,
        )
    return False


async def poll_for_copilot_completion(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    interval_seconds: int = 60,
) -> None:
    """
    Background polling loop to check for Copilot PR completions.

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner
        repo: Repository name
        interval_seconds: Polling interval in seconds (default: 60)
    """
    logger.info(
        "Starting Copilot PR completion polling (interval: %ds)",
        interval_seconds,
    )

    _polling_state.is_running = True

    # Blocking queue: startup recovery — activate any pending issues stuck during downtime
    try:
        from src.services import blocking_queue as bq_service

        await bq_service.recover_all_repos()
    except Exception:
        logger.debug("Blocking queue startup recovery skipped (not available)")

    try:
        await _poll_loop(access_token, project_id, owner, repo, interval_seconds)
    except asyncio.CancelledError:
        logger.info("Copilot PR completion polling cancelled")
    finally:
        _polling_state.is_running = False


async def _poll_loop(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    interval_seconds: int,
) -> None:
    """Inner polling loop, separated so CancelledError is handled in the caller."""

    while _polling_state.is_running:
        # Initialize result variables so the activity check after the
        # try/except always has valid references (even after continue).
        output_results: list = []
        backlog_results: list = []
        ready_results: list = []
        results: list = []
        review_results: list = []
        in_review_results: list = []
        recovery_results: list = []
        skip_expensive = False
        try:
            _polling_state.last_poll_time = utcnow()
            _polling_state.poll_count += 1

            # Clear per-cycle cache so each iteration starts with fresh data.
            _cp.github_projects_service.clear_cycle_cache()

            logger.debug(
                "Polling for Copilot PR completions (poll #%d)",
                _polling_state.poll_count,
            )

            # ── Pre-cycle rate-limit check ──
            # After a restart the first poll triggers expensive reconstruction.
            # If we already know the budget is critically low, pause now.
            if await _pause_if_rate_limited("pre-cycle"):
                continue  # restart the while loop

            # Fetch all project items once per poll cycle
            all_tasks = await _cp.github_projects_service.get_project_items(
                access_token, project_id
            )

            # Filter out agent sub-issues — they are on the board but should
            # NOT be processed as standalone pipeline-tracked issues.  Processing
            # them wastes API calls (linked PRs, comments) and can create
            # spurious pipeline states that burn through the rate limit.
            from .helpers import is_sub_issue

            parent_tasks = [t for t in all_tasks if not is_sub_issue(t)]
            sub_count = len(all_tasks) - len(parent_tasks)
            if sub_count:
                logger.debug(
                    "Filtered out %d sub-issues from %d board items",
                    sub_count,
                    len(all_tasks),
                )

            # Step 0: Post agent .md outputs from completed PRs as issue comments
            # This runs first so Done! markers are available for steps 1-3
            # This is the MOST expensive step — skip it when budget is low.
            remaining_pre, _ = await _check_rate_limit_budget()
            skip_expensive = (
                remaining_pre is not None and remaining_pre <= RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD
            )

            if skip_expensive:
                logger.warning(
                    "Poll #%d: Skipping Step 0 (agent outputs) — "
                    "rate limit budget low (remaining=%d)",
                    _polling_state.poll_count,
                    remaining_pre,
                )
                output_results = []
            else:
                output_results = await _cp.post_agent_outputs_from_pr(
                    access_token=access_token,
                    project_id=project_id,
                    owner=owner,
                    repo=repo,
                    tasks=parent_tasks,
                )

            if output_results:
                logger.info(
                    "Poll #%d: Posted agent outputs for %d issues",
                    _polling_state.poll_count,
                    len(output_results),
                )

            if await _pause_if_rate_limited("Step 0"):
                continue

            # Step 1: Check "Backlog" issues for agent completion
            backlog_results = await _cp.check_backlog_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=parent_tasks,
            )

            if backlog_results:
                logger.info(
                    "Poll #%d: Processed %d backlog issues",
                    _polling_state.poll_count,
                    len(backlog_results),
                )

            if await _pause_if_rate_limited("Step 1"):
                continue

            # Step 2: Check "Ready" issues for agent pipeline completion
            ready_results = await _cp.check_ready_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=parent_tasks,
            )

            if ready_results:
                logger.info(
                    "Poll #%d: Processed %d ready issues",
                    _polling_state.poll_count,
                    len(ready_results),
                )

            if await _pause_if_rate_limited("Step 2"):
                continue

            # Step 3: Check "In Progress" issues for completed Copilot PRs
            results = await _cp.check_in_progress_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=parent_tasks,
            )

            if results:
                logger.info(
                    "Poll #%d: Processed %d in-progress issues",
                    _polling_state.poll_count,
                    len(results),
                )

            if await _pause_if_rate_limited("Step 3"):
                continue

            # Step 4: Check "In Review" issues to ensure Copilot has reviewed their PRs
            review_results = await _cp.check_in_review_issues_for_copilot_review(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=parent_tasks,
            )

            if review_results:
                logger.info(
                    "Poll #%d: Requested Copilot review for %d PRs",
                    _polling_state.poll_count,
                    len(review_results),
                )

            if await _pause_if_rate_limited("Step 4"):
                continue

            # Step 4b: Check "In Review" issues for completed Copilot reviews
            # and advance the pipeline to "Done"
            in_review_results = await _cp.check_in_review_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=parent_tasks,
            )

            if in_review_results:
                logger.info(
                    "Poll #%d: Advanced %d issues after Copilot review completion",
                    _polling_state.poll_count,
                    len(in_review_results),
                )
            elif not skip_expensive:
                recovery_results = await _cp.recover_stalled_issues(
                    access_token=access_token,
                    project_id=project_id,
                    owner=owner,
                    repo=repo,
                    tasks=parent_tasks,
                )

                if recovery_results:
                    logger.info(
                        "Poll #%d: Recovered %d stalled issues",
                        _polling_state.poll_count,
                        len(recovery_results),
                    )

            if await _pause_if_rate_limited("Step 4b"):
                continue

            # Step 4c: Blocking queue sweep — detect closed/deleted blocking
            # issues and unblock the queue.  Lightweight: one REST call per
            # active/in_review entry (typically 0-2).
            try:
                from src.services import blocking_queue as bq_service

                swept = await bq_service.sweep_stale_entries(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                )
                if swept:
                    logger.info(
                        "Poll #%d: Blocking queue sweep cleared %d stale entries: %s",
                        _polling_state.poll_count,
                        len(swept),
                        swept,
                    )
            except Exception:
                logger.debug("Blocking queue sweep skipped (not available)")

            # Step 5: Self-healing recovery — detect and fix stalled pipelines
            # Skip if budget is low — recovery is least critical.
            if skip_expensive:
                logger.debug(
                    "Poll #%d: Skipping Step 5 (recovery) — rate limit budget low",
                    _polling_state.poll_count,
                )
            else:
                recovery_results = await _cp.recover_stalled_issues(
                    access_token=access_token,
                    project_id=project_id,
                    owner=owner,
                    repo=repo,
                    tasks=parent_tasks,
                )

                if recovery_results:
                    logger.info(
                        "Poll #%d: Recovered %d stalled issues",
                        _polling_state.poll_count,
                        len(recovery_results),
                    )

        except Exception as e:
            logger.error("Error in polling loop: %s", e)
            _polling_state.errors_count += 1
            _polling_state.last_error = str(e)

            # If the error came from a rate-limit 403, the cached headers
            # may show remaining=0 with a reset_at that is already past
            # (or about to be).  Clear stale data so the next cycle's
            # pre-cycle check doesn't enter an infinite 10s sleep loop.
            err_remaining, err_reset = await _check_rate_limit_budget()
            if err_remaining is not None and err_remaining <= RATE_LIMIT_PAUSE_THRESHOLD:
                now_err = int(utcnow().timestamp())
                if err_reset is not None and err_reset <= now_err:
                    logger.info(
                        "Post-error: clearing stale rate-limit data "
                        "(remaining=%d, reset_at=%d <= now=%d)",
                        err_remaining,
                        err_reset,
                        now_err,
                    )
                    _cp.github_projects_service.clear_last_rate_limit()

        # ── Dynamic interval based on remaining rate-limit budget ──
        remaining, _ = await _check_rate_limit_budget()
        if remaining is not None and remaining <= RATE_LIMIT_SLOW_THRESHOLD:
            # Double the interval when budget is getting low
            effective_interval = interval_seconds * 2
            logger.info(
                "Rate limit budget low (remaining=%d). Doubling poll interval to %ds.",
                remaining,
                effective_interval,
            )
        else:
            effective_interval = interval_seconds

        # ── Activity-based adaptive polling (FR-019) ──
        # Detect whether this cycle produced any results; if so, treat it
        # as "active" and reset the idle counter back to baseline.
        import src.services.copilot_polling.state as _poll_state

        had_activity = bool(
            output_results
            or backlog_results
            or ready_results
            or results
            or review_results
            or in_review_results
            or (not skip_expensive and recovery_results)
        )

        if had_activity:
            if _poll_state._consecutive_idle_polls:
                logger.info(
                    "Adaptive polling: activity detected, resetting idle counter from %d to 0",
                    _poll_state._consecutive_idle_polls,
                )
            _poll_state._consecutive_idle_polls = 0
        else:
            _poll_state._consecutive_idle_polls += 1

        # Only apply adaptive backoff when rate-limit doubling is NOT already
        # active — avoid stacking both multipliers.
        if _poll_state._consecutive_idle_polls > 0 and effective_interval == interval_seconds:
            max_doublings = 3  # 60 → 120 → 240 → 300 (capped)
            idle_multiplier = 2 ** min(_poll_state._consecutive_idle_polls, max_doublings)
            adaptive_interval = min(
                interval_seconds * idle_multiplier,
                MAX_POLL_INTERVAL_SECONDS,
            )
            if adaptive_interval > effective_interval:
                logger.info(
                    "Adaptive polling: %d consecutive idle polls, interval %ds → %ds",
                    _poll_state._consecutive_idle_polls,
                    effective_interval,
                    adaptive_interval,
                )
                effective_interval = adaptive_interval

        await asyncio.sleep(effective_interval)

    logger.info("Copilot PR completion polling stopped")
    _polling_state.is_running = False


def stop_polling() -> None:
    """Stop the background polling loop.

    Sets the is_running flag to False AND cancels the asyncio task so that
    the loop stops even if it's in the middle of a long-running await.

    Reads ``_polling_task`` from the package namespace (``_cp``) so that
    callers setting ``src.services.copilot_polling._polling_task`` are
    correctly reflected here.
    """
    _polling_state.is_running = False
    if _cp._polling_task is not None and not _cp._polling_task.done():
        _cp._polling_task.cancel()
        _cp._polling_task = None


def get_polling_status() -> dict[str, Any]:
    """Get current polling status."""
    rl = _cp.github_projects_service.get_last_rate_limit()
    rate_limit_info: dict[str, Any] | None = None
    if rl:
        rate_limit_info = {
            "limit": rl.get("limit"),
            "remaining": rl.get("remaining"),
            "used": rl.get("used"),
            "reset_at": rl.get("reset_at"),
        }
    return {
        "is_running": _polling_state.is_running,
        "last_poll_time": (
            _polling_state.last_poll_time.isoformat() if _polling_state.last_poll_time else None
        ),
        "poll_count": _polling_state.poll_count,
        "errors_count": _polling_state.errors_count,
        "last_error": _polling_state.last_error,
        "processed_issues_count": len(_processed_issue_prs),
        "rate_limit": rate_limit_info,
    }
