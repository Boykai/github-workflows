"""Polling lifecycle — start, stop, tick, and status reporting."""

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypedDict

import src.services.copilot_polling as _cp
from src.logging_utils import get_logger
from src.utils import utcnow

from .state import (
    MAX_POLL_INTERVAL_SECONDS,
    RATE_LIMIT_PAUSE_THRESHOLD,
    RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD,
    RATE_LIMIT_SLOW_THRESHOLD,
    _polling_state,
    _processed_issue_prs,
)

logger = get_logger(__name__)


class RateLimitInfo(TypedDict, total=False):
    """Rate limit info from GitHub API."""

    limit: int | None
    remaining: int | None
    used: int | None
    reset_at: int | None


class PollingStatus(TypedDict):
    """Return type for :func:`get_polling_status`."""

    is_running: bool
    last_poll_time: str | None
    poll_count: int
    errors_count: int
    last_error: str | None
    processed_issues_count: int
    rate_limit: RateLimitInfo | None


@dataclass(frozen=True)
class PollStep:
    """Definition of a single polling loop step."""

    name: str
    execute: Callable[..., Awaitable[list]]
    is_expensive: bool = False


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


# ── Poll step implementations ──────────────────────────────────


async def _step_post_outputs(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Step 0: Post agent .md outputs from completed PRs as issue comments."""
    return (
        await _cp.post_agent_outputs_from_pr(
            access_token=access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            tasks=tasks,
        )
        or []
    )


async def _step_check_backlog(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Step 1: Check Backlog issues for agent completion."""
    return (
        await _cp.check_backlog_issues(
            access_token=access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            tasks=tasks,
        )
        or []
    )


async def _step_check_ready(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Step 2: Check Ready issues for agent pipeline completion."""
    return (
        await _cp.check_ready_issues(
            access_token=access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            tasks=tasks,
        )
        or []
    )


async def _step_check_in_progress(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Step 3: Check In Progress issues for completed Copilot PRs."""
    return (
        await _cp.check_in_progress_issues(
            access_token=access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            tasks=tasks,
        )
        or []
    )


async def _step_request_reviews(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Step 4: Request Copilot review for In Review PRs."""
    return (
        await _cp.check_in_review_issues_for_copilot_review(
            access_token=access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            tasks=tasks,
        )
        or []
    )


async def _step_review_completion(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Step 4b: Advance issues after Copilot review; recover stalled if idle."""
    results = await _cp.check_in_review_issues(
        access_token=access_token,
        project_id=project_id,
        owner=owner,
        repo=repo,
        tasks=tasks,
    )
    if results:
        return results
    # No reviews completed — try recovery if rate-limit budget allows
    remaining, _ = await _check_rate_limit_budget()
    if remaining is not None and remaining <= RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD:
        return []
    return (
        await _cp.recover_stalled_issues(
            access_token=access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            tasks=tasks,
        )
        or []
    )


async def _step_recover_stalled(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list:
    """Step 5: Self-healing recovery for stalled pipelines."""
    return (
        await _cp.recover_stalled_issues(
            access_token=access_token,
            project_id=project_id,
            owner=owner,
            repo=repo,
            tasks=tasks,
        )
        or []
    )


POLL_STEPS: list[PollStep] = [
    PollStep(name="Step 0: agent outputs", execute=_step_post_outputs, is_expensive=True),
    PollStep(name="Step 1: backlog", execute=_step_check_backlog),
    PollStep(name="Step 2: ready", execute=_step_check_ready),
    PollStep(name="Step 3: in-progress", execute=_step_check_in_progress),
    PollStep(name="Step 4: copilot review requests", execute=_step_request_reviews),
    PollStep(name="Step 4b: review completion", execute=_step_review_completion),
    PollStep(name="Step 5: stalled recovery", execute=_step_recover_stalled, is_expensive=True),
]


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

    try:
        await _poll_loop(access_token, project_id, owner, repo, interval_seconds)
    except asyncio.CancelledError:
        logger.info("Copilot PR completion polling cancelled")
    finally:
        _polling_state.is_running = False


async def _poll_single_project(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
) -> dict[str, list] | None:
    """Execute all polling steps for a single project.

    Returns a dict of step_name → results, or ``None`` if the rate-limit
    budget was exhausted (caller should abort the cycle).
    """
    from .helpers import is_sub_issue

    all_tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

    parent_tasks = [t for t in all_tasks if not is_sub_issue(t)]
    sub_count = len(all_tasks) - len(parent_tasks)
    if sub_count:
        logger.debug(
            "Project %s: filtered out %d sub-issues from %d board items",
            project_id[:12],
            sub_count,
            len(all_tasks),
        )

    remaining_pre, _ = await _check_rate_limit_budget()
    skip_expensive = (
        remaining_pre is not None and remaining_pre <= RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD
    )

    results: dict[str, list] = {}
    for step in POLL_STEPS:
        if step.is_expensive and skip_expensive:
            logger.warning(
                "Poll #%d (%s): Skipping %s — rate limit budget low (remaining=%d)",
                _polling_state.poll_count,
                project_id[:12],
                step.name,
                remaining_pre,
            )
            results[step.name] = []
            continue

        results[step.name] = await step.execute(
            access_token,
            project_id,
            owner,
            repo,
            parent_tasks,
        )

        if results[step.name]:
            logger.info(
                "Poll #%d (%s): %s — processed %d items",
                _polling_state.poll_count,
                project_id[:12],
                step.name,
                len(results[step.name]),
            )

        if await _pause_if_rate_limited(step.name):
            return None  # signal caller to abort cycle

    return results


async def _poll_loop(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    interval_seconds: int,
) -> None:
    """Inner polling loop, separated so CancelledError is handled in the caller."""

    while _polling_state.is_running:
        step_results: dict[str, list] = {}
        try:
            _polling_state.last_poll_time = utcnow()
            _polling_state.poll_count += 1

            # Clear per-cycle cache so each iteration starts with fresh data.
            _cp.github_projects_service.clear_cycle_cache()

            # ── Build project list: primary project first, then others ──
            from .state import MonitoredProject, get_monitored_projects

            primary = MonitoredProject(
                project_id=project_id,
                owner=owner,
                repo=repo,
                access_token=access_token,
                registered_at=utcnow(),
            )
            projects_to_poll: list[MonitoredProject] = [primary]
            projects_to_poll.extend(
                mp for mp in get_monitored_projects() if mp.project_id != project_id
            )

            logger.debug(
                "Polling for Copilot PR completions (poll #%d, %d project(s))",
                _polling_state.poll_count,
                len(projects_to_poll),
            )

            # ── Pre-cycle rate-limit check ──
            # After a restart the first poll triggers expensive reconstruction.
            # If we already know the budget is critically low, pause now.
            if await _pause_if_rate_limited("pre-cycle"):
                continue  # restart the while loop

            # ── Rate-limit critical alert (Phase 5) ──
            try:
                from src.config import get_settings as _get_settings

                _settings = _get_settings()
                rl_info = _cp.github_projects_service.get_last_rate_limit()
                if (
                    rl_info
                    and rl_info.get("remaining") is not None
                    and rl_info["remaining"] < _settings.rate_limit_critical_threshold
                ):
                    from src.services.alert_dispatcher import get_dispatcher

                    dispatcher = get_dispatcher()
                    if dispatcher is not None:
                        await dispatcher.dispatch_alert(
                            alert_type="rate_limit_critical",
                            summary=(
                                f"GitHub API rate limit critical: "
                                f"{rl_info['remaining']} remaining "
                                f"(threshold: {_settings.rate_limit_critical_threshold})"
                            ),
                            details={
                                "remaining": rl_info["remaining"],
                                "limit": rl_info.get("limit"),
                                "threshold": _settings.rate_limit_critical_threshold,
                                "reset_at": rl_info.get("reset_at"),
                            },
                        )
            except Exception as alert_err:
                logger.debug("Failed to dispatch rate_limit_critical alert: %s", alert_err)

            # ── Poll each registered project ──
            cycle_aborted = False
            for proj in projects_to_poll:
                if cycle_aborted:
                    break

                proj_results = await _poll_single_project(
                    access_token=proj.access_token,
                    project_id=proj.project_id,
                    owner=proj.owner,
                    repo=proj.repo,
                )
                if proj_results is None:
                    # Rate-limit pause triggered — abort remaining projects
                    cycle_aborted = True
                else:
                    for k, v in proj_results.items():
                        step_results.setdefault(k, []).extend(v)
                    proj.last_polled = utcnow()

            if cycle_aborted:
                continue

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

        # ── OTel metrics emission (Phase 5) ──
        try:
            from src.services.otel_setup import get_meter as _get_otel_meter
            from src.services.pipeline_state_store import get_all_pipeline_states

            _cycle_meter = _get_otel_meter()
            active_gauge = _cycle_meter.create_gauge("pipeline.active_count")
            active_gauge.set(len(get_all_pipeline_states()))

            rl_gauge = _cycle_meter.create_gauge("github.api_remaining")
            _rl_data = _cp.github_projects_service.get_last_rate_limit()
            if _rl_data and _rl_data.get("remaining") is not None:
                rl_gauge.set(_rl_data["remaining"])
        except Exception:
            pass  # OTel metrics are best-effort

        # ── Rate-limit snapshot recording (Phase 5, optional) ──
        try:
            from src.services.rate_limit_tracker import get_tracker

            _rl_snap = _cp.github_projects_service.get_last_rate_limit()
            if (
                _rl_snap
                and _rl_snap.get("remaining") is not None
                and _rl_snap.get("limit") is not None
                and _rl_snap.get("reset_at") is not None
            ):
                await get_tracker().record_snapshot(
                    remaining=_rl_snap["remaining"],
                    limit=_rl_snap["limit"],
                    reset_at=_rl_snap["reset_at"],
                )
        except Exception as snap_err:
            logger.debug("Rate-limit snapshot recording failed: %s", snap_err)

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

        had_activity = any(step_results.values())

        if had_activity:
            if _poll_state._consecutive_idle_polls:
                logger.info(
                    "Adaptive polling: activity detected, resetting idle counter from %d to 0",
                    _poll_state._consecutive_idle_polls,
                )
            _poll_state._consecutive_idle_polls = 0
        else:
            _poll_state._consecutive_idle_polls += 1

        # Phase 8: Update sliding-window activity tracking and tier
        _poll_state._activity_window.append(had_activity)

        if _poll_state._activity_window:
            activity_score = sum(1 for x in _poll_state._activity_window if x) / len(
                _poll_state._activity_window
            )
        else:
            activity_score = 0.0

        if activity_score > _poll_state.ACTIVITY_SCORE_HIGH_THRESHOLD:
            _poll_state._adaptive_tier = "high"
        elif activity_score > _poll_state.ACTIVITY_SCORE_MEDIUM_THRESHOLD:
            _poll_state._adaptive_tier = "medium"
        else:
            _poll_state._adaptive_tier = "low"

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


# ── Scoped App Pipeline Polling ─────────────────────────────────────────────


async def poll_app_pipeline(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    interval_seconds: int = 15,
) -> None:
    """Scoped polling loop for a new-repo / external-repo app pipeline.

    Monitors only the parent issue and its sub-issues on the app's project
    board.  Automatically stops when the pipeline is complete (all agents
    done) or the parent issue is closed.
    """
    from .helpers import is_sub_issue
    from .state import _app_polling_tasks

    logger.info(
        "Starting scoped app-pipeline polling for issue #%d on %s/%s (project %s)",
        parent_issue_number,
        owner,
        repo,
        project_id,
    )

    try:
        while True:
            try:
                _cp.github_projects_service.clear_cycle_cache()

                # Check whether the pipeline is still active.
                pipeline_state = _cp.get_pipeline_state(parent_issue_number)
                if pipeline_state is not None and pipeline_state.is_complete:
                    logger.info(
                        "App pipeline for issue #%d is complete — stopping scoped polling",
                        parent_issue_number,
                    )
                    break

                # Fetch all board items and run the standard polling steps.
                all_tasks = await _cp.github_projects_service.get_project_items(
                    access_token, project_id
                )
                parent_tasks = [t for t in all_tasks if not is_sub_issue(t)]

                for step in POLL_STEPS:
                    if step.is_expensive:
                        continue  # skip expensive steps for scoped polling
                    await step.execute(access_token, project_id, owner, repo, parent_tasks)

                # Re-check after processing — pipeline may have just completed.
                pipeline_state = _cp.get_pipeline_state(parent_issue_number)
                if pipeline_state is None or pipeline_state.is_complete:
                    logger.info(
                        "App pipeline for issue #%d finished — stopping scoped polling",
                        parent_issue_number,
                    )
                    break

            except Exception as exc:
                logger.warning(
                    "Error in scoped app-pipeline polling for issue #%d: %s",
                    parent_issue_number,
                    exc,
                )

            await asyncio.sleep(interval_seconds)

    except asyncio.CancelledError:
        logger.info("Scoped app-pipeline polling cancelled for issue #%d", parent_issue_number)
    finally:
        _app_polling_tasks.pop(project_id, None)
        logger.info(
            "Scoped app-pipeline polling ended for issue #%d on %s/%s",
            parent_issue_number,
            owner,
            repo,
        )


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


def get_polling_status() -> PollingStatus:
    """Get current polling status."""
    rl = _cp.github_projects_service.get_last_rate_limit()
    rate_limit_info: RateLimitInfo | None = None
    if rl:
        rate_limit_info = RateLimitInfo(
            limit=rl.get("limit"),
            remaining=rl.get("remaining"),
            used=rl.get("used"),
            reset_at=rl.get("reset_at"),
        )
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
