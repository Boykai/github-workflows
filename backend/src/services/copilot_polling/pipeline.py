"""Pipeline state management, status checking, and advancement logic."""

import asyncio
import logging
from typing import Any

import src.services.copilot_polling as _cp
from src.utils import utcnow

from .state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    _claimed_child_prs,
    _pending_agent_assignments,
    _polling_state,
    _processed_issue_prs,
    _system_marked_ready_prs,
)

logger = logging.getLogger(__name__)


async def _get_or_reconstruct_pipeline(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
    status: str,
    agents: list[str],
    expected_status: str | None = None,
) -> "_cp.PipelineState":
    """
    Get existing pipeline state or reconstruct from issue comments.

    This consolidates the repeated pattern of checking for existing pipeline
    state and reconstructing it if missing or for a different status.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        project_id: Project ID
        status: Current workflow status
        agents: Ordered list of agents for this status
        expected_status: If provided, only use cached pipeline if status matches

    Returns:
        PipelineState (either cached or reconstructed)
    """
    pipeline = _cp.get_pipeline_state(issue_number)

    # Use cached pipeline if it exists and matches expected status
    if pipeline is not None:
        if expected_status is None or pipeline.status == expected_status:
            return pipeline

    # Reconstruct from comments
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
        if pipeline.completed_agents and not completed:
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

            # Check if current agent has started work (created a PR)
            main_branch_info = _cp.get_issue_main_branch(task.issue_number)
            if main_branch_info:
                child_pr = await _cp._find_completed_child_pr(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    main_branch=main_branch_info["branch"],
                    main_pr_number=main_branch_info["pr_number"],
                    agent_name=current_agent,
                    pipeline=pipeline,
                )
                # If no child PR exists (even incomplete), the agent was never assigned
                if child_pr is None:
                    # Check if there's even an incomplete child PR in progress
                    linked_prs = await _cp.github_projects_service.get_linked_pull_requests(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=task.issue_number,
                    )
                    # Count PRs that target the main branch (excluding the main PR itself)
                    child_prs_for_current_agent = [
                        pr
                        for pr in (linked_prs or [])
                        if int(pr.get("number", 0)) != main_branch_info["pr_number"]
                        and _cp.github_projects_service.is_copilot_author(pr.get("author", ""))
                    ]
                    # If there are completed agents but the current agent's PR doesn't exist,
                    # we need to trigger it. Count expected PRs vs actual child PRs.
                    expected_child_prs = len(pipeline.completed_agents)
                    actual_child_prs = len(child_prs_for_current_agent)

                    if actual_child_prs < expected_child_prs + 1:
                        # Current agent was never assigned - trigger it now
                        logger.info(
                            "Agent '%s' was never assigned for issue #%d (found %d child PRs, "
                            "expected %d for %d completed agents) — assigning now",
                            current_agent,
                            task.issue_number,
                            actual_child_prs,
                            expected_child_prs + 1,
                            len(pipeline.completed_agents),
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

                        assigned = await orchestrator.assign_agent_for_status(
                            ctx, from_status, agent_index=pipeline.current_agent_index
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
        if not agents:
            return results

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
            )

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
        if not agents:
            return results

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
            )

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

    try:
        issue_data = await _cp.github_projects_service.get_issue_with_comments(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

        comments = issue_data.get("comments", []) if issue_data else []

        # Check each agent sequentially — stop at first incomplete
        for agent in agents:
            marker = f"{agent}: Done!"
            if any(marker in comment.get("body", "") for comment in comments):
                completed.append(agent)
            else:
                break

        # Claim all MERGED child PRs for completed agents
        # This prevents subsequent agents from re-detecting them
        if completed:
            main_branch_info = _cp.get_issue_main_branch(issue_number)
            if main_branch_info:
                main_branch = main_branch_info.get("branch")
                main_pr_number = main_branch_info.get("pr_number")
                if main_branch and main_pr_number:
                    linked_prs = await _cp.github_projects_service.get_linked_pull_requests(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                    )
                    for pr in linked_prs or []:
                        pr_number = pr.get("number")
                        pr_state = pr.get("state", "").upper()
                        if pr_number and pr_state == "MERGED" and pr_number != main_pr_number:
                            # Get PR details to check if it targets the main branch
                            pr_details = await _cp.github_projects_service.get_pull_request(
                                access_token=access_token,
                                owner=owner,
                                repo=repo,
                                pr_number=pr_number,
                            )
                            if pr_details and pr_details.get("base_ref") == main_branch:
                                # Claim this merged child PR for all completed agents
                                # This prevents re-detection
                                for completed_agent in completed:
                                    claimed_key = f"{issue_number}:{pr_number}:{completed_agent}"
                                    if claimed_key not in _claimed_child_prs:
                                        _claimed_child_prs.add(claimed_key)
                                        logger.debug(
                                            "Claimed merged child PR #%d for agent '%s' "
                                            "during pipeline reconstruction (issue #%d)",
                                            pr_number,
                                            completed_agent,
                                            issue_number,
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
        except Exception as e:
            logger.debug("Could not capture HEAD SHA during reconstruction: %s", e)

    pipeline = _cp.PipelineState(
        issue_number=issue_number,
        project_id=project_id,
        status=status,
        agents=list(agents),
        current_agent_index=len(completed),
        completed_agents=completed,
        started_at=utcnow(),
        agent_assigned_sha=reconstructed_sha,
    )

    # Reconstruct sub-issue mappings from GitHub API
    pipeline.agent_sub_issues = await _cp._reconstruct_sub_issue_mappings(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )

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
    assert completed_agent is not None, "No current agent in pipeline"
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

    # NOTE: Child PR merge is handled in post_agent_outputs_from_pr BEFORE
    # the Done! comment is posted.  The safety-net merge below catches edge
    # cases where Step 0 could not merge (e.g. Done! posted externally,
    # child PR found via sub-issue fallback without is_child_pr flag).

    # ── Safety-net: ensure the completed agent's child PR is merged
    # BEFORE advancing further (whether to the next agent or to the
    # next status).  This runs for ALL agents including the last one
    # in a pipeline.  Without this, the pipeline.is_complete path
    # goes straight to _transition_after_pipeline_complete, which has
    # no merge of its own — leaving the child PR unmerged (#740).
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
        if merge_result:
            logger.info(
                "Safety-net merge: child PR for agent '%s' merged in _advance_pipeline (issue #%d)",
                completed_agent,
                issue_number,
            )
            await asyncio.sleep(_cp.POST_ACTION_DELAY_SECONDS)

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

        logger.info("Assigning next agent '%s' to issue #%d", next_agent, issue_number)

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
            ctx, from_status, agent_index=pipeline.current_agent_index
        )

        # Send agent_assigned WebSocket notification
        if success:
            await _cp.connection_manager.broadcast_to_project(
                project_id,
                {
                    "type": "agent_assigned",
                    "issue_number": issue_number,
                    "agent_name": next_agent,
                    "status": from_status,
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
    # and request Copilot code review on the main PR
    if to_status.lower() == "in review":
        main_branch_info = _cp.get_issue_main_branch(issue_number)
        if main_branch_info:
            main_pr_number = main_branch_info["pr_number"]
            main_pr_details = await _cp.github_projects_service.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=main_pr_number,
            )
            if main_pr_details:
                main_pr_id = main_pr_details.get("id")
                main_pr_is_draft = main_pr_details.get("is_draft", False)

                # Convert draft → ready
                if main_pr_is_draft and main_pr_id:
                    logger.info(
                        "Converting main PR #%d from draft to ready for review",
                        main_pr_number,
                    )
                    mark_ready_success = await _cp.github_projects_service.mark_pr_ready_for_review(
                        access_token=access_token,
                        pr_node_id=main_pr_id,
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
                    )
                    if review_requested:
                        logger.info(
                            "Copilot code review requested for main PR #%d",
                            main_pr_number,
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
            except Exception:
                pass
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
                    # Update the pipeline to reflect actual board status so subsequent
                    # polling iterations treat it as an "In Progress" pipeline.
                    pipeline.status = config.status_in_progress if config else "In Progress"
                    _cp.set_pipeline_state(task.issue_number, pipeline)
                    # Fall through to the normal In Progress handling below
                    # (don't 'continue')

            # Check for active pipeline (e.g., speckit.implement)
            if (
                pipeline
                and not pipeline.is_complete
                and pipeline.status.lower() == in_progress_label
            ):
                # Check if current agent has completed (via Done! comment marker)
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
                        result = await _advance_pipeline(
                            access_token=access_token,
                            project_id=project_id,
                            item_id=task.github_item_id,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=task.issue_number,
                            issue_node_id=task.github_content_id,
                            pipeline=pipeline,
                            from_status=effective_from_status,
                            to_status=effective_to_status,
                            task_title=task.title,
                        )
                        if result:
                            results.append(result)
                continue

            # No active pipeline — use legacy PR completion detection
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
            if merge_result:
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
