"""Pipeline state management, status checking, and advancement logic."""

import asyncio
from datetime import datetime
from typing import Any

import src.services.copilot_polling as _cp
from src.constants import ACTIVE_LABEL, build_agent_label, find_agent_label, find_pipeline_label
from src.logging_utils import get_logger
from src.utils import utcnow

from .state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    _claimed_child_prs,
    _pending_agent_assignments,
    _polling_state,
    _processed_issue_prs,
    _system_marked_ready_prs,
)

logger = get_logger(__name__)


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
        from src.services.pipelines.service import PipelineService

        svc = PipelineService()
        configs = await svc.list_pipelines(project_id)
        matched_config = next((c for c in configs if c.name == config_name), None)
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
    pipeline.completed_agents.append(completed_agent)
    pipeline.current_agent_index += 1

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
            await asyncio.sleep(_cp.POST_ACTION_DELAY_SECONDS)
        elif merge_result and merge_result.get("status") == "merge_failed":
            # A child PR exists but could not be merged.  Block the
            # pipeline so the next agent does NOT start on a stale base.
            # The next polling cycle will retry the merge.
            logger.warning(
                "Safety-net merge FAILED for agent '%s' on issue #%d "
                "(child PR #%s) — blocking pipeline advance until "
                "child PR is merged",
                completed_agent,
                issue_number,
                merge_result.get("pr_number"),
            )
            # Roll back the pipeline advance.  Because external side
            # effects (tracking table, sub-issue close) have NOT been
            # applied yet, this rollback is fully consistent.
            pipeline.current_agent_index -= 1
            if completed_agent in pipeline.completed_agents:
                pipeline.completed_agents.remove(completed_agent)
            _cp.set_pipeline_state(issue_number, pipeline)
            return {
                "status": "merge_blocked",
                "issue_number": issue_number,
                "task_title": task_title,
                "action": "merge_blocked",
                "agent_name": completed_agent,
                "blocked_pr": merge_result.get("pr_number"),
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

    # Close the completed agent's sub-issue
    sub_info = None
    if pipeline.agent_sub_issues:
        sub_info = pipeline.agent_sub_issues.get(completed_agent)
    # Fall back to the global sub-issue store (survives pipeline resets)
    if not sub_info:
        global_subs = _cp.get_issue_sub_issues(issue_number)
        sub_info = global_subs.get(completed_agent)
    if sub_info and sub_info.get("number") and sub_info["number"] != issue_number:
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
                "Closed sub-issue #%d for completed agent '%s'",
                sub_info["number"],
                completed_agent,
            )
        except Exception as e:
            logger.warning(
                "Failed to close sub-issue #%d for agent '%s': %s",
                sub_info["number"],
                completed_agent,
                e,
            )

        # Update the sub-issue's project board Status to "Done"
        try:
            sub_node_id = sub_info.get("node_id", "")
            if sub_node_id:
                await _cp.github_projects_service.update_sub_issue_project_status(
                    access_token=access_token,
                    project_id=project_id,
                    sub_issue_node_id=sub_node_id,
                    status_name="Done",
                )
        except Exception as e:
            logger.warning(
                "Failed to update sub-issue #%d board status to Done: %s",
                sub_info["number"],
                e,
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
        # Pipeline complete → transition to next status
        _cp.remove_pipeline_state(issue_number)
        return await _transition_after_pipeline_complete(
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
    else:
        # Assign next agent
        next_agent = pipeline.current_agent
        pipeline.started_at = utcnow()
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

    # Remove any old pipeline state for this issue
    _cp.remove_pipeline_state(issue_number)

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
                    from .state import _copilot_review_requested_at

                    _copilot_review_requested_at[issue_number] = utcnow()
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
            # DEPRECATED(v2.0): Remove once all active issues use pipeline-based tracking.
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
                # DEPRECATED(v2.0): Remove once all active issues use pipeline-based tracking.
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
            # DEPRECATED(v2.0): Remove once all active issues use pipeline-based tracking.
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
    # DEPRECATED(v2.0): Remove once all active issues use pipeline-based tracking.
    Issues with active pipelines (e.g., speckit.implement) are handled
    directly in check_in_progress_issues via check_agent_completion_comment
    and _advance_pipeline, just like Backlog and Ready status handling.

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
        # DEPRECATED(v2.0): Remove once all active issues use pipeline-based tracking.
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
        cache_key = _cp.cache_key_issue_pr(issue_number, pr_number)
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

        # DEPRECATED(v2.0): Remove once all active issues use pipeline-based tracking.
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
