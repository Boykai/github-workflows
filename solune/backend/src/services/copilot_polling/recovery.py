"""Self-healing recovery: detect and fix stalled agent pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import src.services.copilot_polling as _cp
from src.constants import STALLED_LABEL
from src.logging_utils import get_logger
from src.models.agent import AgentStepState
from src.services.github_projects.identities import is_copilot_author
from src.utils import utcnow

from .helpers import _get_sub_issue_number
from .label_manager import ParsedLabel
from .pipeline import _wait_if_rate_limited
from .state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    RECOVERY_COOLDOWN_SECONDS,
    _pending_agent_assignments,
    _polling_state,
    _recovery_last_attempt,
)

logger = get_logger(__name__)


# ── Phase 8: Label-Driven State Recovery Models ──


@dataclass
class RecoveryState:
    """Represents the outcome of label-driven state recovery for a board item."""

    issue_number: int
    project_id: str
    source_labels: list[ParsedLabel] = field(default_factory=list)
    reconstructed_stage: str | None = None
    reconstructed_status: str | None = None
    confidence: str = "ambiguous"  # "high" | "medium" | "low" | "ambiguous"
    ambiguity_flags: list[str] = field(default_factory=list)
    requires_manual_review: bool = False
    recovered_at: datetime = field(default_factory=utcnow)
    recovery_source: str = "labels"  # "labels" | "database" | "mixed"


@dataclass
class RecoveryReport:
    """Summary of a full project-level recovery run."""

    project_id: str
    total_items: int = 0
    recovered_count: int = 0
    skipped_count: int = 0
    manual_review_count: int = 0
    states: list[RecoveryState] = field(default_factory=list)
    started_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None


async def _validate_and_reconcile_tracking_table(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    steps: list,
    pipeline: Any,
) -> tuple[str, list, bool]:
    """Validate every step in the tracking table against GitHub ground truth.

    GitHub is the source of truth — Done! markers in comments, PR reviews,
    and closed sub-issues are the real signals.  The tracking table in the
    issue body is a convenience display that can fall behind if a body-update
    API call fails or the process restarts mid-cycle.

    This function walks *every* step, checks its actual state via GitHub,
    and corrects the tracking table when it disagrees.

    Returns:
        (updated_body, updated_steps, table_was_corrected)
    """
    from src.services.agent_tracking import STATE_DONE

    corrections: list[str] = []

    for step in steps:
        is_done_in_github = await _cp._check_agent_done_on_sub_or_parent(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=issue_number,
            agent_name=step.agent_name,
            pipeline=pipeline,
        )

        step_state = AgentStepState.from_markdown(step.state)
        if is_done_in_github and step_state != AgentStepState.DONE:
            # GitHub says Done but tracking table says Active/Pending
            corrections.append(f"'{step.agent_name}' was {step.state} in table but Done in GitHub")
            step.state = STATE_DONE

    if not corrections:
        return body, steps, False

    logger.warning(
        "Recovery: issue #%d — tracking table out of sync with GitHub. Corrections: %s",
        issue_number,
        "; ".join(corrections),
    )

    # Rebuild the tracking table with corrected states and push to GitHub
    from src.services.agent_tracking import replace_tracking_section

    updated_body = replace_tracking_section(body, steps)

    try:
        await _cp.github_projects_service.update_issue_body(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            body=updated_body,
        )
        logger.info(
            "Recovery: issue #%d — reconciled tracking table (%d corrections pushed to GitHub)",
            issue_number,
            len(corrections),
        )
    except Exception as e:
        logger.warning(
            "Recovery: issue #%d — failed to push reconciled tracking table: %s "
            "(continuing with corrected in-memory state)",
            issue_number,
            e,
        )

    return updated_body, steps, True


async def _should_skip_recovery(
    issue_number: int,
    task_owner: str,
    task_repo: str,
    now: Any,
) -> bool:
    """Check if recovery should be skipped for this issue (cooldown)."""
    # Cooldown check
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
            return True

    return False


async def _attempt_reassignment(
    access_token: str,
    project_id: str,
    issue_number: int,
    task: Any,
    agent_name: str,
    agent_status: str,
    active_step: Any,
    missing: list[str],
    config: Any,
    now: Any,
) -> dict[str, Any] | None:
    """Re-assign a stalled agent. Returns a result dict or None."""
    task_owner = task.repository_owner
    task_repo = task.repository_name

    agents_for_status = _cp.get_agent_slugs(config, agent_status)
    try:
        agent_index = agents_for_status.index(agent_name)
    except ValueError:
        logger.warning(
            "Recovery: agent '%s' not found in mappings for status '%s'",
            agent_name,
            agent_status,
        )
        return None

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

    # Apply stalled label before re-assignment (non-blocking)
    try:
        await _cp.github_projects_service.update_issue_state(
            access_token=access_token,
            owner=task_owner,
            repo=task_repo,
            issue_number=issue_number,
            labels_add=[STALLED_LABEL],
        )
    except Exception as exc:
        logger.warning(
            "Non-blocking: failed to apply stalled label on issue #%d: %s",
            issue_number,
            exc,
        )

    # Check rate limit budget before recovery re-assignment
    if await _wait_if_rate_limited(
        f"recovery re-assignment '{agent_name}' on issue #{issue_number}"
    ):
        return None  # Defer to next recovery cycle

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
        return None

    _recovery_last_attempt[issue_number] = now

    if assigned:
        pending_key = f"{issue_number}:{agent_name}"
        _pending_agent_assignments[pending_key] = now

        result = {
            "status": "recovered",
            "issue_number": issue_number,
            "agent_name": agent_name,
            "agent_status": agent_status,
            "was_active": active_step is not None,
            "missing": missing,
        }
        logger.info(
            "Recovery: re-assigned agent '%s' for issue #%d (missing: %s)",
            agent_name,
            issue_number,
            ", ".join(missing),
        )
        return result
    else:
        logger.warning(
            "Recovery: assign_agent_for_status returned False for '%s' on issue #%d",
            agent_name,
            issue_number,
        )
        return None


async def _detect_stalled_issue(
    access_token: str,
    task_owner: str,
    task_repo: str,
    issue_number: int,
    agent_name: str,
    recovery_pipeline: Any,
) -> tuple[bool, bool, int | None]:
    """Check if a coding agent is stalled (missing assignment or WIP PR).

    Returns:
        (copilot_assigned, has_wip_pr, wip_pr_number)
    """
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

    # Check condition B: WIP (draft) PR exists
    has_wip_pr = False
    wip_pr_number = None

    main_branch_info = _cp.get_issue_main_branch(issue_number)

    linked_prs = await _cp.github_projects_service.get_linked_pull_requests(
        access_token=access_token,
        owner=task_owner,
        repo=task_repo,
        issue_number=issue_number,
    )

    if linked_prs:
        for pr in linked_prs:
            pr_num = pr.get("number")
            pr_state = (pr.get("state") or "").upper()
            pr_author = (pr.get("author") or "").lower()

            if pr_state != "OPEN" or not is_copilot_author(pr_author):
                continue

            if not isinstance(pr_num, int):
                continue

            pr_details = await _cp.github_projects_service.get_pull_request(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                pr_number=pr_num,
            )
            if not pr_details:
                continue

            is_draft = pr_details.get("is_draft", False)
            pr_base = pr_details.get("base_ref", "")

            if main_branch_info:
                main_branch = main_branch_info["branch"]
                main_pr = main_branch_info["pr_number"]

                if pr_num == main_pr:
                    if is_draft and not main_branch_info.get("head_sha"):
                        has_wip_pr = True
                        wip_pr_number = pr_num
                        break
                    continue

                if pr_base == main_branch or pr_base == "main":
                    has_wip_pr = True
                    wip_pr_number = pr_num
                    break
            else:
                has_wip_pr = True
                wip_pr_number = pr_num
                break

    return copilot_assigned, has_wip_pr, wip_pr_number


async def _check_copilot_session_health(
    access_token: str,
    task_owner: str,
    task_repo: str,
    issue_number: int,
    agent_name: str,
    wip_pr_number: int | None,
) -> bool:
    """Return True if the WIP PR has a healthy Copilot session (not errored/stopped)."""
    if not wip_pr_number:
        return True
    try:
        errored = await _cp.github_projects_service.check_copilot_session_error(
            access_token=access_token,
            owner=task_owner,
            repo=task_repo,
            pr_number=wip_pr_number,
        )
        return not errored
    except Exception as err:
        logger.debug(
            "Recovery: could not check Copilot session error on PR #%s for issue #%d: %s",
            wip_pr_number,
            issue_number,
            err,
        )
        return True


async def recover_stalled_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list | None = None,
) -> list[dict[str, Any]]:
    """
    Self-healing recovery check for all active issues (not yet Done).

    For every issue in Backlog / Ready / In Progress / In Review status:
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

        # Only "Done" is truly terminal — recovery must also check issues in
        # "In Review" because they can have stalled agents from earlier
        # statuses (e.g. an In-Progress agent whose assignment was lost
        # before the board moved forward).
        terminal_statuses = {
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
            "Recovery check: %d active issues (not yet Done)",
            len(active_tasks),
        )

        now = utcnow()

        for task in active_tasks:
            issue_number = task.issue_number
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo

            if not task_owner or not task_repo:
                continue

            # Cooldown guard
            if await _should_skip_recovery(issue_number, task_owner, task_repo, now):
                continue

            # NOTE: A label-based early exit was previously here, skipping
            # issues with an agent:* label on the assumption that the agent
            # is actively working.  However, having an agent label only
            # proves a Copilot assignment was *attempted* — Copilot may
            # have silently failed to start (no WIP PR).  When that
            # happens, both the pipeline check (which sees tracking=Active
            # and waits) and recovery (which skipped due to the label)
            # would deadlock — permanently stalling the pipeline.
            # Removed to allow recovery to always verify actual work.

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
                # No tracking table — attempt to self-heal from sub-issues
                # (mirrors the self-heal logic in _get_or_reconstruct_pipeline).
                from .pipeline import _self_heal_tracking_table

                healed_steps = await _self_heal_tracking_table(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=issue_number,
                    project_id=project_id,
                    body=body,
                )
                if not healed_steps:
                    # Genuinely no pipeline info — nothing to recover
                    continue
                steps = healed_steps
                # Re-read the body now that the tracking table has been
                # embedded so downstream helpers see the updated text.
                try:
                    refreshed = await _cp.github_projects_service.get_issue_with_comments(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=issue_number,
                    )
                    body = refreshed.get("body", body)
                except Exception as e:
                    logger.debug(
                        "Recovery: issue #%d — failed to re-fetch issue body after self-heal: %s "
                        "(continuing with stale body)",
                        issue_number,
                        e,
                        exc_info=True,
                    )

            recovery_pipeline = _cp.get_pipeline_state(issue_number)

            # ── Validate tracking table against GitHub (source of truth) ──
            # The tracking table can be stale/wrong if a body-update API
            # call failed.  Cross-reference every step with real GitHub
            # signals (Done! markers, PR reviews, closed sub-issues) and
            # correct the table before deciding what to do.
            body, steps, _table_was_corrected = await _validate_and_reconcile_tracking_table(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=issue_number,
                body=body,
                steps=steps,
                pipeline=recovery_pipeline,
            )

            # Determine expected agent from reconciled state (T041: use AgentStepState)
            active_step = None
            pending_step = None
            for step in steps:
                step_state = AgentStepState.from_markdown(step.state)
                if step_state == AgentStepState.DONE:
                    continue
                if step_state == AgentStepState.ACTIVE:
                    active_step = step
                    break
                if step_state == AgentStepState.QUEUED and pending_step is None:
                    pending_step = step
                    break

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
                    # Set cooldown to avoid re-checking every cycle.
                    _recovery_last_attempt[issue_number] = now
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
            # ── Check condition B: WIP (draft) PR exists ─────────────────
            copilot_assigned, has_wip_pr, wip_pr_number = await _detect_stalled_issue(
                access_token=access_token,
                task_owner=task_owner,
                task_repo=task_repo,
                issue_number=issue_number,
                agent_name=agent_name,
                recovery_pipeline=recovery_pipeline,
            )

            # ── Evaluate whether recovery is needed ───────────────────────
            if copilot_assigned and has_wip_pr:
                # Both conditions met — but Copilot may have errored/stopped.
                session_healthy = await _check_copilot_session_health(
                    access_token=access_token,
                    task_owner=task_owner,
                    task_repo=task_repo,
                    issue_number=issue_number,
                    agent_name=agent_name,
                    wip_pr_number=wip_pr_number,
                )

                if session_healthy:
                    logger.debug(
                        "Recovery: issue #%d OK — agent '%s' assigned and WIP PR #%s exists",
                        issue_number,
                        agent_name,
                        wip_pr_number,
                    )
                    continue

                # Copilot errored/stopped on the WIP PR — treat as stalled
                logger.warning(
                    "Recovery: issue #%d — agent '%s' has WIP PR #%s but "
                    "Copilot stopped/errored. Will re-assign.",
                    issue_number,
                    agent_name,
                    wip_pr_number,
                )

            # Something is wrong — log what's missing
            missing = []
            if not copilot_assigned:
                missing.append("Copilot NOT assigned")
            if not has_wip_pr:
                missing.append("no WIP PR found")
            if copilot_assigned and has_wip_pr:
                missing.append(f"Copilot errored/stopped on PR #{wip_pr_number}")

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

            # ── Guard: check for a merged child PR without Done! marker ──
            # If the child PR was merged but processing was interrupted
            # before the Done! comment was posted, the agent DID complete
            # successfully.  Post the missing marker to self-heal and skip
            # re-assignment — otherwise recovery creates a duplicate PR.
            main_branch_info = _cp.get_issue_main_branch(issue_number)
            if main_branch_info:
                merged_child = await _cp._find_completed_child_pr(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=issue_number,
                    main_branch=main_branch_info["branch"],
                    main_pr_number=main_branch_info["pr_number"],
                    agent_name=agent_name,
                    pipeline=recovery_pipeline,
                )
                if merged_child and merged_child.get("is_merged"):
                    logger.warning(
                        "Recovery: issue #%d — agent '%s' has MERGED child PR #%s "
                        "but no Done! marker. Self-healing: posting marker and "
                        "skipping re-assignment (problems were: %s)",
                        issue_number,
                        agent_name,
                        merged_child["number"],
                        ", ".join(missing),
                    )
                    # Post the missing Done! marker so subsequent cycles
                    # detect completion via the normal comment-based path.
                    marker = f"{agent_name}: Done!"
                    try:
                        await _cp.github_projects_service.create_issue_comment(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=issue_number,
                            body=marker,
                        )
                    except Exception as marker_err:
                        logger.warning(
                            "Recovery: issue #%d — failed to post Done! marker "
                            "for '%s': %s (skipping re-assignment anyway)",
                            issue_number,
                            agent_name,
                            marker_err,
                        )
                    _recovery_last_attempt[issue_number] = now
                    continue
                elif merged_child:
                    # Child PR exists and is completed but NOT yet merged.
                    # The agent DID finish its work — do not re-assign.
                    # Post the Done! marker; the safety-net merge in
                    # _advance_pipeline will handle merging the PR.
                    logger.warning(
                        "Recovery: issue #%d — agent '%s' has COMPLETED (but "
                        "unmerged) child PR #%s. Self-healing: posting Done! "
                        "marker and skipping re-assignment (problems were: %s)",
                        issue_number,
                        agent_name,
                        merged_child["number"],
                        ", ".join(missing),
                    )
                    marker = f"{agent_name}: Done!"
                    try:
                        await _cp.github_projects_service.create_issue_comment(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=issue_number,
                            body=marker,
                        )
                    except Exception as marker_err:
                        logger.warning(
                            "Recovery: issue #%d — failed to post Done! marker "
                            "for '%s': %s (skipping re-assignment anyway)",
                            issue_number,
                            agent_name,
                            marker_err,
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

            # ── Alert dispatch: pipeline_stall (Phase 5) ──
            try:
                from src.config import get_settings as _get_settings

                _settings = _get_settings()
                # Estimate stall duration from recovery cooldown history
                last_attempt_ts = _recovery_last_attempt.get(issue_number)
                stall_minutes = (
                    int((now - last_attempt_ts).total_seconds() / 60)
                    if last_attempt_ts
                    else _settings.pipeline_stall_alert_minutes
                )
                if stall_minutes >= _settings.pipeline_stall_alert_minutes:
                    from src.services.alert_dispatcher import get_dispatcher

                    dispatcher = get_dispatcher()
                    if dispatcher is not None:
                        await dispatcher.dispatch_alert(
                            alert_type="pipeline_stall",
                            summary=(
                                f"Pipeline stall detected: issue #{issue_number} "
                                f"stalled for {stall_minutes} minutes"
                            ),
                            details={
                                "issue_number": issue_number,
                                "stall_duration_minutes": stall_minutes,
                                "threshold_minutes": _settings.pipeline_stall_alert_minutes,
                                "pipeline_state": "active" if active_step else "pending",
                            },
                        )
            except Exception as alert_err:
                logger.debug("Failed to dispatch pipeline_stall alert: %s", alert_err)

            # Re-assign the agent (T040)
            result = await _attempt_reassignment(
                access_token=access_token,
                project_id=project_id,
                issue_number=issue_number,
                task=task,
                agent_name=agent_name,
                agent_status=agent_status,
                active_step=active_step,
                missing=missing,
                config=config,
                now=now,
            )
            if result:
                results.append(result)

    except Exception as e:
        logger.error("Error in recovery check: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = f"Recovery error: {e}"

    return results


# ── Phase 8: Label-Driven State Recovery (T027-T032) ──


def batch_parse_pipeline_labels(
    items: list[dict[str, Any]],
) -> dict[int, list[ParsedLabel]]:
    """Parse all ``solune:pipeline:*`` labels on a list of board items.

    Args:
        items: Board items, each with an ``issue_number`` and ``labels`` list.

    Returns:
        Mapping of issue_number → list of parsed pipeline labels.
    """
    from .label_manager import parse_label

    result: dict[int, list[ParsedLabel]] = {}
    for item in items:
        issue_number = item.get("number") or item.get("issue_number")
        if not issue_number:
            continue
        labels_data = item.get("labels", [])
        parsed: list[ParsedLabel] = []
        for label in labels_data:
            name = label.get("name", "") if isinstance(label, dict) else getattr(label, "name", "")
            p = parse_label(name)
            if p:
                parsed.append(p)
        if parsed:
            result[int(issue_number)] = parsed
    return result


def recover_single_item_state(
    issue_number: int,
    project_id: str,
    labels: list[ParsedLabel],
) -> RecoveryState:
    """Reconstruct a ``RecoveryState`` from parsed labels for one item.

    Applies confidence scoring:
    - **high**: Exactly one latest-status label per stage → unambiguous.
    - **medium**: Multiple stages but labels are consistent.
    - **low**: Partial information, some guessing required.
    - **ambiguous**: Conflicting labels → requires manual review.
    """
    state = RecoveryState(
        issue_number=issue_number,
        project_id=project_id,
        source_labels=list(labels),
    )

    if not labels:
        state.confidence = "ambiguous"
        state.ambiguity_flags.append("no_pipeline_labels_found")
        state.requires_manual_review = True
        return state

    # Group by stage_id → latest status per stage
    stages: dict[str, list[ParsedLabel]] = {}
    for lbl in labels:
        stages.setdefault(lbl.stage_id, []).append(lbl)

    # Find the latest run_id (most recent pipeline run)
    max_run_id = max(lbl.run_id for lbl in labels)
    latest_labels = [lbl for lbl in labels if lbl.run_id == max_run_id]

    if not latest_labels:
        state.confidence = "ambiguous"
        state.ambiguity_flags.append("no_labels_for_latest_run")
        state.requires_manual_review = True
        return state

    # Determine current stage from latest labels
    latest_stages: dict[str, list[ParsedLabel]] = {}
    for lbl in latest_labels:
        latest_stages.setdefault(lbl.stage_id, []).append(lbl)

    # Check for conflicting statuses within same stage
    conflicting = False
    for stage_id, stage_labels in latest_stages.items():
        statuses = {lbl.status for lbl in stage_labels}
        if len(statuses) > 1:
            conflicting = True
            state.ambiguity_flags.append(f"conflicting_statuses_in_{stage_id}: {statuses}")

    if conflicting:
        state.confidence = "ambiguous"
        state.requires_manual_review = True
        return state

    # Find the most advanced stage (running > pending > completed)
    priority = {"running": 3, "pending": 2, "failed": 1, "completed": 0, "skipped": -1}
    best_stage = None
    best_status = None
    best_priority = -2
    for stage_id, stage_labels in latest_stages.items():
        status = stage_labels[0].status
        p = priority.get(status, -1)
        if p > best_priority:
            best_priority = p
            best_stage = stage_id
            best_status = status

    state.reconstructed_stage = best_stage
    state.reconstructed_status = best_status

    if len(latest_stages) == 1 and not state.ambiguity_flags:
        state.confidence = "high"
    elif len(latest_stages) > 1 and not state.ambiguity_flags:
        state.confidence = "medium"
    else:
        state.confidence = "low"

    return state


async def recover_pipeline_states_from_labels(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    items: list[dict[str, Any]] | None = None,
) -> RecoveryReport:
    """Orchestrate full project-level state recovery from GitHub labels.

    1. Lists all board items (or uses provided items).
    2. Parses pipeline labels from each item.
    3. Reconstructs pipeline states with confidence scoring.
    4. Populates the pipeline state store for high/medium confidence items.
    5. Flags ambiguous items for manual review.

    Args:
        access_token: GitHub access token.
        project_id: Project ID.
        owner: Repository owner.
        repo: Repository name.
        items: Optional pre-fetched board items.

    Returns:
        RecoveryReport summarizing the recovery run.
    """
    report = RecoveryReport(project_id=project_id)

    if items is None:
        # Fetch items from the board
        try:
            from src.services.github_projects import github_projects_service

            board_data = await github_projects_service.get_project_items(access_token, project_id)
            # get_project_items returns list[Task]; convert to list[dict] since
            # batch_parse_pipeline_labels accesses both .get() and attribute paths.
            items = (
                [t.model_dump(mode="json") for t in board_data]
                if isinstance(board_data, list)
                else []
            )
        except Exception:
            logger.exception("Failed to fetch board items for recovery")
            items = []

    report.total_items = len(items)

    # Parse labels from all items
    item_labels = batch_parse_pipeline_labels(items)
    if not item_labels:
        logger.info("No pipeline labels found for project %s — nothing to recover", project_id)
        report.completed_at = utcnow()
        return report

    # Recover each item
    for issue_number, labels in item_labels.items():
        recovery_state = recover_single_item_state(issue_number, project_id, labels)
        report.states.append(recovery_state)

        if recovery_state.requires_manual_review:
            report.manual_review_count += 1
            logger.warning(
                "Issue #%d requires manual review: %s",
                issue_number,
                recovery_state.ambiguity_flags,
            )
            continue

        if recovery_state.confidence in ("high", "medium"):
            report.recovered_count += 1
            logger.info(
                "Recovered state for issue #%d: stage=%s status=%s confidence=%s",
                issue_number,
                recovery_state.reconstructed_stage,
                recovery_state.reconstructed_status,
                recovery_state.confidence,
            )
        else:
            report.skipped_count += 1

    report.completed_at = utcnow()
    logger.info(
        "Recovery complete for project %s: %d recovered, %d skipped, %d manual review",
        project_id,
        report.recovered_count,
        report.skipped_count,
        report.manual_review_count,
    )

    # Persist recovery log
    await _persist_recovery_log(report)

    return report


async def _persist_recovery_log(report: RecoveryReport) -> None:
    """Persist recovery states to the recovery_log table."""
    import json

    try:
        from src.services.database import get_db

        db = get_db()
        for state in report.states:
            source_labels_json = json.dumps(
                [
                    {
                        "run_id": lbl.run_id,
                        "stage_id": lbl.stage_id,
                        "status": lbl.status,
                        "full_name": lbl.full_name,
                    }
                    for lbl in state.source_labels
                ]
            )
            ambiguity_json = json.dumps(state.ambiguity_flags)
            await db.execute(
                "INSERT OR REPLACE INTO recovery_log "
                "(issue_number, project_id, source_labels_json, reconstructed_stage, "
                "reconstructed_status, confidence, ambiguity_flags_json, "
                "requires_manual_review, recovered_at, recovery_source) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    state.issue_number,
                    state.project_id,
                    source_labels_json,
                    state.reconstructed_stage,
                    state.reconstructed_status,
                    state.confidence,
                    ambiguity_json,
                    int(state.requires_manual_review),
                    state.recovered_at.isoformat(),
                    state.recovery_source,
                ),
            )
        await db.commit()
    except Exception:
        logger.exception("Failed to persist recovery log")
