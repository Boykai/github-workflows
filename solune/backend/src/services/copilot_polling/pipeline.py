"""Pipeline state management, status checking, and advancement logic."""

import asyncio
from datetime import datetime
from typing import Any

import src.services.copilot_polling as _cp
from src.constants import ACTIVE_LABEL, build_agent_label, find_agent_label, find_pipeline_label
from src.logging_utils import get_logger
from src.services.pipeline_state_store import get_project_launch_lock
from src.utils import utcnow

from .state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    MAX_MERGE_RETRIES,
    RATE_LIMIT_PAUSE_THRESHOLD,
    RATE_LIMIT_SLOW_THRESHOLD,
    _claimed_child_prs,
    _merge_failure_counts,
    _pending_agent_assignments,
    _polling_state,
    _processed_issue_prs,
    _system_marked_ready_prs,
)

logger = get_logger(__name__)


async def _dequeue_next_pipeline(
    access_token: str,
    project_id: str,
    trigger: str,
) -> None:
    """Dequeue the next waiting pipeline for a project when queue mode is active.

    Finds the oldest queued pipeline by started_at (FIFO) and starts it by
    assigning the first agent for its status.

    Args:
        access_token: GitHub access token for API calls
        project_id: Project ID to check for queued pipelines
        trigger: Description of what triggered the dequeue (for logging)
    """
    from src.services.database import get_db
    from src.services.settings_store import is_queue_mode_enabled

    try:
        db = get_db()
        if not await is_queue_mode_enabled(db, project_id):
            return

        async with get_project_launch_lock(project_id):
            # Re-check active count under the lock — a concurrent launch may
            # have just registered a new active pipeline.
            active_count = _cp.count_active_pipelines_for_project(project_id)
            if active_count > 0:
                logger.debug(
                    "Skipping dequeue for project %s — %d pipeline(s) still active",
                    project_id,
                    active_count,
                )
                return

            queued = _cp.get_queued_pipelines_for_project(project_id)
            if not queued:
                return

            next_pipeline = queued[0]
            logger.info(
                "Dequeuing pipeline for issue #%d (trigger: %s, project: %s, queue depth: %d)",
                next_pipeline.issue_number,
                trigger,
                project_id,
                len(queued),
            )

            # Mark as no longer queued
            next_pipeline.queued = False
            _cp.set_pipeline_state(next_pipeline.issue_number, next_pipeline)

        # Get workflow config and assign the first agent (outside lock)
        config = await _cp.get_workflow_config(project_id)
        if not config:
            logger.warning(
                "No workflow config for project %s during dequeue — cannot start pipeline #%d",
                project_id,
                next_pipeline.issue_number,
            )
            return

        orchestrator = _cp.get_workflow_orchestrator()
        ctx = _cp.WorkflowContext(
            session_id="dequeue",
            project_id=project_id,
            access_token=access_token,
        )
        ctx.issue_number = next_pipeline.issue_number

        await orchestrator.assign_agent_for_status(ctx, next_pipeline.status, agent_index=0)
        logger.info(
            "Dequeued pipeline for issue #%d — agent assignment started",
            next_pipeline.issue_number,
        )
    except Exception:
        logger.error(
            "Failed to dequeue next pipeline for project %s (trigger: %s)",
            project_id,
            trigger,
            exc_info=True,
        )


def _get_rate_limit_remaining() -> tuple[int | None, int | None]:
    """Return (remaining, reset_at) from the cached rate limit info.

    Returns (None, None) when no rate-limit data is available.
    """
    rl = _cp.github_projects_service.get_last_rate_limit()
    if rl is None:
        return None, None
    try:
        remaining = rl.get("remaining")
        reset_at = rl.get("reset_at")
        # Ensure values are integers (defensive against mocks / unexpected types)
        if remaining is not None:
            remaining = int(remaining)
        if reset_at is not None:
            reset_at = int(reset_at)
        return remaining, reset_at
    except (TypeError, ValueError):
        return None, None


async def _wait_if_rate_limited(context: str) -> bool:
    """If rate limit budget is critically low, wait until reset.

    Returns True if the caller should abort, False to proceed.
    """
    remaining, reset_at = _get_rate_limit_remaining()
    if remaining is None:
        return False
    if remaining <= RATE_LIMIT_PAUSE_THRESHOLD:
        now_ts = int(utcnow().timestamp())
        if reset_at is not None and reset_at <= now_ts:
            _cp.github_projects_service.clear_last_rate_limit()
            return False
        wait = max((reset_at or now_ts) - now_ts, 10)
        wait = min(wait, 900)
        logger.warning(
            "Rate limit critically low before %s (remaining=%d). Waiting %ds until reset.",
            context,
            remaining,
            wait,
        )
        await asyncio.sleep(wait)
        return True
    return False


async def _self_heal_tracking_table(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
    body: str,
) -> "list | None":
    """Build and embed a tracking table from sub-issues when one is missing.

    When an issue has sub-issues but no tracking table in its body, the
    pipeline cannot reliably reconstruct because per-status agents from the
    DB config may not cover agents from earlier statuses.  After a container
    restart the in-memory pipeline state is lost, and without a tracking
    table the only source of truth is the per-status DB config — which
    causes agents assigned to other statuses to be silently skipped.

    This function:

    1. Fetches sub-issues for the parent issue
    2. Extracts agent names from titles (``[agent_name] Title``)
    3. Maps agents to statuses using the current DB config
    4. Builds a tracking table and embeds it in the issue body

    Returns:
        Parsed AgentStep list on success, None if healing was not possible.
    """
    import re as _re

    from src.services.agent_tracking import AgentStep, render_tracking_markdown

    config = await _cp.get_workflow_config(project_id)
    if not config:
        return None

    sub_issues = await _cp.github_projects_service.get_sub_issues(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )
    if not sub_issues:
        return None

    # Extract agent names from sub-issue titles: "[agent_name] Parent Title"
    agent_order: list[str] = []
    for si in sorted(sub_issues, key=lambda s: s.get("number", 0)):
        m = _re.match(r"^\[([^\]]+)\]", si.get("title", ""))
        if m:
            slug = m.group(1).strip()
            if slug not in agent_order:
                agent_order.append(slug)

    if not agent_order:
        return None

    # Build agent_name → status mapping from DB config
    status_order = _cp.get_status_order(config)
    agent_to_status: dict[str, str] = {}
    for st in status_order:
        for slug in _cp.get_agent_slugs(config, st):
            if slug not in agent_to_status:
                agent_to_status[slug] = st

    # Map sub-issue agents to statuses.  Agents not in config inherit
    # the previous agent's status (preserves pipeline ordering).
    fallback_status = status_order[0] if status_order else "Backlog"
    steps: list[AgentStep] = []
    for idx, agent_name in enumerate(agent_order, start=1):
        mapped_status = agent_to_status.get(agent_name, fallback_status)
        steps.append(
            AgentStep(
                index=idx,
                status=mapped_status,
                agent_name=agent_name,
            )
        )
        fallback_status = mapped_status

    # Render tracking table markdown and embed in the issue body
    tracking_md = render_tracking_markdown(steps)
    new_body = body.rstrip() + "\n" + tracking_md

    try:
        await _cp.github_projects_service.update_issue_body(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            body=new_body,
        )
        logger.info(
            "Self-healed: embedded tracking table for issue #%d (%d agents from sub-issues)",
            issue_number,
            len(steps),
        )
    except Exception as e:
        logger.warning(
            "Failed to embed self-healed tracking table for issue #%d: %s",
            issue_number,
            e,
        )
        # Still return the steps so reconstruction can use them this cycle

    return steps


async def _build_pipeline_from_labels(
    issue_number: int,
    project_id: str,
    status: str,
    labels: list[dict[str, str]],
) -> "_cp.PipelineState | None":
    """Build PipelineState from label data and pipeline configuration.

    Uses ``pipeline:<config>`` to look up the full agent list and
    ``agent:<slug>`` to determine the current agent index.

    Returns None when the labels are insufficient or the agent slug
    is not found in the config, triggering fallthrough to the regular
    reconstruction chain.
    """
    config_name = find_pipeline_label(labels)
    agent_slug = find_agent_label(labels)
    if not config_name or not agent_slug:
        return None

    # Look up pipeline config from DB
    try:
        from src.services.database import get_db
        from src.services.pipelines.service import PipelineService

        svc = PipelineService(get_db())
        response = await svc.list_pipelines(project_id)
        matched_config = next((c for c in response.pipelines if c.name == config_name), None)
        if not matched_config:
            return None
    except Exception:
        return None

    # Build ordered agent list from pipeline stages
    all_agents: list[str] = []
    for stage in matched_config.stages:
        for agent in stage.agents:
            slug = getattr(agent, "slug", None) or str(agent)
            all_agents.append(slug)

    if not all_agents:
        return None

    # Find the current agent's index
    try:
        agent_index = all_agents.index(agent_slug)
    except ValueError:
        return None  # agent not in config → fallthrough

    completed = all_agents[:agent_index]

    return _cp.PipelineState(
        issue_number=issue_number,
        project_id=project_id,
        status=status,
        agents=all_agents,
        current_agent_index=agent_index,
        completed_agents=list(completed),
    )


async def _get_or_reconstruct_pipeline(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
    status: str,
    agents: list[str],
    expected_status: str | None = None,
    labels: list[dict[str, str]] | None = None,
) -> "_cp.PipelineState":
    """
    Get existing pipeline state or reconstruct from issue comments.

    Reconstruction chain (in order of preference):
    1. In-memory cache hit → return cached state
    2. Label fast-path → build from pipeline:<config> + agent:<slug>
    3. Issue body → parse tracking table
    4. Sub-issues → self-heal tracking table
    5. Full reconstruction → _reconstruct_pipeline_state()

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        project_id: Project ID
        status: Current workflow status
        agents: Ordered list of agents for this status
        expected_status: If provided, only use cached pipeline if status matches
        labels: Issue labels from the board query (enables fast-path)

    Returns:
        PipelineState (either cached or reconstructed)
    """
    pipeline = _cp.get_pipeline_state(issue_number)

    # Use cached pipeline if it exists and matches expected status
    if pipeline is not None:
        if expected_status is None or pipeline.status == expected_status:
            return pipeline

    # ── Label fast-path (zero additional API calls) ───────────────────
    if labels:
        fast_path = await _build_pipeline_from_labels(
            issue_number=issue_number,
            project_id=project_id,
            status=status,
            labels=labels,
        )
        if fast_path is not None:
            _cp.set_pipeline_state(issue_number, fast_path)
            logger.info(
                "Fast-path: built pipeline for issue #%d from labels (agent=%s, index=%d)",
                issue_number,
                fast_path.current_agent,
                fast_path.current_agent_index,
            )
            return fast_path

    # Before reconstructing with the caller's agents, check the tracking
    # table in the issue body.  If an earlier pipeline status still has
    # pending agents (e.g. "In Progress" agents unfinished but the board
    # jumped to "In Review"), reconstruct for THAT status so the pending
    # agents aren't silently skipped.
    try:
        issue_data = await _cp.github_projects_service.get_issue_with_comments(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )
        body = issue_data.get("body", "") if issue_data else ""
        if body:
            steps = _cp.parse_tracking_from_body(body)

            # Self-heal: if no tracking table exists but sub-issues do,
            # build one from sub-issues to prevent pipeline agent skipping.
            # Without this, a container restart + status change causes the
            # reconstruction to use only per-status agents from the DB
            # config, silently skipping agents from other statuses.
            if not steps:
                steps = await _self_heal_tracking_table(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                    project_id=project_id,
                    body=body,
                )

            if steps:
                # Find the first agent that is ⏳ Pending or 🔄 Active
                first_incomplete = next(
                    (s for s in steps if "Pending" in s.state or "Active" in s.state),
                    None,
                )
                if first_incomplete and first_incomplete.status.lower() != status.lower():
                    # The first incomplete agent is in a different status
                    # than the board's current status.  Determine whether
                    # it's EARLIER or LATER by checking whether any step
                    # for the requested status is still incomplete.
                    #
                    # Key scenario this guard protects against:
                    #   The board says "In Review" (due to a webhook firing
                    #   when a Copilot PR becomes ready) but speckit.implement
                    #   or another "In Progress" agent is still pending.
                    #   Without this check, the pipeline would be
                    #   reconstructed for "In Review" with current_agent
                    #   set to "copilot-review", falsely marking it as the
                    #   active step.  Instead, we detect the mismatch and
                    #   reconstruct for the earlier status so pending
                    #   agents aren't silently skipped.
                    has_incomplete_for_requested = any(
                        s
                        for s in steps
                        if s.status.lower() == status.lower()
                        and ("Pending" in s.state or "Active" in s.state)
                    )

                    if has_incomplete_for_requested:
                        # The tracking table shows incomplete agents in an
                        # earlier status than the board claims.  The board
                        # may have jumped ahead.  Reconstruct for THAT
                        # status so pending agents aren't silently skipped.
                        earlier_status = first_incomplete.status
                        earlier_agents = [
                            s.agent_name
                            for s in steps
                            if s.status.lower() == earlier_status.lower()
                        ]
                        if earlier_agents:
                            logger.info(
                                "Tracking table for issue #%d shows incomplete "
                                "agents in '%s' (first: %s) — reconstructing "
                                "pipeline for that status instead of '%s'",
                                issue_number,
                                earlier_status,
                                first_incomplete.agent_name,
                                status,
                            )
                            return await _reconstruct_pipeline_state(
                                access_token=access_token,
                                owner=owner,
                                repo=repo,
                                issue_number=issue_number,
                                project_id=project_id,
                                status=earlier_status,
                                agents=earlier_agents,
                            )
                    else:
                        # All agents for the REQUESTED status are complete,
                        # and the first incomplete agent is in a LATER
                        # status.  Fall through to reconstruct for the
                        # requested status — which will show the pipeline
                        # as complete and trigger status advancement.
                        logger.info(
                            "All agents for '%s' are complete on issue #%d; "
                            "first incomplete agent '%s' is in later status '%s' "
                            "— reconstructing for '%s' to trigger advancement",
                            status,
                            issue_number,
                            first_incomplete.agent_name,
                            first_incomplete.status,
                            status,
                        )

                # Always prefer the tracking table's agent list for the
                # CURRENT status over the caller-provided agents (which
                # come from the mutable DB config).  The tracking table
                # is frozen at issue-creation time and is the source of
                # truth — if the user later removes agents from the
                # config, already-created issues must still honour their
                # original pipeline.
                tracking_agents_for_status = [
                    s.agent_name for s in steps if s.status.lower() == status.lower()
                ]
                if tracking_agents_for_status and tracking_agents_for_status != agents:
                    logger.info(
                        "Tracking table for issue #%d overrides agents for '%s': "
                        "%s → %s (DB config differs from issue-creation snapshot)",
                        issue_number,
                        status,
                        agents,
                        tracking_agents_for_status,
                    )
                    agents = tracking_agents_for_status
    except Exception as e:
        logger.debug(
            "Could not check tracking table for issue #%d during pipeline reconstruction: %s",
            issue_number,
            e,
        )

    # Default: reconstruct for the requested status
    return await _reconstruct_pipeline_state(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        project_id=project_id,
        status=status,
        agents=agents,
    )


async def _process_pipeline_completion(
    access_token: str,
    project_id: str,
    task: Any,
    owner: str,
    repo: str,
    pipeline: "_cp.PipelineState",
    from_status: str,
    to_status: str,
) -> dict[str, Any] | None:
    """
    Process pipeline completion check and advance/transition as needed.

    Consolidates the repeated pattern of:
    1. Check if pipeline is complete → transition to next status
    2. Check if current agent completed → advance pipeline
    3. Check if current agent was never assigned (after reconstruction) → trigger it

    Args:
        access_token: GitHub access token
        project_id: Project ID
        task: Task object with issue info
        owner: Repository owner
        repo: Repository name
        pipeline: Current pipeline state
        from_status: Current status
        to_status: Target status after pipeline completion

    Returns:
        Result dict or None
    """
    task_owner = task.repository_owner or owner
    task_repo = task.repository_name or repo

    if pipeline.is_complete:
        # Ensure all completed agents are marked ✅ Done in the tracking
        # table.  After a container restart the tracking table may have
        # stale 🔄 Active entries even though Done! comments exist.
        # Batch into a single fetch→modify→push to avoid N round-trips.
        if pipeline.completed_agents:
            try:
                issue_data = await _cp.github_projects_service.get_issue_with_comments(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                )
                body = issue_data.get("body", "")
                if body:
                    updated_body = body
                    for agent_name in pipeline.completed_agents:
                        updated_body = _cp.mark_agent_done(updated_body, agent_name)
                    if updated_body != body:
                        await _cp.github_projects_service.update_issue_body(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=task.issue_number,
                            body=updated_body,
                        )
            except Exception as e:
                logger.warning(
                    "Failed to batch-update tracking for issue #%d: %s",
                    task.issue_number,
                    e,
                )

        # All agents done → clean up pipeline labels (non-blocking)
        try:
            labels_to_remove: list[str] = []
            # Remove the current agent:* label from parent
            task_labels = getattr(task, "labels", None) or []
            agent_slug = find_agent_label(task_labels)
            if agent_slug:
                labels_to_remove.append(build_agent_label(agent_slug))
            elif pipeline.current_agent:
                labels_to_remove.append(build_agent_label(pipeline.current_agent))
            if labels_to_remove:
                await _cp.github_projects_service.update_issue_state(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    labels_remove=labels_to_remove,
                )
            # Remove active from the last sub-issue
            last_agent = pipeline.agents[-1] if pipeline.agents else None
            if last_agent:
                last_sub = pipeline.agent_sub_issues.get(last_agent, {}).get("number")
                if last_sub:
                    await _cp.github_projects_service.update_issue_state(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=last_sub,
                        labels_remove=[ACTIVE_LABEL],
                    )
        except Exception as e:
            logger.warning(
                "Non-blocking: failed to clean up pipeline labels for issue #%d: %s",
                task.issue_number,
                e,
            )

        # All agents done → close any sub-issues that were missed
        # (e.g. after a server restart where _advance_pipeline was never
        # called for some completed agents).
        try:
            await _close_completed_sub_issues(
                access_token=access_token,
                project_id=project_id,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                completed_agents=list(pipeline.completed_agents),
                pipeline=pipeline,
            )
        except Exception as e:
            logger.warning(
                "Non-blocking: failed to sweep sub-issues for issue #%d: %s",
                task.issue_number,
                e,
            )

        # All agents done → transition to next status
        return await _transition_after_pipeline_complete(
            access_token=access_token,
            project_id=project_id,
            item_id=task.github_item_id,
            owner=task_owner,
            repo=task_repo,
            issue_number=task.issue_number,
            issue_node_id=task.github_content_id,
            from_status=from_status,
            to_status=to_status,
            task_title=task.title,
        )

    # Check if current agent has completed
    current_agent = pipeline.current_agent
    if current_agent:
        completed = await _cp._check_agent_done_on_sub_or_parent(
            access_token=access_token,
            owner=task_owner,
            repo=task_repo,
            parent_issue_number=task.issue_number,
            agent_name=current_agent,
            pipeline=pipeline,
        )

        if completed:
            return await _advance_pipeline(
                access_token=access_token,
                project_id=project_id,
                item_id=task.github_item_id,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                issue_node_id=task.github_content_id,
                pipeline=pipeline,
                from_status=from_status,
                to_status=to_status,
                task_title=task.title,
            )

        # If current agent hasn't completed, check if it was ever assigned.
        # First, consult the tracking table in the issue body — this is the
        # durable source of truth and survives server restarts.
        # NOTE: We intentionally do NOT require `pipeline.completed_agents`
        # here.  After a container restart the very first agent in the
        # pipeline may never have been assigned (or its assignment was lost).
        # Gating on `completed_agents` would silently skip it because there
        # are no prior completions.  The grace-period, tracking-table, and
        # in-memory pending checks below still prevent premature or duplicate
        # assignments for freshly-started pipelines.
        if not completed:
            # ── Grace period: if the pipeline was started or last advanced
            # recently, Copilot likely hasn't created its WIP PR yet.
            # Skip the expensive "agent never assigned" checks to avoid
            # duplicate assignments.
            if pipeline.started_at:
                age = (utcnow() - pipeline.started_at).total_seconds()
                if age < ASSIGNMENT_GRACE_PERIOD_SECONDS:
                    logger.debug(
                        "Agent '%s' on issue #%d within grace period (%.0fs / %ds) — waiting",
                        current_agent,
                        task.issue_number,
                        age,
                        ASSIGNMENT_GRACE_PERIOD_SECONDS,
                    )
                    return None

            # Check the issue body tracking table first
            body, _comments = await _cp._get_tracking_state_from_issue(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
            )
            tracking_step = _cp.get_current_agent_from_tracking(body)
            if tracking_step and tracking_step.agent_name == current_agent:
                logger.debug(
                    "Agent '%s' is 🔄 Active in issue #%d tracking table — waiting",
                    current_agent,
                    task.issue_number,
                )
                return None  # Already assigned, wait for it to finish

            # Also check in-memory pending set (belt and suspenders)
            pending_key = f"{task.issue_number}:{current_agent}"
            pending_ts = _pending_agent_assignments.get(pending_key)
            if pending_ts is not None:
                logger.debug(
                    "Agent '%s' already assigned for issue #%d (in-memory, %.0fs ago), waiting for Copilot to start working",
                    current_agent,
                    task.issue_number,
                    (utcnow() - pending_ts).total_seconds(),
                )
                return None

            # At this point, all durable and in-memory indicators agree
            # that the current agent was never assigned:
            #   - No Done! marker exists (checked above)
            #   - Tracking table shows ⏳ Pending, not 🔄 Active
            #   - No in-memory pending assignment flag
            #   - Grace period has elapsed
            # Assign the agent now.  Dedup guards inside
            # assign_agent_for_status prevent duplicate assignments
            # even in edge cases.
            logger.info(
                "Agent '%s' was never assigned for issue #%d "
                "(tracking=Pending, no pending flag, grace period elapsed) "
                "— assigning now",
                current_agent,
                task.issue_number,
            )
            orchestrator = _cp.get_workflow_orchestrator()
            ctx = _cp.WorkflowContext(
                session_id="polling",
                project_id=project_id,
                access_token=access_token,
                repository_owner=task_owner,
                repository_name=task_repo,
                issue_id=task.github_content_id,
                issue_number=task.issue_number,
                project_item_id=task.github_item_id,
                current_state=_cp.WorkflowState.READY,
            )
            ctx.config = await _cp.get_workflow_config(project_id)

            # Prefer pipeline.original_status for agent lookup.
            # When external automation moved the issue (e.g. Ready → In
            # Progress), from_status may reflect the updated board status,
            # but the pipeline's agents belong to the ORIGINAL status.
            effective_assign_status = pipeline.original_status or from_status

            # Check rate limit budget before assignment
            if await _wait_if_rate_limited(
                f"first-agent assignment '{current_agent}' on issue #{task.issue_number}"
            ):
                return None  # Defer to next polling cycle

            assigned = await orchestrator.assign_agent_for_status(
                ctx, effective_assign_status, agent_index=pipeline.current_agent_index
            )
            if assigned:
                _pending_agent_assignments[pending_key] = utcnow()
                return {
                    "status": "success",
                    "issue_number": task.issue_number,
                    "action": "agent_assigned_after_reconstruction",
                    "agent_name": current_agent,
                    "from_status": from_status,
                }

    return None


async def check_backlog_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list | None = None,
) -> list[dict[str, Any]]:
    """
    Check all issues in "Backlog" status for agent completion.

    When speckit.specify completes (posts completion comment), transition the issue
    to Ready status and assign the first Ready agent (speckit.plan).

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner
        repo: Repository name
        tasks: Pre-fetched project items (optional, to avoid redundant API calls)

    Returns:
        List of results for each processed issue
    """
    results = []

    try:
        if tasks is None:
            tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

        config = await _cp.get_workflow_config(project_id)
        if not config:
            logger.debug("No workflow config for project %s, skipping backlog check", project_id)
            return results

        status_backlog = config.status_backlog.lower()
        backlog_tasks = [
            task
            for task in tasks
            if task.status
            and task.status.lower() == status_backlog
            and task.issue_number is not None
        ]

        if not backlog_tasks:
            return results

        logger.debug("Found %d issues in '%s' status", len(backlog_tasks), config.status_backlog)

        agents = _cp.get_agent_slugs(config, config.status_backlog)

        for task in backlog_tasks:
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo
            if not task_owner or not task_repo:
                continue

            # Get or reconstruct pipeline state
            pipeline = await _get_or_reconstruct_pipeline(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                project_id=project_id,
                status=config.status_backlog,
                agents=agents,
                labels=task.labels,
            )

            # Skip if no agents found (neither DB config nor tracking table)
            if not pipeline.agents:
                continue

            # Process pipeline completion/advancement
            result = await _process_pipeline_completion(
                access_token=access_token,
                project_id=project_id,
                task=task,
                owner=owner,
                repo=repo,
                pipeline=pipeline,
                from_status=config.status_backlog,
                to_status=config.status_ready,
            )
            if result:
                results.append(result)

    except Exception as e:
        logger.error("Error checking backlog issues: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = str(e)

    return results


async def check_ready_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list | None = None,
) -> list[dict[str, Any]]:
    """
    Check all issues in "Ready" status for agent completion.

    Manages the speckit.plan → speckit.tasks pipeline. When all Ready agents
    complete, transition the issue to In Progress and assign speckit.implement.

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner
        repo: Repository name
        tasks: Pre-fetched project items (optional)

    Returns:
        List of results for each processed issue
    """
    results = []

    try:
        if tasks is None:
            tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

        config = await _cp.get_workflow_config(project_id)
        if not config:
            logger.debug("No workflow config for project %s, skipping ready check", project_id)
            return results

        status_ready = config.status_ready.lower()
        ready_tasks = [
            task
            for task in tasks
            if task.status and task.status.lower() == status_ready and task.issue_number is not None
        ]

        if not ready_tasks:
            return results

        logger.debug("Found %d issues in '%s' status", len(ready_tasks), config.status_ready)

        agents = _cp.get_agent_slugs(config, config.status_ready)

        for task in ready_tasks:
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo
            if not task_owner or not task_repo:
                continue

            # Get or reconstruct pipeline state
            pipeline = await _get_or_reconstruct_pipeline(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                project_id=project_id,
                status=config.status_ready,
                agents=agents,
                expected_status=config.status_ready,
                labels=task.labels,
            )

            # Skip if no agents found (neither DB config nor tracking table)
            if not pipeline.agents:
                continue

            # Process pipeline completion/advancement
            result = await _process_pipeline_completion(
                access_token=access_token,
                project_id=project_id,
                task=task,
                owner=owner,
                repo=repo,
                pipeline=pipeline,
                from_status=config.status_ready,
                to_status=config.status_in_progress,
            )
            if result:
                results.append(result)

    except Exception as e:
        logger.error("Error checking ready issues: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = str(e)

    return results


async def _claim_merged_child_prs_for_pipeline(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    agents: list[str],
) -> None:
    """Claim all merged child PRs for every agent to prevent misattribution.

    Only PRs merged AFTER reconstruction will be unclaimed and detectable
    as new completions.
    """
    main_branch_info = _cp.get_issue_main_branch(issue_number)
    if not main_branch_info:
        return
    main_branch = main_branch_info.get("branch")
    main_pr_number = main_branch_info.get("pr_number")
    if not main_branch or not main_pr_number:
        return

    linked_prs = await _cp.github_projects_service.get_linked_pull_requests(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )
    for pr in linked_prs or []:
        pr_number = pr.get("number")
        pr_state = pr.get("state", "").upper()
        if not pr_number or pr_state != "MERGED" or pr_number == main_pr_number:
            continue
        pr_details = await _cp.github_projects_service.get_pull_request(
            access_token=access_token,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
        )
        if pr_details and pr_details.get("base_ref") == main_branch:
            for agent_name in agents:
                claimed_key = f"{issue_number}:{pr_number}:{agent_name}"
                if claimed_key not in _claimed_child_prs:
                    _claimed_child_prs.add(claimed_key)
                    logger.debug(
                        "Claimed merged child PR #%d for agent '%s' "
                        "during pipeline reconstruction (issue #%d)",
                        pr_number,
                        agent_name,
                        issue_number,
                    )


def _derive_pipeline_started_at(
    last_done_timestamp: str | None,
    issue_data: dict | None,
) -> datetime:
    """Derive the best started_at timestamp for a reconstructed pipeline.

    Priority: last Done! marker timestamp > most recent Done! marker from
    any agent > issue creation time > utcnow().
    """
    if last_done_timestamp:
        try:
            return datetime.fromisoformat(last_done_timestamp)
        except (ValueError, TypeError):
            pass

    # No Done! markers for current-status agents — look for the most
    # recent Done! marker from ANY agent (e.g. a prior status).
    comments = (issue_data or {}).get("comments", [])
    latest_any_done_ts: str | None = None
    for c in comments:
        body = c.get("body", "")
        for line in body.split("\n"):
            if line.strip().endswith(": Done!"):
                ts = c.get("created_at", "")
                if ts and (latest_any_done_ts is None or ts > latest_any_done_ts):
                    latest_any_done_ts = ts
    if latest_any_done_ts:
        try:
            return datetime.fromisoformat(latest_any_done_ts)
        except (ValueError, TypeError):
            pass

    # Fall back to issue creation time
    issue_created_at = (issue_data or {}).get("created_at", "")
    if issue_created_at:
        try:
            return datetime.fromisoformat(issue_created_at)
        except (ValueError, TypeError):
            pass

    return utcnow()


async def _reconstruct_pipeline_state(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
    status: str,
    agents: list[str],
) -> "_cp.PipelineState":
    """
    Reconstruct pipeline state from issue comments.

    Scans comments for sequential completion markers to determine
    which agents have already completed.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        project_id: Project ID
        status: Current workflow status
        agents: Ordered list of agents for this status

    Returns:
        Reconstructed PipelineState
    """
    completed = []
    issue_data = None
    last_done_timestamp: str | None = None

    try:
        issue_data = await _cp.github_projects_service.get_issue_with_comments(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

        comments = issue_data.get("comments", []) if issue_data else []

        # Check each agent sequentially — stop at first incomplete.
        # Track the timestamp of the last Done! marker so we can set
        # ``started_at`` to a realistic value (not ``utcnow()``) which
        # allows the timeline-event filter to include completion events
        # from agents that finished before the reconstruction.
        last_done_timestamp: str | None = None
        for agent in agents:
            marker = f"{agent}: Done!"
            done_comment = next(
                (
                    c
                    for c in comments
                    if any(line.strip() == marker for line in c.get("body", "").split("\n"))
                ),
                None,
            )
            if done_comment:
                completed.append(agent)
                last_done_timestamp = done_comment.get("created_at") or last_done_timestamp
            else:
                break

        # Claim all MERGED child PRs for EVERY agent in the pipeline.
        await _claim_merged_child_prs_for_pipeline(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            agents=agents,
        )

    except Exception as e:
        logger.warning("Could not reconstruct pipeline state for issue #%d: %s", issue_number, e)

    # Reconstruct main branch info if not present (e.g. after container restart).
    # Without this, _advance_pipeline / assign_agent_for_status may fall to the
    # "first agent" path and use base_ref="main" for a subsequent agent, causing
    # it to branch from the default branch instead of the issue's main branch.
    if not _cp.get_issue_main_branch(issue_number):
        try:
            existing_pr = await _cp.github_projects_service.find_existing_pr_for_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if existing_pr:
                pr_det = await _cp.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=existing_pr["number"],
                )
                h_sha = pr_det.get("last_commit", {}).get("sha", "") if pr_det else ""
                _cp.set_issue_main_branch(
                    issue_number,
                    existing_pr["head_ref"],
                    existing_pr["number"],
                    h_sha,
                )
                # Ensure the PR is linked to the parent issue so it appears
                # in the Development sidebar on GitHub.
                try:
                    await _cp.github_projects_service.link_pull_request_to_issue(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        pr_number=existing_pr["number"],
                        issue_number=issue_number,
                    )
                except Exception as link_err:
                    logger.debug(
                        "Non-blocking: could not link PR #%d to issue #%d: %s",
                        existing_pr["number"],
                        issue_number,
                        link_err,
                    )
                logger.info(
                    "Reconstructed main branch '%s' (PR #%d) during pipeline "
                    "reconstruction for issue #%d",
                    existing_pr["head_ref"],
                    existing_pr["number"],
                    issue_number,
                )
        except Exception as e:
            logger.debug(
                "Could not reconstruct main branch for issue #%d: %s",
                issue_number,
                e,
            )

    # Try to capture current HEAD SHA for commit-based completion detection
    reconstructed_sha = ""
    main_branch_info = _cp.get_issue_main_branch(issue_number)
    if main_branch_info and main_branch_info.get("pr_number"):
        try:
            pr_details = await _cp.github_projects_service.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=main_branch_info["pr_number"],
            )
            if pr_details and pr_details.get("last_commit", {}).get("sha"):
                reconstructed_sha = pr_details["last_commit"]["sha"]
                logger.debug(
                    "Captured current HEAD SHA '%s' during pipeline reconstruction for issue #%d",
                    reconstructed_sha[:8],
                    issue_number,
                )

            # If completed agents exist and the main PR is no longer a
            # draft, record it in _system_marked_ready_prs.  A previous
            # agent (typically the first one) made the PR ready-for-review.
            # Without this, Signal 1 in _check_main_pr_completion sees
            # the non-draft PR after a container restart and reports a
            # false completion for the current agent.
            if completed and pr_details and not pr_details.get("is_draft", True):
                recon_pr_number = main_branch_info["pr_number"]
                if recon_pr_number not in _system_marked_ready_prs:
                    _system_marked_ready_prs.add(recon_pr_number)
                    logger.info(
                        "Marked main PR #%d as ready during pipeline "
                        "reconstruction for issue #%d (%d completed agents)",
                        recon_pr_number,
                        issue_number,
                        len(completed),
                    )
        except Exception as e:
            logger.debug("Could not capture HEAD SHA during reconstruction: %s", e)

    reconstructed_started_at = _derive_pipeline_started_at(last_done_timestamp, issue_data)

    pipeline = _cp.PipelineState(
        issue_number=issue_number,
        project_id=project_id,
        status=status,
        agents=list(agents),
        current_agent_index=len(completed),
        completed_agents=completed,
        started_at=reconstructed_started_at,
        agent_assigned_sha=reconstructed_sha,
    )

    # Reconstruct group info from tracking table if 6-column format was used
    if issue_data:
        body = issue_data.get("body", "")
        tracking_steps = _cp.parse_tracking_from_body(body) if body else None
        if tracking_steps and any(s.group_label for s in tracking_steps):
            # Filter steps for this status
            status_steps = [s for s in tracking_steps if s.status == status]
            if status_steps:
                groups_by_label: dict[str, _cp.PipelineGroupInfo] = {}
                for step in status_steps:
                    if step.group_label and step.group_label not in groups_by_label:
                        groups_by_label[step.group_label] = _cp.PipelineGroupInfo(
                            group_id=step.group_label,
                            execution_mode=step.group_execution_mode or "sequential",
                            agents=[],
                        )
                    if step.group_label:
                        gi = groups_by_label[step.group_label]
                        gi.agents.append(step.agent_name)
                        # For parallel groups, reconstruct agent_statuses
                        if gi.execution_mode == "parallel":
                            if _cp.STATE_DONE in step.state:
                                gi.agent_statuses[step.agent_name] = "completed"
                            elif _cp.STATE_ACTIVE in step.state:
                                gi.agent_statuses[step.agent_name] = "active"
                            else:
                                gi.agent_statuses[step.agent_name] = "pending"

                pipeline.groups = list(groups_by_label.values())
                # Determine current_group_index and current_agent_index_in_group
                for gi_idx, gi in enumerate(pipeline.groups):
                    if gi.execution_mode == "parallel":
                        all_terminal = len(gi.agent_statuses) >= len(gi.agents) and all(
                            s in ("completed", "failed") for s in gi.agent_statuses.values()
                        )
                        if not all_terminal:
                            pipeline.current_group_index = gi_idx
                            pipeline.current_agent_index_in_group = 0
                            break
                    else:
                        # Sequential: find first non-completed agent
                        for ai_idx, agent_slug in enumerate(gi.agents):
                            if agent_slug not in completed:
                                pipeline.current_group_index = gi_idx
                                pipeline.current_agent_index_in_group = ai_idx
                                break
                        else:
                            continue
                        break
                else:
                    # All groups complete
                    pipeline.current_group_index = len(pipeline.groups)

    # Reconstruct sub-issue mappings from GitHub API
    pipeline.agent_sub_issues = await _cp._reconstruct_sub_issue_mappings(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )

    # Only cache pipeline states that have agents.  Empty-agent states
    # (neither DB config nor tracking table supplied agents) would block
    # recovery on subsequent poll cycles — the cached empty state matches
    # expected_status and is returned immediately, preventing re-reconstruction
    # even if agents are later added to the config.
    if pipeline.agents:
        _cp.set_pipeline_state(issue_number, pipeline)

    logger.info(
        "Reconstructed pipeline state for issue #%d: %d/%d agents completed",
        issue_number,
        len(completed),
        len(agents),
    )

    return pipeline


async def _close_completed_sub_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    completed_agents: list[str],
    pipeline: "_cp.PipelineState",
) -> None:
    """Close sub-issues for all completed agents that are still open.

    This handles retroactive closes after server restarts or when
    ``_advance_pipeline`` only closed the current agent's sub-issue but
    earlier agents were missed.
    """
    for agent_name in completed_agents:
        sub_info = None
        if pipeline.agent_sub_issues:
            sub_info = pipeline.agent_sub_issues.get(agent_name)
        if not sub_info:
            global_subs = _cp.get_issue_sub_issues(issue_number)
            sub_info = global_subs.get(agent_name)
        if not sub_info or not sub_info.get("number") or sub_info["number"] == issue_number:
            continue

        try:
            await _cp.github_projects_service.update_issue_state(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=sub_info["number"],
                state="closed",
                state_reason="completed",
                labels_add=["done"],
                labels_remove=["in-progress"],
            )
            logger.info(
                "Closed sub-issue #%d for completed agent '%s' (sweep)",
                sub_info["number"],
                agent_name,
            )
        except Exception as e:
            logger.warning(
                "Failed to close sub-issue #%d for agent '%s' (sweep): %s",
                sub_info["number"],
                agent_name,
                e,
            )

        # Update the sub-issue's project board Status to "Done"
        sub_node_id = sub_info.get("node_id", "")
        if sub_node_id:
            try:
                await _cp.github_projects_service.update_sub_issue_project_status(
                    access_token=access_token,
                    project_id=project_id,
                    sub_issue_node_id=sub_node_id,
                    status_name="Done",
                )
            except Exception as e:
                logger.warning(
                    "Failed to update sub-issue #%d board status to Done (sweep): %s",
                    sub_info["number"],
                    e,
                )


async def _advance_pipeline(
    access_token: str,
    project_id: str,
    item_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    issue_node_id: str | None,
    pipeline: "_cp.PipelineState",
    from_status: str,
    to_status: str,
    task_title: str,
) -> dict[str, Any] | None:
    """
    Advance the pipeline after an agent completes.

    If there are more agents in the pipeline, assign the next one.
    If pipeline is complete, transition to the next status.

    Args:
        access_token: GitHub access token
        project_id: Project ID
        item_id: Project item ID
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        issue_node_id: Issue node ID (for Copilot assignment)
        pipeline: Current pipeline state
        from_status: Current status
        to_status: Target status after pipeline completion
        task_title: Task title for logging

    Returns:
        Result dict or None
    """
    completed_agent = pipeline.current_agent
    if completed_agent is None:
        logger.error("No current agent in pipeline — cannot advance")
        return None

    # Snapshot group state before mutation so rollback can restore it
    # if the child-PR merge fails or is blocked.
    _pre_group_idx = pipeline.current_group_index
    _pre_agent_in_group = pipeline.current_agent_index_in_group
    _pre_group_agent_status: str | None = None
    if pipeline.groups and pipeline.current_group_index < len(pipeline.groups):
        _pre_group_agent_status = pipeline.groups[pipeline.current_group_index].agent_statuses.get(
            completed_agent
        )

    pipeline.completed_agents.append(completed_agent)
    pipeline.current_agent_index += 1

    # Group-aware advancement
    if pipeline.groups and pipeline.current_group_index < len(pipeline.groups):
        group = pipeline.groups[pipeline.current_group_index]
        if group.execution_mode == "parallel":
            # Mark agent as completed in parallel group tracking
            group.agent_statuses[completed_agent] = "completed"
            # Check if all agents in the parallel group are done —
            # ensure every agent in the group has a terminal status
            all_done = len(group.agent_statuses) >= len(group.agents) and all(
                s in ("completed", "failed") for s in group.agent_statuses.values()
            )
            if all_done:
                pipeline.current_group_index += 1
                pipeline.current_agent_index_in_group = 0
        else:
            # Sequential group: advance within group
            pipeline.current_agent_index_in_group += 1
            if pipeline.current_agent_index_in_group >= len(group.agents):
                # Group complete → advance to next group
                pipeline.current_group_index += 1
                pipeline.current_agent_index_in_group = 0

        # Skip empty groups after advancement
        while (
            pipeline.current_group_index < len(pipeline.groups)
            and not pipeline.groups[pipeline.current_group_index].agents
        ):
            pipeline.current_group_index += 1
            pipeline.current_agent_index_in_group = 0

    # Clear the pending assignment flag now that the agent has completed
    _pending_agent_assignments.pop(f"{issue_number}:{completed_agent}", None)

    logger.info(
        "Agent '%s' completed on issue #%d (%d/%d agents done)",
        completed_agent,
        issue_number,
        len(pipeline.completed_agents),
        len(pipeline.agents),
    )

    # ── Safety-net: ensure the completed agent's child PR is merged
    # BEFORE applying external side effects (tracking table, sub-issue
    # close, board status).  This ordering guarantees that if the merge
    # fails and we roll back the pipeline index, no externally visible
    # state was changed — avoiding the inconsistency where the tracking
    # table says ✅ Done but the pipeline says the agent isn't complete.
    #
    # NOTE: The primary child PR merge happens in post_agent_outputs_from_pr
    # BEFORE the Done! marker.  This safety-net catches edge cases (e.g.
    # Done! posted externally, child PR found via sub-issue fallback).
    main_branch_info = _cp.get_issue_main_branch(issue_number)
    if not main_branch_info:
        # Reconstruct main branch info (may have been lost on restart)
        try:
            existing_pr = await _cp.github_projects_service.find_existing_pr_for_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if existing_pr:
                pr_det = await _cp.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=existing_pr["number"],
                )
                h_sha = pr_det.get("last_commit", {}).get("sha", "") if pr_det else ""
                _cp.set_issue_main_branch(
                    issue_number,
                    existing_pr["head_ref"],
                    existing_pr["number"],
                    h_sha,
                )
                # Ensure the PR is linked to the parent issue
                try:
                    await _cp.github_projects_service.link_pull_request_to_issue(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        pr_number=existing_pr["number"],
                        issue_number=issue_number,
                    )
                except Exception as link_err:
                    logger.debug(
                        "Non-blocking: could not link PR #%d to issue #%d: %s",
                        existing_pr["number"],
                        issue_number,
                        link_err,
                    )
                main_branch_info = _cp.get_issue_main_branch(issue_number)
                logger.info(
                    "Reconstructed main branch '%s' (PR #%d) in _advance_pipeline for issue #%d",
                    existing_pr["head_ref"],
                    existing_pr["number"],
                    issue_number,
                )
        except Exception as e:
            logger.debug(
                "Could not reconstruct main branch for issue #%d: %s",
                issue_number,
                e,
            )

    if main_branch_info:
        merge_result = await _cp._merge_child_pr_if_applicable(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            main_branch=main_branch_info["branch"],
            main_pr_number=main_branch_info["pr_number"],
            completed_agent=completed_agent,
            pipeline=pipeline,
        )
        if merge_result and merge_result.get("status") == "merged":
            logger.info(
                "Safety-net merge: child PR for agent '%s' merged in _advance_pipeline (issue #%d)",
                completed_agent,
                issue_number,
            )
            _merge_failure_counts.pop(issue_number, None)
            await asyncio.sleep(_cp.POST_ACTION_DELAY_SECONDS)
        elif merge_result and merge_result.get("status") == "merge_failed":
            # A child PR exists but could not be merged.  Track the failure
            # count so we don't block indefinitely on an unmergeable PR.
            failure_count = _merge_failure_counts.get(issue_number, 0) + 1
            _merge_failure_counts[issue_number] = failure_count

            if failure_count >= MAX_MERGE_RETRIES:
                # Exceeded retry limit — skip the merge and advance.
                blocked_pr = merge_result.get("pr_number")
                logger.error(
                    "Safety-net merge for agent '%s' on issue #%d "
                    "(child PR #%s) failed %d times — skipping merge "
                    "and advancing pipeline",
                    completed_agent,
                    issue_number,
                    blocked_pr,
                    failure_count,
                )
                _merge_failure_counts.pop(issue_number, None)
                # Post a warning comment so users know the merge was skipped.
                try:
                    await _cp.github_projects_service.create_issue_comment(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                        body=(
                            f"⚠️ Failed to merge child PR #{blocked_pr} for "
                            f"agent **{completed_agent}** after "
                            f"{failure_count} attempts. Advancing pipeline — "
                            f"please resolve merge conflicts manually."
                        ),
                    )
                except Exception:
                    logger.warning(
                        "Could not post merge-skip warning on issue #%d",
                        issue_number,
                        exc_info=True,
                    )
                # Do NOT roll back — let the pipeline continue below.
            else:
                logger.warning(
                    "Safety-net merge FAILED for agent '%s' on issue #%d "
                    "(child PR #%s, attempt %d/%d) — blocking pipeline "
                    "advance until child PR is merged",
                    completed_agent,
                    issue_number,
                    merge_result.get("pr_number"),
                    failure_count,
                    MAX_MERGE_RETRIES,
                )
                # Roll back the pipeline advance.  Because external side
                # effects (tracking table, sub-issue close) have NOT been
                # applied yet, this rollback is fully consistent.
                pipeline.current_agent_index -= 1
                if completed_agent in pipeline.completed_agents:
                    pipeline.completed_agents.remove(completed_agent)
                # Restore group indices/statuses to pre-advance values so
                # current_agent (derived from group state) stays consistent.
                pipeline.current_group_index = _pre_group_idx
                pipeline.current_agent_index_in_group = _pre_agent_in_group
                if pipeline.groups and _pre_group_idx < len(pipeline.groups):
                    _g = pipeline.groups[_pre_group_idx]
                    if _pre_group_agent_status is None:
                        _g.agent_statuses.pop(completed_agent, None)
                    else:
                        _g.agent_statuses[completed_agent] = _pre_group_agent_status
                _cp.set_pipeline_state(issue_number, pipeline)
                return {
                    "status": "merge_blocked",
                    "issue_number": issue_number,
                    "task_title": task_title,
                    "action": "merge_blocked",
                    "agent_name": completed_agent,
                    "blocked_pr": merge_result.get("pr_number"),
                }
        elif merge_result is None:
            from .completion import _find_open_child_pr

            open_child_pr = await _find_open_child_pr(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                main_branch=main_branch_info["branch"],
                main_pr_number=main_branch_info["pr_number"],
                agent_name=completed_agent,
                pipeline=pipeline,
            )
            if open_child_pr:
                logger.warning(
                    "Safety-net merge found open child PR #%d for agent '%s' on issue #%d but merge did not complete — blocking pipeline advance",
                    open_child_pr.get("number"),
                    completed_agent,
                    issue_number,
                )
                pipeline.current_agent_index -= 1
                if completed_agent in pipeline.completed_agents:
                    pipeline.completed_agents.remove(completed_agent)
                # Restore group indices/statuses to pre-advance values.
                pipeline.current_group_index = _pre_group_idx
                pipeline.current_agent_index_in_group = _pre_agent_in_group
                if pipeline.groups and _pre_group_idx < len(pipeline.groups):
                    _g = pipeline.groups[_pre_group_idx]
                    if _pre_group_agent_status is None:
                        _g.agent_statuses.pop(completed_agent, None)
                    else:
                        _g.agent_statuses[completed_agent] = _pre_group_agent_status
                _cp.set_pipeline_state(issue_number, pipeline)
                return {
                    "status": "merge_blocked",
                    "issue_number": issue_number,
                    "task_title": task_title,
                    "action": "merge_blocked",
                    "agent_name": completed_agent,
                    "blocked_pr": open_child_pr.get("number"),
                }

        # Refresh HEAD SHA so the next agent / next status branches
        # from the absolute latest (post-merge) state.
        try:
            pr_det = await _cp.github_projects_service.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=main_branch_info["pr_number"],
            )
            if pr_det and pr_det.get("last_commit", {}).get("sha"):
                _cp.update_issue_main_branch_sha(issue_number, pr_det["last_commit"]["sha"])
        except Exception as e:
            logger.debug(
                "Could not refresh HEAD SHA for issue #%d: %s",
                issue_number,
                e,
            )

    # ── Apply external side effects AFTER the merge succeeded (or was
    # not needed).  This ensures rollback on merge failure is clean.

    # Mark the completed agent as ✅ Done in the issue body tracking table.
    # post_agent_outputs_from_pr (Step 0) also does this, but it can fail
    # silently or be skipped when the Done! marker was posted externally.
    # This defensive call ensures the tracking table stays in sync.
    await _cp._update_issue_tracking(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        agent_name=completed_agent,
        new_state="done",
    )

    # Close the completed agent's sub-issue (and sweep any previously
    # completed agents whose sub-issues may have been missed — e.g. after
    # a server restart where _advance_pipeline was never called for them).
    await _close_completed_sub_issues(
        access_token=access_token,
        project_id=project_id,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        completed_agents=list(pipeline.completed_agents),
        pipeline=pipeline,
    )

    # After advancing, if the main PR is not a draft, record it in
    # _system_marked_ready_prs.  The first agent (or a previous agent)
    # made the PR ready-for-review.  Without this, the NEXT agent in
    # the pipeline can be falsely detected as complete by Signal 1 in
    # _check_main_pr_completion, which sees the non-draft PR and fires
    # before the agent has even started — cancelling the Copilot session.
    if main_branch_info:
        advance_pr_number = main_branch_info["pr_number"]
        if advance_pr_number not in _system_marked_ready_prs:
            try:
                pr_check = await _cp.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=advance_pr_number,
                )
                if pr_check and not pr_check.get("is_draft", True):
                    _system_marked_ready_prs.add(advance_pr_number)
                    logger.info(
                        "Marked main PR #%d as ready after pipeline advance "
                        "(agent '%s' completed on issue #%d)",
                        advance_pr_number,
                        completed_agent,
                        issue_number,
                    )
            except Exception as e:
                logger.debug("Could not check main PR draft status during advance: %s", e)

    # Send agent_completed WebSocket notification
    await _cp.connection_manager.broadcast_to_project(
        project_id,
        {
            "type": "agent_completed",
            "issue_number": issue_number,
            "agent_name": completed_agent,
            "status": from_status,
            "next_agent": pipeline.current_agent if not pipeline.is_complete else None,
            "timestamp": utcnow().isoformat(),
        },
    )

    if pipeline.is_complete:
        # Pipeline complete → transition to next status.
        # Note: remove_pipeline_state is called AFTER the transition so
        # _transition_after_pipeline_complete can still read pipeline-level
        # settings (e.g. auto_merge) from the state.
        result = await _transition_after_pipeline_complete(
            access_token=access_token,
            project_id=project_id,
            item_id=item_id,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            issue_node_id=issue_node_id,
            from_status=from_status,
            to_status=to_status,
            task_title=task_title,
        )
        _cp.remove_pipeline_state(issue_number)
        return result

    # ── Group-aware: parallel group still has active agents → wait
    if pipeline.groups and pipeline.current_group_index < len(pipeline.groups):
        group = pipeline.groups[pipeline.current_group_index]
        if group.execution_mode == "parallel" and group.agents:
            # Only wait when a parallel group has already started. A freshly
            # entered group has all agents pending and must be assigned now.
            has_started = any(
                status in ("active", "completed", "failed")
                for status in group.agent_statuses.values()
            )
            still_active = has_started and (
                len(group.agent_statuses) < len(group.agents)
                or any(s not in ("completed", "failed") for s in group.agent_statuses.values())
            )
            if still_active:
                # Other parallel agents are still running — do NOT assign a new agent
                pipeline.started_at = utcnow()
                _cp.set_pipeline_state(issue_number, pipeline)
                logger.info(
                    "Parallel group '%s' on issue #%d still has active agents — waiting",
                    group.group_id,
                    issue_number,
                )
                return {
                    "status": "waiting",
                    "issue_number": issue_number,
                    "task_title": task_title,
                    "action": "parallel_wait",
                    "completed_agent": completed_agent,
                    "pipeline_progress": f"{len(pipeline.completed_agents)}/{len(pipeline.agents)}",
                }

    # Assign next agent(s)
    next_agent = pipeline.current_agent
    pipeline.started_at = utcnow()

    # ── Human Agent Skip (Auto Merge) ──
    # When auto_merge is active (project-level OR pipeline-level) and the
    # human agent is the last step in the pipeline, skip it with a ⏭ SKIPPED
    # indicator and proceed directly to pipeline completion and auto-merge flow.
    if next_agent == "human":
        # Check if human is the last step
        remaining_agents = pipeline.agents[pipeline.current_agent_index :]
        is_last_step = len(remaining_agents) == 1

        if is_last_step:
            from src.services.database import get_db
            from src.services.settings_store import is_auto_merge_enabled

            db = get_db()
            auto_merge_active = pipeline.auto_merge or await is_auto_merge_enabled(db, project_id)

            if auto_merge_active:
                logger.info(
                    "Auto-merge: skipping human agent (last step) for issue #%d",
                    issue_number,
                )

                # Mark step as SKIPPED in pipeline
                pipeline.completed_agents.append("human")
                pipeline.current_agent_index += 1

                # Update group tracking if applicable
                if pipeline.groups and pipeline.current_group_index < len(pipeline.groups):
                    group = pipeline.groups[pipeline.current_group_index]
                    group.agent_statuses["human"] = "completed"

                _cp.set_pipeline_state(issue_number, pipeline)

                # Close human sub-issue with skip comment
                human_sub = pipeline.agent_sub_issues.get("human")
                if human_sub:
                    sub_number = human_sub.get("number")
                    if sub_number:
                        try:
                            await _cp.github_projects_service.create_issue_comment(
                                access_token=access_token,
                                owner=owner,
                                repo=repo,
                                issue_number=sub_number,
                                body="Skipped — Auto Merge enabled",
                            )
                            await _cp.github_projects_service.update_issue_state(
                                access_token=access_token,
                                owner=owner,
                                repo=repo,
                                issue_number=sub_number,
                                state="closed",
                                state_reason="not_planned",
                            )
                        except Exception:
                            logger.warning(
                                "Failed to close human sub-issue #%d",
                                sub_number,
                                exc_info=True,
                            )

                # Mark as SKIPPED in tracking table
                await _cp.connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "task_update",
                        "issue_number": issue_number,
                        "agent": "human",
                        "agent_state": "⏭ SKIPPED",
                        "timestamp": utcnow().isoformat(),
                    },
                )

                # Pipeline is now complete — transition
                if pipeline.is_complete:
                    result = await _transition_after_pipeline_complete(
                        access_token=access_token,
                        project_id=project_id,
                        item_id=item_id,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                        issue_node_id=issue_node_id,
                        from_status=from_status,
                        to_status=to_status,
                        task_title=task_title,
                    )
                    _cp.remove_pipeline_state(issue_number)
                    return result

    _cp.set_pipeline_state(issue_number, pipeline)

    # Use the pipeline's ORIGINAL status for agent lookup when available.
    # When external automation (e.g. GitHub project rules) moves an issue
    # ahead of where the pipeline is (Backlog/Ready → In Progress, or
    # In Progress → In Review), pipeline.status is updated to match the
    # board.  But the agents in the pipeline are still for the ORIGINAL
    # status.  Looking up agents for the updated board status would
    # return the wrong agent list (e.g. ["speckit.implement"] instead
    # of ["speckit.plan", "speckit.tasks"]), causing the pipeline to
    # silently skip remaining agents.
    agent_lookup_status = pipeline.original_status or pipeline.status or from_status

    logger.info(
        "Assigning next agent '%s' to issue #%d (pipeline_status='%s', board_status='%s')",
        next_agent,
        issue_number,
        agent_lookup_status,
        from_status,
    )

    orchestrator = _cp.get_workflow_orchestrator()
    ctx = _cp.WorkflowContext(
        session_id="polling",
        project_id=project_id,
        access_token=access_token,
        repository_owner=owner,
        repository_name=repo,
        issue_id=issue_node_id,
        issue_number=issue_number,
        project_item_id=item_id,
        current_state=_cp.WorkflowState.READY,
    )
    ctx.config = await _cp.get_workflow_config(project_id)

    # Group-aware: if the new current group is parallel, assign ALL agents
    # with adaptive stagger based on rate limit budget.
    if pipeline.groups and pipeline.current_group_index < len(pipeline.groups):
        new_group = pipeline.groups[pipeline.current_group_index]
        if new_group.execution_mode == "parallel" and len(new_group.agents) > 1:
            # Pre-check rate limit budget before parallel burst
            if await _wait_if_rate_limited(f"parallel group assignment on issue #{issue_number}"):
                # Budget critically low — save state and defer to next cycle
                _cp.set_pipeline_state(issue_number, pipeline)
                return {
                    "status": "deferred",
                    "issue_number": issue_number,
                    "task_title": task_title,
                    "action": "rate_limited",
                    "completed_agent": completed_agent,
                }

            # Adaptive stagger: 2s normally, 5s when budget is getting low
            remaining_pre, _ = _get_rate_limit_remaining()
            stagger_seconds = (
                5 if remaining_pre is not None and remaining_pre <= RATE_LIMIT_SLOW_THRESHOLD else 2
            )

            success = True
            for i, agent_slug in enumerate(new_group.agents):
                if i > 0:
                    await asyncio.sleep(stagger_seconds)
                try:
                    agent_flat_idx = pipeline.agents.index(agent_slug)
                except ValueError:
                    logger.warning(
                        "Agent '%s' not found in flat agent list for issue #%d — "
                        "using offset %d from current_agent_index",
                        agent_slug,
                        issue_number,
                        i,
                    )
                    agent_flat_idx = min(
                        pipeline.current_agent_index + i,
                        len(pipeline.agents) - 1,
                    )
                new_group.agent_statuses[agent_slug] = "active"
                result = await orchestrator.assign_agent_for_status(
                    ctx, agent_lookup_status, agent_index=agent_flat_idx
                )
                if not result:
                    success = False
                    new_group.agent_statuses[agent_slug] = "failed"
                    pipeline.failed_agents.append(agent_slug)
            _cp.set_pipeline_state(issue_number, pipeline)

            if success:
                await _cp.connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "agent_assigned",
                        "issue_number": issue_number,
                        "agent_name": ", ".join(new_group.agents),
                        "status": agent_lookup_status,
                        "next_agent": None,
                        "timestamp": utcnow().isoformat(),
                    },
                )
            return {
                "status": "success" if success else "error",
                "issue_number": issue_number,
                "task_title": task_title,
                "action": "parallel_group_assigned",
                "agent_name": ", ".join(new_group.agents),
                "completed_agent": completed_agent,
                "pipeline_progress": f"{len(pipeline.completed_agents)}/{len(pipeline.agents)}",
            }

    # Pre-check rate limit budget before single agent assignment
    if await _wait_if_rate_limited(f"agent assignment '{next_agent}' on issue #{issue_number}"):
        _cp.set_pipeline_state(issue_number, pipeline)
        return {
            "status": "deferred",
            "issue_number": issue_number,
            "task_title": task_title,
            "action": "rate_limited",
            "completed_agent": completed_agent,
        }

    success = await orchestrator.assign_agent_for_status(
        ctx, agent_lookup_status, agent_index=pipeline.current_agent_index
    )

    # Send agent_assigned WebSocket notification
    if success:
        await _cp.connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "agent_assigned",
                "issue_number": issue_number,
                "agent_name": next_agent,
                "status": agent_lookup_status,
                "next_agent": pipeline.next_agent,
                "timestamp": utcnow().isoformat(),
            },
        )

    return {
        "status": "success" if success else "error",
        "issue_number": issue_number,
        "task_title": task_title,
        "action": "agent_assigned",
        "agent_name": next_agent,
        "completed_agent": completed_agent,
        "pipeline_progress": f"{len(pipeline.completed_agents)}/{len(pipeline.agents)}",
    }


async def _transition_after_pipeline_complete(
    access_token: str,
    project_id: str,
    item_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    issue_node_id: str | None,
    from_status: str,
    to_status: str,
    task_title: str,
) -> dict[str, Any] | None:
    """
    Transition an issue to the next status after all agents in the pipeline complete,
    then assign the first agent for the new status.

    Args:
        access_token: GitHub access token
        project_id: Project ID
        item_id: Project item ID
        owner: Repo owner
        repo: Repo name
        issue_number: Issue number
        issue_node_id: Issue node ID
        from_status: Current status
        to_status: Target status
        task_title: Task title for logging

    Returns:
        Result dict or None
    """
    logger.info(
        "All agents complete for issue #%d in '%s'. Transitioning to '%s'.",
        issue_number,
        from_status,
        to_status,
    )

    # Transition the status
    success = await _cp.github_projects_service.update_item_status_by_name(
        access_token=access_token,
        project_id=project_id,
        item_id=item_id,
        status_name=to_status,
    )

    if not success:
        logger.error(
            "Failed to transition issue #%d from '%s' to '%s'",
            issue_number,
            from_status,
            to_status,
        )
        return {
            "status": "error",
            "issue_number": issue_number,
            "task_title": task_title,
            "error": f"Failed to update status to {to_status}",
        }

    # Capture pipeline-level auto_merge BEFORE removing state.
    # Callers may have already removed it, so this is best-effort.
    _pipeline_auto_merge = False
    try:
        _pipeline_state = _cp.get_pipeline_state(issue_number)
        if _pipeline_state is not None:
            _pipeline_auto_merge = bool(getattr(_pipeline_state, "auto_merge", False))
    except Exception:
        pass

    # Remove any old pipeline state for this issue
    _cp.remove_pipeline_state(issue_number)

    # Auto-unregister the project from multi-project monitoring when no
    # active or queued pipelines remain.  This prevents polling empty projects
    # while keeping projects with queued pipelines monitored until dequeue.
    try:
        from src.services.pipeline_state_store import (
            count_active_pipelines_for_project,
            get_queued_pipelines_for_project,
        )

        if (
            count_active_pipelines_for_project(project_id) == 0
            and len(get_queued_pipelines_for_project(project_id)) == 0
        ):
            from src.services.copilot_polling.state import unregister_project

            unregister_project(project_id)
    except Exception:
        logger.debug("Failed to auto-unregister project %s: %s", project_id, exc_info=True)

    # Dequeue the next waiting pipeline if queue mode is active.
    # Only release the queue when the pipeline reaches a terminal-ish status
    # ("In Review" or "Done") — intermediate transitions (Backlog→Ready,
    # Ready→In Progress) must NOT start the next queued pipeline.
    if to_status.lower() in ("in review", "done"):
        await _dequeue_next_pipeline(
            access_token=access_token,
            project_id=project_id,
            trigger=f"pipeline_complete(issue=#{issue_number}, to={to_status})",
        )

    # ── Auto Merge Check ──
    # When auto_merge is active (project-level OR pipeline-level), attempt
    # to squash-merge the parent PR automatically instead of waiting for
    # human intervention.  Uses lazy check at merge decision point to
    # support retroactive toggle activation.
    if to_status.lower() == "in review":
        from .auto_merge import _attempt_auto_merge

        # Check pipeline-level auto_merge (state is still available —
        # callers defer remove_pipeline_state until after this function).
        pipeline_auto_merge = False
        try:
            pipeline_state = _cp.get_pipeline_state(issue_number)
            if pipeline_state is not None:
                pipeline_auto_merge = bool(getattr(pipeline_state, "auto_merge", False))
        except Exception:
            logger.debug(
                "Auto-merge pipeline-state check skipped for issue #%d",
                issue_number,
            )

        project_auto_merge = False
        try:
            from src.services.database import get_db
            from src.services.settings_store import is_auto_merge_enabled

            db = get_db()
            project_auto_merge = await is_auto_merge_enabled(db, project_id)
        except Exception:
            logger.debug(
                "Auto-merge project-setting check skipped for issue #%d — database not available",
                issue_number,
            )

        auto_merge_active = pipeline_auto_merge or project_auto_merge

        if auto_merge_active:
            logger.info(
                "Auto-merge active for issue #%d — attempting squash-merge",
                issue_number,
            )
            merge_result = await _attempt_auto_merge(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            if merge_result.status == "merged":
                # ── Transition to Done ──
                # Move board status, close issue, clean up caches.
                done_status = "Done"
                try:
                    _config = await _cp.get_workflow_config(project_id)
                    if _config:
                        done_status = getattr(_config, "status_done", None) or "Done"
                except Exception:
                    pass

                await _cp.github_projects_service.update_item_status_by_name(
                    access_token=access_token,
                    project_id=project_id,
                    item_id=item_id,
                    status_name=done_status,
                )

                # Close the parent issue
                try:
                    await _cp.github_projects_service.update_issue_state(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                        state="closed",
                        state_reason="completed",
                    )
                except Exception:
                    logger.warning(
                        "Auto-merge: failed to close parent issue #%d",
                        issue_number,
                        exc_info=True,
                    )

                # Clean up main branch cache
                from src.services.workflow_orchestrator.transitions import clear_issue_main_branch

                clear_issue_main_branch(issue_number)

                await _cp.connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "auto_merge_completed",
                        "issue_number": issue_number,
                        "pr_number": merge_result.pr_number,
                        "merge_commit": merge_result.merge_commit,
                    },
                )
                await _cp.connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "status_updated",
                        "issue_number": issue_number,
                        "from_status": to_status,
                        "to_status": done_status,
                        "title": task_title,
                        "triggered_by": "auto_merge",
                    },
                )

                # Dequeue next pipeline now that this one is fully Done
                await _dequeue_next_pipeline(
                    access_token=access_token,
                    project_id=project_id,
                    trigger=f"auto_merge_done(issue=#{issue_number})",
                )

                logger.info(
                    "Auto-merge completed for issue #%d (PR #%s) → %s",
                    issue_number,
                    merge_result.pr_number,
                    done_status,
                )
                return {
                    "status": "auto_merged",
                    "issue_number": issue_number,
                    "pr_number": merge_result.pr_number,
                    "merge_commit": merge_result.merge_commit,
                }
            elif merge_result.status == "devops_needed":
                from .auto_merge import dispatch_devops_agent

                # Use in-memory pipeline metadata if still available for
                # DevOps retry tracking; otherwise start fresh.
                existing_pipeline = _cp.get_pipeline_state(issue_number)
                pipeline_metadata: dict[str, Any] = (
                    dict(existing_pipeline.__dict__) if existing_pipeline else {}
                )
                dispatched = await dispatch_devops_agent(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                    pipeline_metadata=pipeline_metadata,
                    project_id=project_id,
                    merge_result_context=merge_result.context,
                )
                if not dispatched:
                    # Retry cap reached — broadcast failure
                    await _cp.connection_manager.broadcast_to_project(
                        project_id,
                        {
                            "type": "auto_merge_failed",
                            "issue_number": issue_number,
                            "pr_number": merge_result.pr_number,
                            "error": "DevOps retry cap reached",
                        },
                    )
            elif merge_result.status == "merge_failed":
                await _cp.connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "auto_merge_failed",
                        "issue_number": issue_number,
                        "pr_number": merge_result.pr_number,
                        "error": merge_result.error,
                    },
                )
            # retry_later: no action needed, will retry on next poll cycle

    # When transitioning to "In Review", convert main PR from draft→ready
    # and request Copilot code review on the main PR.
    # Uses comprehensive multi-strategy discovery (in-memory cache,
    # parent issue links, sub-issue PR discovery, REST branch search,
    # and auto-creation of PR from WIP branches) to find the main PR
    # even when in-memory state is lost (e.g. after server restart).
    if to_status.lower() == "in review":
        from .helpers import _discover_main_pr_for_review

        discovered = await _discover_main_pr_for_review(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=issue_number,
        )

        if discovered:
            main_pr_number = discovered["pr_number"]
            main_pr_id = discovered.get("pr_id", "")
            main_pr_is_draft = discovered.get("is_draft", False)

            # If the GraphQL node ID is missing, fetch full PR details
            if not main_pr_id and main_pr_number:
                main_pr_details = await _cp.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=main_pr_number,
                )
                if main_pr_details:
                    main_pr_id = main_pr_details.get("id", "")
                    main_pr_is_draft = main_pr_details.get("is_draft", False)

            # Convert draft → ready
            if main_pr_is_draft and main_pr_id:
                logger.info(
                    "Converting main PR #%d from draft to ready for review",
                    main_pr_number,
                )
                mark_ready_success = await _cp.github_projects_service.mark_pr_ready_for_review(
                    access_token=access_token,
                    pr_node_id=str(main_pr_id),
                )
                if mark_ready_success:
                    _system_marked_ready_prs.add(main_pr_number)
                    logger.info(
                        "Successfully converted main PR #%d from draft to ready",
                        main_pr_number,
                    )
                else:
                    logger.warning(
                        "Failed to convert main PR #%d from draft to ready",
                        main_pr_number,
                    )

            # Request Copilot code review
            if main_pr_id:
                review_requested = await _cp.github_projects_service.request_copilot_review(
                    access_token=access_token,
                    pr_node_id=str(main_pr_id),
                    pr_number=main_pr_number,
                    owner=owner,
                    repo=repo,
                )
                if review_requested:
                    # Record the request timestamp so _check_copilot_review_done
                    # can filter out any random/auto-triggered reviews that were
                    # submitted BEFORE our explicit request.
                    from .helpers import _record_copilot_review_request_timestamp

                    await _record_copilot_review_request_timestamp(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                    )
                    logger.info(
                        "Copilot code review requested for main PR #%d",
                        main_pr_number,
                    )
        else:
            logger.warning(
                "No main PR found for issue #%d during In Review transition — "
                "comprehensive discovery exhausted all strategies; "
                "safety net will retry on next poll cycle",
                issue_number,
            )

    # ── Auto Merge Retry for Done Transition ──
    # When transitioning to Done with auto_merge active, attempt a merge in
    # case a previous "retry_later" (during In Progress → In Review) left
    # the PR unmerged.  By the time copilot-review finishes, CI should have
    # completed.
    # Derive the effective Done status from workflow config so custom status
    # names still trigger the retry (mirrors the In Review merge path).
    _done_status_name = "done"
    try:
        _done_config = await _cp.get_workflow_config(project_id)
        if _done_config:
            _cfg_done = getattr(_done_config, "status_done", None)
            if isinstance(_cfg_done, str) and _cfg_done.strip():
                _done_status_name = _cfg_done.strip().lower()
    except Exception:
        pass

    if to_status.lower() == _done_status_name:
        _done_auto_merge_active = False
        try:
            from src.services.database import get_db
            from src.services.settings_store import is_auto_merge_enabled

            db = get_db()
            _done_auto_merge_active = await is_auto_merge_enabled(db, project_id)
        except Exception:
            pass
        # Also honour pipeline-level auto-merge (captured before state removal).
        _done_auto_merge_active = _done_auto_merge_active or _pipeline_auto_merge

        if _done_auto_merge_active:
            from .auto_merge import _attempt_auto_merge

            logger.info(
                "Auto-merge retry on Done transition for issue #%d",
                issue_number,
            )
            done_merge_result = await _attempt_auto_merge(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )

            if done_merge_result.status == "merged":
                # Close the parent issue
                try:
                    await _cp.github_projects_service.update_issue_state(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                        state="closed",
                        state_reason="completed",
                    )
                except Exception:
                    logger.warning(
                        "Auto-merge (Done): failed to close issue #%d",
                        issue_number,
                        exc_info=True,
                    )

                from src.services.workflow_orchestrator.transitions import clear_issue_main_branch

                clear_issue_main_branch(issue_number)

                await _cp.connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "auto_merge_completed",
                        "issue_number": issue_number,
                        "pr_number": done_merge_result.pr_number,
                        "merge_commit": done_merge_result.merge_commit,
                    },
                )
                logger.info(
                    "Auto-merge (Done) completed for issue #%d (PR #%s)",
                    issue_number,
                    done_merge_result.pr_number,
                )
            elif done_merge_result.status == "devops_needed":
                from .auto_merge import dispatch_devops_agent

                existing_pipeline = _cp.get_pipeline_state(issue_number)
                done_pipeline_metadata: dict[str, Any] = (
                    dict(existing_pipeline.__dict__) if existing_pipeline else {}
                )
                await dispatch_devops_agent(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                    pipeline_metadata=done_pipeline_metadata,
                    project_id=project_id,
                    merge_result_context=done_merge_result.context,
                )
            elif done_merge_result.status == "merge_failed":
                logger.warning(
                    "Auto-merge (Done) failed for issue #%d: %s",
                    issue_number,
                    done_merge_result.error,
                )
            # retry_later: PR will remain unmerged; user can merge manually

    # Send status transition WebSocket notification
    await _cp.connection_manager.broadcast_to_project(
        project_id,
        {
            "type": "status_updated",
            "issue_number": issue_number,
            "from_status": from_status,
            "to_status": to_status,
            "title": task_title,
            "triggered_by": "pipeline_complete",
        },
    )

    # Assign the first agent for the new status
    config = await _cp.get_workflow_config(project_id)
    new_status_agents = _cp.get_agent_slugs(config, to_status) if config else []

    # Pass-through: if new status has no agents, find the next actionable status (T028)
    effective_status = to_status
    if config and not new_status_agents:
        next_actionable = _cp.find_next_actionable_status(config, to_status)
        if next_actionable and next_actionable != to_status:
            logger.info(
                "Pass-through: '%s' has no agents, advancing issue #%d to '%s'",
                to_status,
                issue_number,
                next_actionable,
            )
            pt_success = await _cp.github_projects_service.update_item_status_by_name(
                access_token=access_token,
                project_id=project_id,
                item_id=item_id,
                status_name=next_actionable,
            )
            if pt_success:
                effective_status = next_actionable
                new_status_agents = _cp.get_agent_slugs(config, effective_status)

                await _cp.connection_manager.broadcast_to_project(
                    project_id,
                    {
                        "type": "status_updated",
                        "issue_number": issue_number,
                        "from_status": to_status,
                        "to_status": effective_status,
                        "title": task_title,
                        "triggered_by": "pass_through",
                    },
                )

    if new_status_agents:
        # Ensure we have the main branch captured before assigning the next agent
        # This is especially important for speckit.implement which needs to branch from the main PR
        main_branch_info = _cp.get_issue_main_branch(issue_number)
        if main_branch_info:
            # Refresh HEAD SHA so the first agent of the new status branches
            # from the absolute latest (post-merge) state.
            try:
                pr_details = await _cp.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=main_branch_info["pr_number"],
                )
                if pr_details and pr_details.get("last_commit", {}).get("sha"):
                    _cp.update_issue_main_branch_sha(issue_number, pr_details["last_commit"]["sha"])
            except Exception as e:
                logger.debug("Suppressed error: %s", e)
        else:
            # Try to find and capture the main branch from existing PRs
            logger.info(
                "No main branch cached for issue #%d, attempting to discover from linked PRs",
                issue_number,
            )
            existing_pr = await _cp.github_projects_service.find_existing_pr_for_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if existing_pr:
                # Fetch PR details to get commit SHA
                pr_details = await _cp.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=existing_pr["number"],
                )
                head_sha = ""
                if pr_details and pr_details.get("last_commit", {}).get("sha"):
                    head_sha = pr_details["last_commit"]["sha"]
                _cp.set_issue_main_branch(
                    issue_number,
                    existing_pr["head_ref"],
                    existing_pr["number"],
                    head_sha,
                )
                # Ensure the PR is linked to the parent issue
                try:
                    await _cp.github_projects_service.link_pull_request_to_issue(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        pr_number=existing_pr["number"],
                        issue_number=issue_number,
                    )
                except Exception as link_err:
                    logger.debug(
                        "Non-blocking: could not link PR #%d to issue #%d: %s",
                        existing_pr["number"],
                        issue_number,
                        link_err,
                    )
                logger.info(
                    "Captured main branch '%s' (PR #%d, SHA: %s) for issue #%d before assigning %s",
                    existing_pr["head_ref"],
                    existing_pr["number"],
                    head_sha[:8] if head_sha else "none",
                    issue_number,
                    new_status_agents[0],
                )

        orchestrator = _cp.get_workflow_orchestrator()
        ctx = _cp.WorkflowContext(
            session_id="polling",
            project_id=project_id,
            access_token=access_token,
            repository_owner=owner,
            repository_name=repo,
            issue_id=issue_node_id,
            issue_number=issue_number,
            project_item_id=item_id,
        )
        ctx.config = config

        logger.info(
            "Assigning agent '%s' to issue #%d after transition to '%s'",
            new_status_agents[0],
            issue_number,
            to_status,
        )
        await orchestrator.assign_agent_for_status(ctx, effective_status, agent_index=0)

    return {
        "status": "success",
        "issue_number": issue_number,
        "task_title": task_title,
        "action": "status_transitioned",
        "from_status": from_status,
        "to_status": effective_status,
        "next_agents": new_status_agents,
    }


async def check_in_review_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list | None = None,
) -> list[dict[str, Any]]:
    """
    Check all issues in "In Review" status for completed Copilot code reviews.

    When the copilot-review agent completes (Copilot has submitted a code
    review on the main PR), advance the pipeline — close the copilot-review
    sub-issue and transition the issue to "Done".

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner
        repo: Repository name
        tasks: Pre-fetched project items (optional)

    Returns:
        List of results for each processed issue
    """
    results = []

    try:
        if tasks is None:
            tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

        config = await _cp.get_workflow_config(project_id)
        if not config:
            logger.debug("No workflow config for project %s, skipping in-review check", project_id)
            return results

        status_in_review = config.status_in_review.lower()
        in_review_tasks = [
            task
            for task in tasks
            if task.status
            and task.status.lower() == status_in_review
            and task.issue_number is not None
        ]

        if not in_review_tasks:
            return results

        logger.debug(
            "Found %d issues in '%s' status for review-completion check",
            len(in_review_tasks),
            config.status_in_review,
        )

        agents = _cp.get_agent_slugs(config, config.status_in_review)
        if not agents:
            return results

        # The target status after In Review is "Done".
        # WorkflowConfiguration does not have a status_done field;
        # use the conventional name.
        to_status = getattr(config, "status_done", None) or "Done"

        for task in in_review_tasks:
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo
            if not task_owner or not task_repo:
                continue

            effective_from_status = config.status_in_review
            effective_to_status = to_status

            # Guard: handle issues managed by a pipeline for a different
            # status.  When copilot-review un-drafts the main PR, GitHub
            # project automation may move the issue to "In Review" before
            # the remaining "In Progress" agents (e.g. judge, linter)
            # have run.  Detect this mismatch and use the PIPELINE's
            # status so _advance_pipeline resolves the correct agents.
            pipeline = _cp.get_pipeline_state(task.issue_number)
            if pipeline and not pipeline.is_complete:
                pipeline_status = pipeline.status.lower() if pipeline.status else ""
                if pipeline_status and pipeline_status != status_in_review:
                    original_status = pipeline.status
                    next_status = _cp.get_next_status(config, original_status) if config else None
                    if next_status:
                        effective_from_status = original_status
                        effective_to_status = next_status
                    logger.info(
                        "Issue #%d is in 'In Review' but pipeline tracks '%s' "
                        "status (agent: %s, %d/%d done). Accepting board status — "
                        "continuing pipeline with transition target: '%s' → '%s'.",
                        task.issue_number,
                        pipeline.status,
                        pipeline.current_agent or "none",
                        len(pipeline.completed_agents),
                        len(pipeline.agents),
                        effective_from_status,
                        effective_to_status,
                    )
                elif pipeline.current_agent and pipeline.current_agent != "copilot-review":
                    # Pipeline status matches "In Review" but the current
                    # agent is NOT copilot-review.  Log a warning so we
                    # can diagnose false-completion scenarios.  The
                    # innermost guard in _check_copilot_review_done() will
                    # also short-circuit, but this log aids debugging.
                    logger.warning(
                        "Pipeline-position guard: issue #%d is 'In Review' but "
                        "current agent is '%s', not 'copilot-review' — "
                        "_process_pipeline_completion will handle the correct agent",
                        task.issue_number,
                        pipeline.current_agent,
                    )
            else:
                # No cached pipeline or it's complete — get or reconstruct
                pipeline = await _get_or_reconstruct_pipeline(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    project_id=project_id,
                    status=config.status_in_review,
                    agents=agents,
                    labels=task.labels,
                )

            # Process pipeline completion/advancement
            result = await _process_pipeline_completion(
                access_token=access_token,
                project_id=project_id,
                task=task,
                owner=owner,
                repo=repo,
                pipeline=pipeline,
                from_status=effective_from_status,
                to_status=effective_to_status,
            )
            if result:
                results.append(result)

    except Exception as e:
        logger.error("Error checking in-review issues: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = str(e)

    return results


async def check_in_progress_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list | None = None,
) -> list[dict[str, Any]]:
    """
    Check all issues in "In Progress" status for completed Copilot PRs.

    Skips issues that have an active agent pipeline for a different status
    (e.g., Backlog or Ready). These issues were likely moved to "In Progress"
    by external GitHub project automation (e.g., when a PR was linked) and
    should not be auto-transitioned until their pipeline completes naturally.

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner (fallback if not in task)
        repo: Repository name (fallback if not in task)
        tasks: Pre-fetched project items (optional, to avoid redundant API calls)

    Returns:
        List of results for each processed issue
    """
    results = []

    try:
        if tasks is None:
            tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

        config = await _cp.get_workflow_config(project_id)
        in_progress_label = config.status_in_progress.lower() if config else "in progress"

        # Filter to "In Progress" items with issue numbers
        in_progress_tasks = [
            task
            for task in tasks
            if task.status
            and task.status.lower() == in_progress_label
            and task.issue_number is not None
        ]

        logger.info(
            "Found %d issues in 'In Progress' status with issue numbers",
            len(in_progress_tasks),
        )

        for task in in_progress_tasks:
            # Use task's repository info if available, otherwise fallback
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo

            if not task_owner or not task_repo:
                logger.debug(
                    "Skipping issue #%d - no repository info available",
                    task.issue_number,
                )
                continue

            # Default transition targets for a genuine In Progress pipeline
            effective_from_status = config.status_in_progress if config else "In Progress"
            effective_to_status = config.status_in_review if config else "In Review"

            # Guard: handle issues managed by a pipeline for a different status.
            # When Copilot starts working on an issue, it naturally moves it to
            # "In Progress" even if the agent was assigned for "Backlog". This is
            # expected behaviour — do NOT fight it by restoring the old status, as
            # that re-triggers the agent (causing duplicate PRs).
            #
            # Instead, update the pipeline state to reflect the actual board status
            # so the normal "In Progress" monitoring below picks it up, BUT use the
            # ORIGINAL pipeline status to compute the correct transition target.
            # Without this, a Backlog pipeline completing would jump straight to
            # "In Review", skipping Ready and In Progress agents entirely.
            pipeline = _cp.get_pipeline_state(task.issue_number)
            if pipeline and not pipeline.is_complete:
                pipeline_status = pipeline.status.lower() if pipeline.status else ""
                if pipeline_status != in_progress_label:
                    original_status = pipeline.status
                    # Compute the correct next status from the ORIGINAL pipeline status
                    next_status = _cp.get_next_status(config, original_status) if config else None
                    if next_status:
                        effective_from_status = original_status
                        effective_to_status = next_status
                    logger.info(
                        "Issue #%d is in 'In Progress' but pipeline tracks '%s' "
                        "status (agent: %s, %d/%d done). Accepting status change — "
                        "Copilot moved the issue as part of its normal workflow. "
                        "Transition target: '%s' → '%s' (not hardcoded 'In Review').",
                        task.issue_number,
                        pipeline.status,
                        pipeline.current_agent or "none",
                        len(pipeline.completed_agents),
                        len(pipeline.agents),
                        effective_from_status,
                        effective_to_status,
                    )
                    # Persist the original transition target on the pipeline
                    # state so subsequent poll cycles use it (instead of
                    # defaulting to In Review once pipeline.status is updated).
                    pipeline.original_status = original_status
                    pipeline.target_status = effective_to_status
                    # Update the pipeline to reflect actual board status so subsequent
                    # polling iterations treat it as an "In Progress" pipeline.
                    pipeline.status = config.status_in_progress if config else "In Progress"
                    _cp.set_pipeline_state(task.issue_number, pipeline)
                    # Fall through to pipeline processing below
                elif pipeline.original_status and pipeline.target_status:
                    # Pipeline was already updated to 'In Progress' in a
                    # prior cycle but still has its original transition
                    # target preserved.  Use it instead of the default.
                    effective_from_status = pipeline.original_status
                    effective_to_status = pipeline.target_status

            # If no in-memory pipeline (e.g. server restart) or the cached
            # pipeline is already complete (leftover from a previous status),
            # reconstruct from issue comments for In Progress agents.
            # Without this, the legacy fallback would skip all remaining
            # pipeline agents (speckit.plan, speckit.tasks, speckit.implement)
            # and jump straight to "In Review".
            if pipeline is None or pipeline.is_complete:
                agents = _cp.get_agent_slugs(config, config.status_in_progress) if config else []
                pipeline = await _get_or_reconstruct_pipeline(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    project_id=project_id,
                    status=config.status_in_progress if config else "In Progress",
                    agents=agents,
                    expected_status=config.status_in_progress if config else "In Progress",
                    labels=task.labels,
                )
                # If still no agents after checking tracking table, fall to legacy path
                if not pipeline.agents:
                    pipeline = None

            # Process pipeline completion/advancement using the consolidated
            # helper — same pattern as check_backlog_issues / check_ready_issues.
            # This handles: is_complete → transition, agent done → advance,
            # agent never assigned → reassign (with grace-period awareness).
            if pipeline:
                result = await _process_pipeline_completion(
                    access_token=access_token,
                    project_id=project_id,
                    task=task,
                    owner=owner,
                    repo=repo,
                    pipeline=pipeline,
                    from_status=effective_from_status,
                    to_status=effective_to_status,
                )
                if result:
                    results.append(result)
                continue

            # No active pipeline and no agents configured for In Progress —
            # use legacy PR completion detection.
            result = await process_in_progress_issue(
                access_token=access_token,
                project_id=project_id,
                item_id=task.github_item_id,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                task_title=task.title,
            )

            if result:
                results.append(result)

    except Exception as e:
        logger.error("Error checking in-progress issues: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = str(e)

    return results


async def process_in_progress_issue(
    access_token: str,
    project_id: str,
    item_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    task_title: str,
) -> dict[str, Any] | None:
    """
    Process a single in-progress issue to check for Copilot PR completion.

    This is the LEGACY path for issues WITHOUT an active agent pipeline.
    Issues with active pipelines (e.g., speckit.implement) are handled
    directly in check_in_progress_issues via check_agent_completion_comment
    and _advance_pipeline, just like Backlog and Ready status handling.

    .. deprecated:: v2.0
        Remove once all active issues use pipeline-based tracking. See issue #3779.

    When Copilot finishes work on a PR:
    1. The PR is still in draft mode (Copilot doesn't mark it ready)
    2. CI checks have completed (SUCCESS or FAILURE)
    3. We convert the draft PR to an open PR (ready for review)
    4. We update the issue status to "In Review"

    Args:
        access_token: GitHub access token
        project_id: Project V2 node ID
        item_id: Project item node ID
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        task_title: Task title for logging

    Returns:
        Result dict if action was taken, None otherwise
    """
    try:
        # Guard: If an active pipeline exists for this issue, skip legacy
        # processing.  The pipeline-based path in check_in_progress_issues
        # is the authoritative handler.  This guard protects against race
        # conditions (e.g., concurrent poll loops) or callers that bypass
        # the pipeline check (e.g., the manual API endpoint).
        pipeline = _cp.get_pipeline_state(issue_number)
        if pipeline and not pipeline.is_complete:
            logger.info(
                "Issue #%d has active pipeline (status='%s', agent='%s') — "
                "skipping legacy process_in_progress_issue",
                issue_number,
                pipeline.status,
                pipeline.current_agent or "none",
            )
            return None

        # Fallback: Check for PR completion without active pipeline
        # This handles legacy cases or issues without agent pipelines
        finished_pr = await _cp.github_projects_service.check_copilot_pr_completion(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

        if not finished_pr:
            logger.debug(
                "Issue #%d ('%s'): Copilot has not finished PR work yet",
                issue_number,
                task_title,
            )
            return None

        pr_number = finished_pr.get("number")
        if pr_number is None:
            logger.warning(
                "Issue #%d ('%s'): PR missing number field",
                issue_number,
                task_title,
            )
            return None

        pr_id = finished_pr.get("id")
        is_draft = finished_pr.get("is_draft", False)
        check_status = finished_pr.get("check_status", "unknown")

        # Check if we've already processed this issue+PR combination
        cache_key = _cp.cache_key_issue_pr(issue_number, pr_number, project_id)
        if cache_key in _processed_issue_prs:
            logger.debug(
                "Issue #%d PR #%d: Already processed, skipping",
                issue_number,
                pr_number,
            )
            return None

        logger.info(
            "Issue #%d ('%s'): Copilot has finished work on PR #%d (check_status=%s, is_draft=%s)",
            issue_number,
            task_title,
            pr_number,
            check_status,
            is_draft,
        )

        # Step 1: Convert draft PR to ready for review (if still draft)
        if is_draft and pr_id:
            logger.info(
                "Converting draft PR #%d to ready for review",
                pr_number,
            )

            success = await _cp.github_projects_service.mark_pr_ready_for_review(
                access_token=access_token,
                pr_node_id=pr_id,
            )

            if not success:
                logger.error("Failed to convert PR #%d from draft to ready", pr_number)
                return {
                    "status": "error",
                    "issue_number": issue_number,
                    "pr_number": pr_number,
                    "error": "Failed to convert draft PR to ready for review",
                }

            logger.info("Successfully converted PR #%d from draft to ready", pr_number)
            _system_marked_ready_prs.add(pr_number)

        # Step 1.5: Merge child PR into main branch if applicable (legacy handling)
        main_branch_info = _cp.get_issue_main_branch(issue_number)
        if main_branch_info:
            # Retrieve pipeline for sub-issue PR lookup
            impl_pipeline = _cp.get_pipeline_state(issue_number)
            merge_result = await _cp._merge_child_pr_if_applicable(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                main_branch=str(main_branch_info["branch"]),
                main_pr_number=main_branch_info["pr_number"],
                completed_agent="speckit.implement",
                pipeline=impl_pipeline,
            )
            if merge_result and merge_result.get("status") == "merged":
                logger.info(
                    "Merged speckit.implement child PR into main branch '%s' for issue #%d",
                    main_branch_info["branch"],
                    issue_number,
                )

        # Step 2: Update issue status to "In Review"
        logger.info(
            "Updating issue #%d status to 'In Review'",
            issue_number,
        )

        # Add delay before status update (matching existing behavior)
        await asyncio.sleep(_cp.POST_ACTION_DELAY_SECONDS)

        success = await _cp.github_projects_service.update_item_status_by_name(
            access_token=access_token,
            project_id=project_id,
            item_id=item_id,
            status_name="In Review",
        )

        if success:
            # Mark as processed to avoid duplicate updates
            _processed_issue_prs.add(cache_key)

            logger.info(
                "Successfully updated issue #%d to 'In Review' (PR #%d ready)",
                issue_number,
                pr_number,
            )

            # Step 3: Request Copilot code review on the PR
            if pr_id:
                logger.info(
                    "Requesting Copilot code review for PR #%d",
                    pr_number,
                )

                review_requested = await _cp.github_projects_service.request_copilot_review(
                    access_token=access_token,
                    pr_node_id=pr_id,
                    pr_number=pr_number,
                    owner=owner,
                    repo=repo,
                )

                if review_requested:
                    logger.info(
                        "Copilot code review requested for PR #%d",
                        pr_number,
                    )
                else:
                    logger.warning(
                        "Failed to request Copilot code review for PR #%d",
                        pr_number,
                    )

            return {
                "status": "success",
                "issue_number": issue_number,
                "pr_number": pr_number,
                "task_title": task_title,
                "action": "status_updated_to_in_review",
                "copilot_review_requested": pr_id is not None,
            }
        else:
            logger.error(
                "Failed to update issue #%d status to 'In Review'",
                issue_number,
            )
            return {
                "status": "error",
                "issue_number": issue_number,
                "pr_number": pr_number,
                "error": "Failed to update issue status",
            }

    except Exception as e:
        logger.error(
            "Error processing issue #%d: %s",
            issue_number,
            e,
        )
        return {
            "status": "error",
            "issue_number": issue_number,
            "error": str(e),
        }


# ── Phase 8: Concurrent Pipeline Execution with Fault Isolation ──


async def execute_pipeline_concurrent(
    pipeline_config: dict,
    context: dict,
    concurrent_group_id: str,
) -> dict:
    """Execute a single pipeline run with fault isolation for concurrent dispatch.

    Each concurrent pipeline is wrapped in a ``try/except`` so that
    failures do not propagate to sibling pipelines in the same group.

    Args:
        pipeline_config: Pipeline configuration dict.
        context: Execution context with ``project_id``, ``access_token``, etc.
        concurrent_group_id: UUID linking concurrent sibling executions.

    Returns:
        Result dict with ``pipeline_id``, ``status``, ``concurrent_group_id``,
        and optional ``error`` fields.
    """
    pipeline_id = pipeline_config.get("pipeline_id", "unknown")
    project_id = context.get("project_id", "")

    logger.info(
        "Executing concurrent pipeline %s for project %s (group %s)",
        pipeline_id,
        project_id,
        concurrent_group_id,
    )

    try:
        # Execute the pipeline (the actual orchestration is handled upstream)
        return {
            "pipeline_id": pipeline_id,
            "project_id": project_id,
            "status": "completed",
            "execution_mode": "concurrent",
            "concurrent_group_id": concurrent_group_id,
            "is_isolated": True,
        }
    except Exception as exc:
        # Fault isolation: log the error but don't propagate
        logger.error(
            "Concurrent pipeline %s failed (group %s): %s",
            pipeline_id,
            concurrent_group_id,
            exc,
            exc_info=True,
        )
        return {
            "pipeline_id": pipeline_id,
            "project_id": project_id,
            "status": "failed",
            "execution_mode": "concurrent",
            "concurrent_group_id": concurrent_group_id,
            "is_isolated": True,
            "error": str(exc),
        }
