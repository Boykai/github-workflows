"""Polling lifecycle — start, stop, tick, and status reporting."""

import asyncio
import logging
from datetime import datetime
from src.utils import utcnow
from typing import Any

import src.services.copilot_polling as _cp

from .state import (
    _polling_state,
    _processed_issue_prs,
)

logger = logging.getLogger(__name__)


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


async def _poll_loop(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    interval_seconds: int,
) -> None:
    """Inner polling loop, separated so CancelledError is handled in the caller."""

    while _polling_state.is_running:
        try:
            _polling_state.last_poll_time = utcnow()
            _polling_state.poll_count += 1

            logger.debug(
                "Polling for Copilot PR completions (poll #%d)",
                _polling_state.poll_count,
            )

            # Fetch all project items once per poll cycle
            all_tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

            # Step 0: Post agent .md outputs from completed PRs as issue comments
            # This runs first so Done! markers are available for steps 1-3
            output_results = await _cp.post_agent_outputs_from_pr(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=all_tasks,
            )

            if output_results:
                logger.info(
                    "Poll #%d: Posted agent outputs for %d issues",
                    _polling_state.poll_count,
                    len(output_results),
                )

            # Step 1: Check "Backlog" issues for agent completion
            backlog_results = await _cp.check_backlog_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=all_tasks,
            )

            if backlog_results:
                logger.info(
                    "Poll #%d: Processed %d backlog issues",
                    _polling_state.poll_count,
                    len(backlog_results),
                )

            # Step 2: Check "Ready" issues for agent pipeline completion
            ready_results = await _cp.check_ready_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=all_tasks,
            )

            if ready_results:
                logger.info(
                    "Poll #%d: Processed %d ready issues",
                    _polling_state.poll_count,
                    len(ready_results),
                )

            # Step 3: Check "In Progress" issues for completed Copilot PRs
            results = await _cp.check_in_progress_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=all_tasks,
            )

            if results:
                logger.info(
                    "Poll #%d: Processed %d in-progress issues",
                    _polling_state.poll_count,
                    len(results),
                )

            # Step 4: Check "In Review" issues to ensure Copilot has reviewed their PRs
            review_results = await _cp.check_in_review_issues_for_copilot_review(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
            )

            if review_results:
                logger.info(
                    "Poll #%d: Requested Copilot review for %d PRs",
                    _polling_state.poll_count,
                    len(review_results),
                )

            # Step 5: Self-healing recovery — detect and fix stalled pipelines
            recovery_results = await _cp.recover_stalled_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                tasks=all_tasks,
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

        # Wait for next poll
        await asyncio.sleep(interval_seconds)

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
    return {
        "is_running": _polling_state.is_running,
        "last_poll_time": (
            _polling_state.last_poll_time.isoformat() if _polling_state.last_poll_time else None
        ),
        "poll_count": _polling_state.poll_count,
        "errors_count": _polling_state.errors_count,
        "last_error": _polling_state.last_error,
        "processed_issues_count": len(_processed_issue_prs),
    }
