"""Self-healing recovery: detect and fix stalled agent pipelines."""

import logging
from typing import Any

import src.services.copilot_polling as _cp
from src.utils import utcnow

from .helpers import _get_sub_issue_number
from .state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    RECOVERY_COOLDOWN_SECONDS,
    _pending_agent_assignments,
    _polling_state,
    _recovery_last_attempt,
)

logger = logging.getLogger(__name__)


async def _resolve_expected_agent_from_completion_signals(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    steps: list,
    pipeline: Any,
) -> Any | None:
    """Return the first step that is not durably complete.

    The issue-body tracking table can lag behind the true pipeline state when
    a Done! comment was posted but the body update failed or the process
    restarted before the table was refreshed. In that case recovery must not
    trust the first stale ⏳ Pending row, or it can reassign an already-finished
    earlier agent and create duplicate branches.
    """
    for step in steps:
        if await _cp._check_agent_done_on_sub_or_parent(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=issue_number,
            agent_name=step.agent_name,
            pipeline=pipeline,
        ):
            continue
        return step
    return None


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
            tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

        config = await _cp.get_workflow_config(project_id)
        if not config:
            # Auto-bootstrap a default workflow config so recovery can work
            # even after an app restart (the config is normally in-memory only)
            logger.info(
                "Recovery: no workflow config for project %s — bootstrapping default config",
                project_id,
            )
            config = _cp.WorkflowConfiguration(
                project_id=project_id,
                repository_owner=owner,
                repository_name=repo,
            )
            await _cp.set_workflow_config(project_id, config)

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

        now = utcnow()

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

            # ── Blocking queue guard ──────────────────────────────────────
            # If the issue is waiting in the blocking queue (pending behind a
            # blocking issue), do NOT attempt recovery — the queue will
            # activate it at the right time.  Without this check, recovery
            # sees an unassigned agent in the pre-created tracking table and
            # assigns it immediately, bypassing the serial blocking gate.
            try:
                from src.models.blocking import BlockingQueueStatus
                from src.services import blocking_queue as bq_service

                repo_key = f"{task_owner}/{task_repo}"
                bq_entry = await bq_service.get_entry(repo_key, issue_number)
                if bq_entry and bq_entry.queue_status == BlockingQueueStatus.PENDING:
                    logger.debug(
                        "Recovery: issue #%d is pending in blocking queue — skipping recovery",
                        issue_number,
                    )
                    continue
            except Exception:
                pass  # blocking queue unavailable — proceed with recovery

            # ── Read the issue body tracking table ────────────────────────
            try:
                issue_data = await _cp.github_projects_service.get_issue_with_comments(
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

            steps = _cp.parse_tracking_from_body(body)
            if not steps:
                # No tracking table — this issue wasn't created through our pipeline
                continue

            recovery_pipeline = _cp.get_pipeline_state(issue_number)

            # ── Determine expected agent ──────────────────────────────────
            # The active agent (🔄) is the one that should be working.
            # If there is no active agent, the next pending agent (⏳) needs
            # to be assigned.
            active_step = _cp.get_current_agent_from_tracking(body)
            pending_step = _cp.get_next_pending_agent(body)

            # If the tracking table says an earlier step is still pending
            # even though a later step is already done/active, the table is
            # stale. Recompute the current step from durable completion
            # signals before attempting any recovery assignment.
            if active_step is None and pending_step is not None:
                later_steps = [step for step in steps if step.index > pending_step.index]
                has_later_progress = any(
                    ("Done" in step.state or "Active" in step.state) for step in later_steps
                )
                if has_later_progress:
                    resolved_step = await _resolve_expected_agent_from_completion_signals(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=issue_number,
                        steps=steps,
                        pipeline=recovery_pipeline,
                    )
                    if resolved_step is not None and resolved_step.index != pending_step.index:
                        logger.warning(
                            "Recovery: issue #%d tracking table is stale/inconsistent "
                            "(first pending '%s' but later progress exists) — "
                            "using durable completion signals to resume at '%s' instead",
                            issue_number,
                            pending_step.agent_name,
                            resolved_step.agent_name,
                        )
                        pending_step = resolved_step
                    elif resolved_step is None:
                        logger.warning(
                            "Recovery: issue #%d tracking table is stale/inconsistent "
                            "and durable completion signals show all agents complete",
                            issue_number,
                        )
                        pending_step = None

            if active_step is None and pending_step is None:
                # All agents are ✅ Done for this status.  Check whether the
                # issue has already advanced beyond its current board status.
                # If it hasn't (e.g. the polling loop was down during the
                # transition window), force the transition now so the pipeline
                # always recovers without manual intervention.
                current_status = task.status or ""
                to_status = _cp.get_next_status(config, current_status) if config else None
                if not to_status or to_status.lower() == current_status.lower():
                    # No forward transition configured — genuinely nothing to do.
                    continue

                logger.warning(
                    "Recovery: issue #%d — all agents ✅ Done in '%s' but still "
                    "not transitioned to '%s' (polling was likely stopped during "
                    "the transition window) — forcing transition now",
                    issue_number,
                    current_status,
                    to_status,
                )
                _recovery_last_attempt[issue_number] = now

                try:
                    from .pipeline import _transition_after_pipeline_complete

                    trans_result = await _transition_after_pipeline_complete(
                        access_token=access_token,
                        project_id=project_id,
                        item_id=task.github_item_id,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=issue_number,
                        issue_node_id=task.github_content_id,
                        from_status=current_status,
                        to_status=to_status,
                        task_title=task.title or f"Issue #{issue_number}",
                    )
                    if trans_result:
                        results.append(
                            {
                                "status": "recovered_transition",
                                "issue_number": issue_number,
                                "from_status": current_status,
                                "to_status": to_status,
                                "pipeline_result": trans_result,
                            }
                        )
                        logger.info(
                            "Recovery: issue #%d successfully transitioned from '%s' to '%s'",
                            issue_number,
                            current_status,
                            to_status,
                        )
                except Exception as trans_err:
                    logger.error(
                        "Recovery: failed to force-transition issue #%d to '%s': %s",
                        issue_number,
                        to_status,
                        trans_err,
                    )
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

            # ── Non-coding agent guard ─────────────────────────────────
            # ``copilot-review`` and ``human`` are NOT traditional coding
            # agents — they don't have Copilot SWE assigned and don't
            # create WIP PRs.  Checking ``copilot_assigned`` and
            # ``has_wip_pr`` would always report False, causing recovery
            # to fire every cycle (wasting API calls and adding risk
            # of duplicate review requests).  Instead, check their own
            # completion signals directly and skip if not yet done.
            if agent_name in ("copilot-review", "human"):
                already_done = await _cp._check_agent_done_on_sub_or_parent(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    parent_issue_number=issue_number,
                    agent_name=agent_name,
                    pipeline=recovery_pipeline,
                )
                if already_done:
                    logger.debug(
                        "Recovery: non-coding agent '%s' on issue #%d already done — skipping",
                        agent_name,
                        issue_number,
                    )
                else:
                    logger.debug(
                        "Recovery: non-coding agent '%s' on issue #%d waiting "
                        "for external completion — skipping stall checks "
                        "(copilot_assigned / has_wip_pr do not apply)",
                        agent_name,
                        issue_number,
                    )
                _recovery_last_attempt[issue_number] = now
                continue

            # ── Check condition A: Copilot is assigned ────────────────────
            # With the sub-issue-per-agent model, Copilot is assigned to the
            # *sub-issue*, not the parent.  Check the sub-issue first to avoid
            # false "Copilot NOT assigned" reports that trigger needless
            # re-assignment (which can duplicate the agent session).
            copilot_assigned = False

            # Try sub-issue first
            sub_issue_number = _get_sub_issue_number(recovery_pipeline, agent_name, issue_number)
            if sub_issue_number != issue_number:
                copilot_assigned = await _cp.github_projects_service.is_copilot_assigned_to_issue(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=sub_issue_number,
                )

            # Fallback: check parent issue
            if not copilot_assigned:
                copilot_assigned = await _cp.github_projects_service.is_copilot_assigned_to_issue(
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
            main_branch_info = _cp.get_issue_main_branch(issue_number)

            linked_prs = await _cp.github_projects_service.get_linked_pull_requests(
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

                    if pr_state != "OPEN" or not _cp.github_projects_service.is_copilot_author(
                        pr_author
                    ):
                        continue

                    if not isinstance(pr_number, int):
                        continue

                    # Get full details to check draft status
                    pr_details = await _cp.github_projects_service.get_pull_request(
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
            already_done = await _cp._check_agent_done_on_sub_or_parent(
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
            agents_for_status = _cp.get_agent_slugs(config, agent_status)
            try:
                agent_index = agents_for_status.index(agent_name)
            except ValueError:
                logger.warning(
                    "Recovery: agent '%s' not found in mappings for status '%s'",
                    agent_name,
                    agent_status,
                )
                continue

            orchestrator = _cp.get_workflow_orchestrator()
            ctx = _cp.WorkflowContext(
                session_id="recovery",
                project_id=project_id,
                access_token=access_token,
                repository_owner=task_owner,
                repository_name=task_repo,
                issue_id=task.github_content_id,
                issue_number=issue_number,
                project_item_id=task.github_item_id,
                current_state=_cp.WorkflowState.READY,
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

    return results
