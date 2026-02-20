"""
Polling lifecycle & recovery for the Copilot polling service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from src.models.chat import WorkflowConfiguration
from src.services.agent_tracking import (
    get_current_agent_from_tracking,
    get_next_pending_agent,
    parse_tracking_from_body,
)
from . import _deps
from src.services.workflow_orchestrator import (
    WorkflowContext,
    WorkflowState,
    get_agent_slugs,
    get_issue_main_branch,
    get_pipeline_state,
    get_workflow_config,
    get_workflow_orchestrator,
    set_workflow_config,
)

from .state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    RECOVERY_COOLDOWN_SECONDS,
    _pending_agent_assignments,
    _polling_state,
    _processed_issue_prs,
    _recovery_last_attempt,
)
from .tracking import _check_agent_done_on_sub_or_parent
from .pr_detection import post_agent_outputs_from_pr
from .status_checks import (
    check_backlog_issues,
    check_in_progress_issues,
    check_in_review_issues_for_copilot_review,
    check_ready_issues,
    process_in_progress_issue,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Self-Healing Recovery: Detect and fix stalled agent pipelines
# ──────────────────────────────────────────────────────────────────────────────


async def recover_stalled_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list | None = None,
) -> list[dict[str, Any]]:
    """
    Self-healing recovery check for all issues that have not reached "In Review".

    For every issue in Backlog / Ready / In Progress status:
      1. Parse the agent tracking table from the issue body to determine the
         expected current agent and its status (Active / Pending).
      2. Verify that BOTH conditions are true:
         a) Copilot is assigned to the issue
         b) There is a WIP (draft) PR that the agent is working on
      3. If either condition is missing, re-assign the agent so Copilot
         restarts the work.

    A per-issue cooldown prevents re-assignment from firing every poll cycle;
    after a recovery assignment, the issue is given RECOVERY_COOLDOWN_SECONDS
    before being checked again.

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner
        repo: Repository name
        tasks: Pre-fetched project items (optional)

    Returns:
        List of recovery actions taken
    """
    results: list[dict[str, Any]] = []

    try:
        if tasks is None:
            tasks = await _deps.github_projects_service.get_project_items(access_token, project_id)

        config = get_workflow_config(project_id)
        if not config:
            # Auto-bootstrap a default workflow config so recovery can work
            # even after an app restart (the config is normally in-memory only)
            logger.info(
                "Recovery: no workflow config for project %s — bootstrapping default config",
                project_id,
            )
            config = WorkflowConfiguration(
                project_id=project_id,
                repository_owner=owner,
                repository_name=repo,
            )
            set_workflow_config(project_id, config)

        # Statuses that are "pre-review" — these are the ones we monitor
        terminal_statuses = {
            (config.status_in_review or "In Review").lower(),
            (getattr(config, "status_done", None) or "Done").lower(),
        }

        # Filter to non-terminal issues with issue numbers
        active_tasks = [
            task
            for task in tasks
            if task.status
            and task.status.lower() not in terminal_statuses
            and task.issue_number is not None
        ]

        if not active_tasks:
            return results

        logger.debug(
            "Recovery check: %d issues have not reached 'In Review'",
            len(active_tasks),
        )

        now = datetime.utcnow()

        for task in active_tasks:
            issue_number = task.issue_number
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo

            if not task_owner or not task_repo:
                continue

            # ── Cooldown check ────────────────────────────────────────────
            last_attempt = _recovery_last_attempt.get(issue_number)
            if last_attempt:
                elapsed = (now - last_attempt).total_seconds()
                if elapsed < RECOVERY_COOLDOWN_SECONDS:
                    logger.debug(
                        "Recovery: issue #%d on cooldown (%.0fs / %ds)",
                        issue_number,
                        elapsed,
                        RECOVERY_COOLDOWN_SECONDS,
                    )
                    continue

            # ── Read the issue body tracking table ────────────────────────
            try:
                issue_data = await _deps.github_projects_service.get_issue_with_comments(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=issue_number,
                )
            except Exception as e:
                logger.debug("Recovery: could not fetch issue #%d: %s", issue_number, e)
                continue

            body = issue_data.get("body", "")
            if not body:
                continue

            steps = parse_tracking_from_body(body)
            if not steps:
                # No tracking table — this issue wasn't created through our pipeline
                continue

            # ── Determine expected agent ──────────────────────────────────
            # The active agent (🔄) is the one that should be working.
            # If there is no active agent, the next pending agent (⏳) needs
            # to be assigned.
            active_step = get_current_agent_from_tracking(body)
            pending_step = get_next_pending_agent(body)

            if active_step is None and pending_step is None:
                # All agents are ✅ Done — nothing to recover
                continue

            expected_agent = active_step or pending_step
            if expected_agent is None:
                continue
            agent_name = expected_agent.agent_name
            agent_status = expected_agent.status  # e.g. "Backlog", "Ready"

            # ── Pending assignment check ──────────────────────────────────
            # If the agent was just assigned (by the workflow or a previous
            # recovery), skip — Copilot needs time to create the WIP PR.
            pending_key = f"{issue_number}:{agent_name}"
            pending_ts = _pending_agent_assignments.get(pending_key)
            if pending_ts is not None:
                pending_age = (now - pending_ts).total_seconds()
                if pending_age < ASSIGNMENT_GRACE_PERIOD_SECONDS:
                    logger.debug(
                        "Recovery: issue #%d agent '%s' is in pending set (%.0fs ago) — skipping",
                        issue_number,
                        agent_name,
                        pending_age,
                    )
                    continue
                else:
                    # Pending entry is stale — remove it and proceed with recovery
                    logger.debug(
                        "Recovery: issue #%d agent '%s' pending entry is stale (%.0fs) — clearing",
                        issue_number,
                        agent_name,
                        pending_age,
                    )
                    _pending_agent_assignments.pop(pending_key, None)

            # ── Check condition A: Copilot is assigned ────────────────────
            copilot_assigned = await _deps.github_projects_service.is_copilot_assigned_to_issue(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=issue_number,
            )

            # ── Check condition B: WIP (draft) PR exists ─────────────────
            has_wip_pr = False
            wip_pr_number = None

            # For the first agent, look for any open Copilot draft PR linked to issue
            # For subsequent agents, look for a child PR targeting the main branch
            main_branch_info = get_issue_main_branch(issue_number)

            linked_prs = await _deps.github_projects_service.get_linked_pull_requests(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=issue_number,
            )

            if linked_prs:
                for pr in linked_prs:
                    pr_number = pr.get("number")
                    pr_state = (pr.get("state") or "").upper()
                    pr_author = (pr.get("author") or "").lower()

                    if pr_state != "OPEN" or "copilot" not in pr_author:
                        continue

                    if not isinstance(pr_number, int):
                        continue

                    # Get full details to check draft status
                    pr_details = await _deps.github_projects_service.get_pull_request(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        pr_number=pr_number,
                    )
                    if not pr_details:
                        continue

                    is_draft = pr_details.get("is_draft", False)
                    pr_base = pr_details.get("base_ref", "")

                    if main_branch_info:
                        # Subsequent agent — WIP PR must be a draft child PR
                        # targeting the main branch (or "main")
                        main_branch = main_branch_info["branch"]
                        main_pr = main_branch_info["pr_number"]

                        if pr_number == main_pr:
                            # This is the main PR, not a child — check if it's
                            # still draft (first agent may still be working)
                            if is_draft and not main_branch_info.get("head_sha"):
                                has_wip_pr = True
                                wip_pr_number = pr_number
                                break
                            continue

                        # Child PR: must target main branch or "main"
                        if pr_base == main_branch or pr_base == "main":
                            has_wip_pr = True
                            wip_pr_number = pr_number
                            break
                    else:
                        # First agent — any open Copilot PR counts
                        has_wip_pr = True
                        wip_pr_number = pr_number
                        break

            # ── Evaluate whether recovery is needed ───────────────────────
            if copilot_assigned and has_wip_pr:
                # Both conditions met — agent is working normally
                logger.debug(
                    "Recovery: issue #%d OK — agent '%s' assigned and WIP PR #%s exists",
                    issue_number,
                    agent_name,
                    wip_pr_number,
                )
                continue

            # Something is wrong — log what's missing
            missing = []
            if not copilot_assigned:
                missing.append("Copilot NOT assigned")
            if not has_wip_pr:
                missing.append("no WIP PR found")

            # ── Guard: check if the agent already completed ──────────────
            # After a container restart, volatile state is lost but the
            # Done! marker (posted by Step 0 in the same or a prior poll
            # cycle) persists in issue comments.  If the marker exists,
            # the agent finished successfully and Steps 1-3 will advance
            # the pipeline — no recovery needed.
            recovery_pipeline = get_pipeline_state(issue_number)
            already_done = await _check_agent_done_on_sub_or_parent(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                parent_issue_number=issue_number,
                agent_name=agent_name,
                pipeline=recovery_pipeline,
            )
            if already_done:
                logger.info(
                    "Recovery: issue #%d — agent '%s' has Done! marker, "
                    "skipping re-assignment (problems were: %s)",
                    issue_number,
                    agent_name,
                    ", ".join(missing),
                )
                _recovery_last_attempt[issue_number] = now
                continue

            logger.warning(
                "Recovery: issue #%d stalled — agent '%s' (%s), problems: %s. Re-assigning agent.",
                issue_number,
                agent_name,
                "Active" if active_step else "Pending",
                ", ".join(missing),
            )

            # ── Re-assign the agent ──────────────────────────────────────
            # Figure out which status and agent_index to use
            agents_for_status = get_agent_slugs(config, agent_status)
            try:
                agent_index = agents_for_status.index(agent_name)
            except ValueError:
                logger.warning(
                    "Recovery: agent '%s' not found in mappings for status '%s'",
                    agent_name,
                    agent_status,
                )
                continue

            orchestrator = get_workflow_orchestrator()
            ctx = WorkflowContext(
                session_id="recovery",
                project_id=project_id,
                access_token=access_token,
                repository_owner=task_owner,
                repository_name=task_repo,
                issue_id=task.github_content_id,
                issue_number=issue_number,
                project_item_id=task.github_item_id,
                current_state=WorkflowState.READY,
            )
            ctx.config = config

            try:
                assigned = await orchestrator.assign_agent_for_status(
                    ctx, agent_status, agent_index=agent_index
                )
            except Exception as e:
                logger.error(
                    "Recovery: failed to re-assign agent '%s' for issue #%d: %s",
                    agent_name,
                    issue_number,
                    e,
                )
                _recovery_last_attempt[issue_number] = now
                continue

            # Set cooldown regardless of success to avoid rapid retries
            _recovery_last_attempt[issue_number] = now

            if assigned:
                # Also add to pending set so normal polling doesn't double-assign
                pending_key = f"{issue_number}:{agent_name}"
                _pending_agent_assignments[pending_key] = now

                results.append(
                    {
                        "status": "recovered",
                        "issue_number": issue_number,
                        "agent_name": agent_name,
                        "agent_status": agent_status,
                        "was_active": active_step is not None,
                        "missing": missing,
                    }
                )
                logger.info(
                    "Recovery: re-assigned agent '%s' for issue #%d (missing: %s)",
                    agent_name,
                    issue_number,
                    ", ".join(missing),
                )
            else:
                logger.warning(
                    "Recovery: assign_agent_for_status returned False for '%s' on issue #%d",
                    agent_name,
                    issue_number,
                )

    except Exception as e:
        logger.error("Error in recovery check: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = f"Recovery error: {e}"

    # Limit cooldown cache size
    if len(_recovery_last_attempt) > 200:
        oldest = sorted(_recovery_last_attempt.items(), key=lambda kv: kv[1])[:100]
        for key, _ in oldest:
            _recovery_last_attempt.pop(key, None)

    return results


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
            _polling_state.last_poll_time = datetime.utcnow()
            _polling_state.poll_count += 1

            logger.debug(
                "Polling for Copilot PR completions (poll #%d)",
                _polling_state.poll_count,
            )

            # Fetch all project items once per poll cycle
            all_tasks = await _deps.github_projects_service.get_project_items(access_token, project_id)

            # Step 0: Post agent .md outputs from completed PRs as issue comments
            # This runs first so Done! markers are available for steps 1-3
            output_results = await post_agent_outputs_from_pr(
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
            backlog_results = await check_backlog_issues(
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
            ready_results = await check_ready_issues(
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
            results = await check_in_progress_issues(
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
            review_results = await check_in_review_issues_for_copilot_review(
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
            recovery_results = await recover_stalled_issues(
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
    """
    import src.services.copilot_polling as _pkg

    _polling_state.is_running = False
    if _pkg._polling_task is not None and not _pkg._polling_task.done():
        _pkg._polling_task.cancel()
        _pkg._polling_task = None


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


# ──────────────────────────────────────────────────────────────────────────────
# Alternative: Manual trigger for checking specific issues
# ──────────────────────────────────────────────────────────────────────────────


async def check_issue_for_copilot_completion(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    issue_number: int,
) -> dict[str, Any]:
    """
    Manually check a specific issue for Copilot PR completion.

    This can be called on-demand via API endpoint.

    Args:
        access_token: GitHub access token
        project_id: Project V2 node ID
        owner: Repository owner (fallback)
        repo: Repository name (fallback)
        issue_number: Issue number to check

    Returns:
        Result dict with status and details
    """
    try:
        # Find the project item for this issue
        tasks = await _deps.github_projects_service.get_project_items(access_token, project_id)

        # Find matching task by issue number
        target_task = None
        for task in tasks:
            if task.issue_number == issue_number:
                target_task = task
                break

        if not target_task:
            return {
                "status": "not_found",
                "issue_number": issue_number,
                "message": f"Issue #{issue_number} not found in project",
            }

        if target_task.status and target_task.status.lower() != "in progress":
            return {
                "status": "skipped",
                "issue_number": issue_number,
                "current_status": target_task.status,
                "message": f"Issue #{issue_number} is not in 'In Progress' status",
            }

        # Use task's repository info if available
        task_owner = target_task.repository_owner or owner
        task_repo = target_task.repository_name or repo

        result = await process_in_progress_issue(
            access_token=access_token,
            project_id=project_id,
            item_id=target_task.github_item_id,
            owner=task_owner,
            repo=task_repo,
            issue_number=issue_number,
            task_title=target_task.title or f"Issue #{issue_number}",
        )

        return result or {
            "status": "no_action",
            "issue_number": issue_number,
            "message": "No completed Copilot PR found",
        }

    except Exception as e:
        logger.error("Error checking issue #%d: %s", issue_number, e)
        return {
            "status": "error",
            "issue_number": issue_number,
            "error": str(e),
        }
