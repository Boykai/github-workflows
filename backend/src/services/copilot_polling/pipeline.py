"""
Pipeline advancement & completion for the Copilot polling service.
"""

import logging
from datetime import datetime
from typing import Any

from src.services.agent_tracking import get_current_agent_from_tracking
from . import _deps
from src.services.workflow_orchestrator import (
    PipelineState,
    WorkflowContext,
    WorkflowState,
    get_agent_slugs,
    get_issue_main_branch,
    get_pipeline_state,
    get_workflow_config,
    get_workflow_orchestrator,
    find_next_actionable_status,
    remove_pipeline_state,
    set_issue_main_branch,
    set_pipeline_state,
)

from .state import (
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    _pending_agent_assignments,
    _system_marked_ready_prs,
)
from .tracking import (
    _check_agent_done_on_sub_or_parent,
    _get_tracking_state_from_issue,
)

logger = logging.getLogger(__name__)


async def _process_pipeline_completion(
    access_token: str,
    project_id: str,
    task: Any,
    owner: str,
    repo: str,
    pipeline: PipelineState,
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
        completed = await _check_agent_done_on_sub_or_parent(
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
                age = (datetime.utcnow() - pipeline.started_at).total_seconds()
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
            body, _comments = await _get_tracking_state_from_issue(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
            )
            tracking_step = get_current_agent_from_tracking(body)
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
                    (datetime.utcnow() - pending_ts).total_seconds(),
                )
                return None

            # Check if current agent has started work (created a PR)
            main_branch_info = get_issue_main_branch(task.issue_number)
            if main_branch_info:
                from .pr_detection import _find_completed_child_pr

                child_pr = await _find_completed_child_pr(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    main_branch=main_branch_info["branch"],
                    main_pr_number=main_branch_info["pr_number"],
                    agent_name=current_agent,
                )
                # If no child PR exists (even incomplete), the agent was never assigned
                if child_pr is None:
                    # Check if there's even an incomplete child PR in progress
                    linked_prs = await _deps.github_projects_service.get_linked_pull_requests(
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
                        and "copilot" in pr.get("author", "").lower()
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
                        orchestrator = get_workflow_orchestrator()
                        ctx = WorkflowContext(
                            session_id="polling",
                            project_id=project_id,
                            access_token=access_token,
                            repository_owner=task_owner,
                            repository_name=task_repo,
                            issue_id=task.github_content_id,
                            issue_number=task.issue_number,
                            project_item_id=task.github_item_id,
                            current_state=WorkflowState.READY,
                        )
                        ctx.config = get_workflow_config(project_id)

                        assigned = await orchestrator.assign_agent_for_status(
                            ctx, from_status, agent_index=pipeline.current_agent_index
                        )
                        if assigned:
                            _pending_agent_assignments[pending_key] = datetime.utcnow()
                            return {
                                "status": "success",
                                "issue_number": task.issue_number,
                                "action": "agent_assigned_after_reconstruction",
                                "agent_name": current_agent,
                                "from_status": from_status,
                            }

    return None


async def _advance_pipeline(
    access_token: str,
    project_id: str,
    item_id: str,
    owner: str,
    repo: str,
    issue_number: int,
    issue_node_id: str | None,
    pipeline: PipelineState,
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

    # Close the completed agent's sub-issue
    if pipeline.agent_sub_issues:
        sub_info = pipeline.agent_sub_issues.get(completed_agent)
        if sub_info and sub_info.get("number") and sub_info["number"] != issue_number:
            try:
                await _deps.github_projects_service.update_issue_state(
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
                    await _deps.github_projects_service.update_sub_issue_project_status(
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

    # NOTE: Child PR merge now happens in post_agent_outputs_from_pr BEFORE the Done! comment
    # is posted. This ensures GitHub has time to process the merge before we assign the next agent.

    # Send agent_completed WebSocket notification
    await _deps.connection_manager.broadcast_to_project(
        project_id,
        {
            "type": "agent_completed",
            "issue_number": issue_number,
            "agent_name": completed_agent,
            "status": from_status,
            "next_agent": pipeline.current_agent if not pipeline.is_complete else None,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    if pipeline.is_complete:
        # Pipeline complete → transition to next status
        remove_pipeline_state(issue_number)
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
        pipeline.started_at = datetime.utcnow()
        set_pipeline_state(issue_number, pipeline)

        logger.info("Assigning next agent '%s' to issue #%d", next_agent, issue_number)

        orchestrator = get_workflow_orchestrator()
        ctx = WorkflowContext(
            session_id="polling",
            project_id=project_id,
            access_token=access_token,
            repository_owner=owner,
            repository_name=repo,
            issue_id=issue_node_id,
            issue_number=issue_number,
            project_item_id=item_id,
            current_state=WorkflowState.READY,
        )
        ctx.config = get_workflow_config(project_id)

        success = await orchestrator.assign_agent_for_status(
            ctx, from_status, agent_index=pipeline.current_agent_index
        )

        # Send agent_assigned WebSocket notification
        if success:
            await _deps.connection_manager.broadcast_to_project(
                project_id,
                {
                    "type": "agent_assigned",
                    "issue_number": issue_number,
                    "agent_name": next_agent,
                    "status": from_status,
                    "next_agent": pipeline.next_agent,
                    "timestamp": datetime.utcnow().isoformat(),
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
    success = await _deps.github_projects_service.update_item_status_by_name(
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
    remove_pipeline_state(issue_number)

    # When transitioning to "In Review", convert main PR from draft→ready
    # and request Copilot code review on the main PR
    if to_status.lower() == "in review":
        main_branch_info = get_issue_main_branch(issue_number)
        if main_branch_info:
            main_pr_number = main_branch_info["pr_number"]
            main_pr_details = await _deps.github_projects_service.get_pull_request(
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
                    mark_ready_success = await _deps.github_projects_service.mark_pr_ready_for_review(
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
                    review_requested = await _deps.github_projects_service.request_copilot_review(
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
    await _deps.connection_manager.broadcast_to_project(
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
    config = get_workflow_config(project_id)
    new_status_agents = get_agent_slugs(config, to_status) if config else []

    # Pass-through: if new status has no agents, find the next actionable status (T028)
    effective_status = to_status
    if config and not new_status_agents:
        next_actionable = find_next_actionable_status(config, to_status)
        if next_actionable and next_actionable != to_status:
            logger.info(
                "Pass-through: '%s' has no agents, advancing issue #%d to '%s'",
                to_status,
                issue_number,
                next_actionable,
            )
            pt_success = await _deps.github_projects_service.update_item_status_by_name(
                access_token=access_token,
                project_id=project_id,
                item_id=item_id,
                status_name=next_actionable,
            )
            if pt_success:
                effective_status = next_actionable
                new_status_agents = get_agent_slugs(config, effective_status)

                await _deps.connection_manager.broadcast_to_project(
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
        main_branch_info = get_issue_main_branch(issue_number)
        if not main_branch_info:
            # Try to find and capture the main branch from existing PRs
            logger.info(
                "No main branch cached for issue #%d, attempting to discover from linked PRs",
                issue_number,
            )
            existing_pr = await _deps.github_projects_service.find_existing_pr_for_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if existing_pr:
                # Fetch PR details to get commit SHA
                pr_details = await _deps.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=existing_pr["number"],
                )
                head_sha = ""
                if pr_details and pr_details.get("last_commit", {}).get("sha"):
                    head_sha = pr_details["last_commit"]["sha"]
                set_issue_main_branch(
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

        orchestrator = get_workflow_orchestrator()
        ctx = WorkflowContext(
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
