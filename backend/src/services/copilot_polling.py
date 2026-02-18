"""
Background Polling Service for Copilot PR Completion Detection

This service polls GitHub Issues in "In Progress" status to detect when
GitHub Copilot has completed work on linked Pull Requests.

When a Copilot PR is detected as complete (no longer a draft):
1. Convert the draft PR to ready for review (if still draft)
2. Update the linked issue status to "In Review"

This provides a fallback mechanism in addition to webhooks.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from src.constants import (
    AGENT_OUTPUT_FILES,
    cache_key_agent_output,
    cache_key_issue_pr,
    cache_key_review_requested,
)
from src.models.chat import WorkflowConfiguration
from src.services.agent_tracking import (
    STATE_DONE,
    get_current_agent_from_tracking,
    get_next_pending_agent,
    mark_agent_active,
    mark_agent_done,
    parse_tracking_from_body,
)
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.services.workflow_orchestrator import (
    PipelineState,
    WorkflowContext,
    WorkflowState,
    find_next_actionable_status,
    get_agent_slugs,
    get_issue_main_branch,
    get_pipeline_state,
    get_workflow_config,
    get_workflow_orchestrator,
    remove_pipeline_state,
    set_issue_main_branch,
    set_pipeline_state,
    set_workflow_config,
    update_issue_main_branch_sha,
)

logger = logging.getLogger(__name__)


@dataclass
class PollingState:
    """State tracking for the polling service."""

    is_running: bool = False
    last_poll_time: datetime | None = None
    poll_count: int = 0
    errors_count: int = 0
    last_error: str | None = None
    processed_issues: dict[int, datetime] = field(default_factory=dict)


# Global polling state
_polling_state = PollingState()

# Reference to the current polling asyncio.Task so we can cancel it
# before starting a new one (prevents concurrent loops).
_polling_task: asyncio.Task | None = None

# Track issues we've already processed to avoid duplicate updates
_processed_issue_prs: set[str] = set()  # "issue_number:pr_number"

# Track issues where we've already posted agent outputs to avoid duplicates
_posted_agent_outputs: set[str] = set()  # "issue_number:agent_name:pr_number"

# Track which child PRs have been claimed/attributed to an agent
# This prevents subsequent agents from re-using already-completed child PRs
_claimed_child_prs: set[str] = set()  # "issue_number:pr_number:agent_name"

# Track agents that we've already assigned (pending Copilot to start working).
# This prevents the polling loop from re-assigning the same agent every cycle
# before Copilot has had time to create its child PR.
_pending_agent_assignments: set[str] = set()  # "issue_number:agent_name"

# Track PRs that OUR system converted from draft → ready.
# This prevents _check_main_pr_completion Signal 1 from misinterpreting
# a non-draft PR as agent completion when we ourselves marked it ready.
_system_marked_ready_prs: set[int] = set()  # pr_number

# Recovery cooldown: tracks when we last attempted recovery for each issue.
# Prevents re-assigning an agent every poll cycle — gives Copilot time to start.
_recovery_last_attempt: dict[int, datetime] = {}  # issue_number -> last attempt time
RECOVERY_COOLDOWN_SECONDS = 300  # 5 minutes between recovery attempts per issue


# ──────────────────────────────────────────────────────────────────────────────
# Issue Body Tracking Helpers
# ──────────────────────────────────────────────────────────────────────────────


async def _update_issue_tracking(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    agent_name: str,
    new_state: str,
) -> bool:
    """
    Update the agent tracking table in a GitHub Issue's body.

    Fetches the current body, updates the agent's state, and pushes it back.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        agent_name: Agent name to update
        new_state: "active" or "done"

    Returns:
        True if update succeeded
    """
    try:
        issue_data = await github_projects_service.get_issue_with_comments(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )
        body = issue_data.get("body", "")
        if not body:
            return False

        if new_state == "active":
            updated_body = mark_agent_active(body, agent_name)
        elif new_state == "done":
            updated_body = mark_agent_done(body, agent_name)
        else:
            return False

        if updated_body == body:
            return True  # No change needed

        success = await github_projects_service.update_issue_body(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            body=updated_body,
        )
        if success:
            logger.info(
                "Tracking update: '%s' → %s on issue #%d",
                agent_name,
                new_state,
                issue_number,
            )
        return success
    except Exception as e:
        logger.warning("Failed to update tracking for issue #%d: %s", issue_number, e)
        return False


async def _get_tracking_state_from_issue(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
) -> tuple[str, list[dict]]:
    """
    Fetch the issue body and comments for tracking-based decisions.

    Returns:
        Tuple of (body, comments)
    """
    issue_data = await github_projects_service.get_issue_with_comments(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )
    return issue_data.get("body", ""), issue_data.get("comments", [])


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline State Management Helpers
# ──────────────────────────────────────────────────────────────────────────────


async def _get_or_reconstruct_pipeline(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
    status: str,
    agents: list[str],
    expected_status: str | None = None,
) -> PipelineState:
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
    pipeline = get_pipeline_state(issue_number)

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
        completed = await github_projects_service.check_agent_completion_comment(
            access_token=access_token,
            owner=task_owner,
            repo=task_repo,
            issue_number=task.issue_number,
            agent_name=current_agent,
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
            if pending_key in _pending_agent_assignments:
                logger.debug(
                    "Agent '%s' already assigned for issue #%d (in-memory), waiting for Copilot to start working",
                    current_agent,
                    task.issue_number,
                )
                return None

            # Check if current agent has started work (created a PR)
            main_branch_info = get_issue_main_branch(task.issue_number)
            if main_branch_info:
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
                    linked_prs = await github_projects_service.get_linked_pull_requests(
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
                            _pending_agent_assignments.add(pending_key)
                            return {
                                "status": "success",
                                "issue_number": task.issue_number,
                                "action": "agent_assigned_after_reconstruction",
                                "agent_name": current_agent,
                                "from_status": from_status,
                            }

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Agent Output Posting
# ──────────────────────────────────────────────────────────────────────────────


async def post_agent_outputs_from_pr(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list[dict[str, Any]]:
    """
    For all issues with active pipelines, check if the current agent's PR work
    is complete. If so, fetch any .md files from the PR (if present), post them
    as issue comments, and post the ``<agent-name>: Done!`` marker.

    All agents are eligible — output files are optional, not required.

    This runs BEFORE the status-specific checks (backlog/ready/in-progress) so
    that the Done! markers are in place for the existing comment-based detection.

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner
        repo: Repository name
        tasks: Pre-fetched project items

    Returns:
        List of results for each issue where outputs were posted
    """
    results = []

    try:
        config = get_workflow_config(project_id)
        if not config:
            return results

        # Find all issues with active pipelines
        for task in tasks:
            if task.issue_number is None:
                continue

            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo
            if not task_owner or not task_repo:
                continue

            pipeline = get_pipeline_state(task.issue_number)

            # If in-memory pipeline state is missing (e.g., after container
            # restart), reconstruct from the durable tracking table in the
            # issue body.  This ensures agent completions are detected and
            # Done! markers posted even when volatile state has been lost.
            # Without this, Step 0 skips the issue entirely, the Done!
            # marker is never posted, and recovery (Step 5) mistakenly
            # re-assigns the same agent — causing duplicate PRs.
            if pipeline is None:
                try:
                    body, comments = await _get_tracking_state_from_issue(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=task.issue_number,
                    )
                    steps = parse_tracking_from_body(body)
                    active_step = get_current_agent_from_tracking(body)
                    if steps and active_step:
                        status_key = active_step.status
                        # Build agent list for this status from the tracking table
                        status_agents = [
                            s.agent_name for s in steps if s.status == status_key
                        ]
                        # Determine completed agents by checking Done! comments
                        completed: list[str] = []
                        for agent in status_agents:
                            done_marker = f"{agent}: Done!"
                            if any(
                                done_marker in c.get("body", "") for c in comments
                            ):
                                completed.append(agent)
                            else:
                                break  # Sequential — stop at first incomplete

                        pipeline = PipelineState(
                            issue_number=task.issue_number,
                            project_id=project_id,
                            status=status_key,
                            agents=status_agents,
                            current_agent_index=len(completed),
                            completed_agents=completed,
                            started_at=datetime.utcnow(),
                        )
                        set_pipeline_state(task.issue_number, pipeline)
                        logger.info(
                            "Reconstructed pipeline for issue #%d from tracking "
                            "table: active agent '%s', status '%s', %d/%d done",
                            task.issue_number,
                            active_step.agent_name,
                            status_key,
                            len(completed),
                            len(status_agents),
                        )

                        # Reconstruct main branch info if missing so that
                        # subsequent-agent child PR detection works correctly
                        if not get_issue_main_branch(task.issue_number):
                            try:
                                existing_pr = await github_projects_service.find_existing_pr_for_issue(
                                    access_token=access_token,
                                    owner=task_owner,
                                    repo=task_repo,
                                    issue_number=task.issue_number,
                                )
                                if existing_pr:
                                    pr_det = await github_projects_service.get_pull_request(
                                        access_token=access_token,
                                        owner=task_owner,
                                        repo=task_repo,
                                        pr_number=existing_pr["number"],
                                    )
                                    h_sha = (
                                        pr_det.get("last_commit", {}).get("sha", "")
                                        if pr_det
                                        else ""
                                    )
                                    set_issue_main_branch(
                                        task.issue_number,
                                        existing_pr["head_ref"],
                                        existing_pr["number"],
                                        h_sha,
                                    )
                                    logger.info(
                                        "Reconstructed main branch '%s' (PR #%d) "
                                        "for issue #%d",
                                        existing_pr["head_ref"],
                                        existing_pr["number"],
                                        task.issue_number,
                                    )
                            except Exception as e:
                                logger.debug(
                                    "Could not reconstruct main branch for "
                                    "issue #%d: %s",
                                    task.issue_number,
                                    e,
                                )
                except Exception as e:
                    logger.debug(
                        "Could not reconstruct pipeline for issue #%d: %s",
                        task.issue_number,
                        e,
                    )

            if not pipeline or pipeline.is_complete:
                continue

            current_agent = pipeline.current_agent
            if not current_agent:
                continue

            # Check if we already posted outputs for this agent on this issue
            cache_prefix = f"{task.issue_number}:{current_agent}"
            if any(k.startswith(cache_prefix) for k in _posted_agent_outputs):
                continue

            # Check if the Done! marker is already posted (agent did it itself)
            marker = f"{current_agent}: Done!"
            already_done = await github_projects_service.check_agent_completion_comment(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                agent_name=current_agent,
            )
            if already_done:
                continue

            # Determine if this is a subsequent agent (not the first in the overall pipeline).
            main_branch_info = get_issue_main_branch(task.issue_number)
            main_pr_number = main_branch_info["pr_number"] if main_branch_info else None
            main_branch = main_branch_info["branch"] if main_branch_info else None
            is_subsequent_agent = main_branch_info is not None

            finished_pr = None

            # For subsequent agents, check child PR completion FIRST
            # Subsequent agents create child PRs targeting the main branch (not 'main')
            if is_subsequent_agent and main_branch and main_pr_number:
                child_pr_info = await _find_completed_child_pr(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    main_branch=main_branch,
                    main_pr_number=main_pr_number,
                    agent_name=current_agent,
                )
                if child_pr_info:
                    finished_pr = child_pr_info
                    logger.info(
                        "Found completed child PR #%d for agent '%s' on issue #%d",
                        child_pr_info.get("number"),
                        current_agent,
                        task.issue_number,
                    )

            # If no child PR, check for standard Copilot PR completion (first agent)
            if not finished_pr:
                finished_pr = await github_projects_service.check_copilot_pr_completion(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                )

            if not finished_pr:
                # No completed PR found via standard detection.
                # For subsequent agents, also check if work was done directly
                # on the main PR (Copilot pushes commits to the same branch
                # rather than creating a child PR).
                if is_subsequent_agent and main_pr_number is not None:
                    main_pr_completed = await _check_main_pr_completion(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        main_pr_number=main_pr_number,
                        issue_number=task.issue_number,
                        agent_name=current_agent,
                        pipeline_started_at=pipeline.started_at,
                        agent_assigned_sha=pipeline.agent_assigned_sha,
                    )
                    if main_pr_completed:
                        # Use the main PR as the finished PR
                        pr_details = await github_projects_service.get_pull_request(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            pr_number=main_pr_number,
                        )
                        if pr_details:
                            finished_pr = {
                                "number": main_pr_number,
                                "id": pr_details.get("id"),
                                "head_ref": pr_details.get("head_ref", ""),
                                "last_commit": pr_details.get("last_commit"),
                                "copilot_finished": True,
                            }
                if not finished_pr:
                    continue

            pr_number = finished_pr.get("number")
            if not pr_number:
                continue

            # For subsequent agents, the main PR may show completion signals.
            # We need to verify these are FRESH signals (after pipeline start)
            # to avoid re-attributing the first agent's work.
            if is_subsequent_agent and pr_number == main_pr_number and main_pr_number is not None:
                main_pr_completed = await _check_main_pr_completion(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    main_pr_number=main_pr_number,
                    issue_number=task.issue_number,
                    agent_name=current_agent,
                    pipeline_started_at=pipeline.started_at,
                    agent_assigned_sha=pipeline.agent_assigned_sha,
                )
                if not main_pr_completed:
                    logger.debug(
                        "Main PR #%d has no fresh completion signals for agent '%s' "
                        "on issue #%d — still in progress",
                        pr_number,
                        current_agent,
                        task.issue_number,
                    )
                    continue

            cache_key = cache_key_agent_output(task.issue_number, current_agent, pr_number)
            if cache_key in _posted_agent_outputs:
                continue

            logger.info(
                "Agent '%s' PR #%d complete for issue #%d — processing completion",
                current_agent,
                pr_number,
                task.issue_number,
            )

            # STEP 1: Merge child PR into the main branch FIRST (before posting Done!)
            # This ensures GitHub has time to process the merge before we try to assign the next agent.
            is_child_pr = finished_pr.get("is_child_pr", False)
            main_branch_info = get_issue_main_branch(task.issue_number)
            if is_child_pr and main_branch_info:
                merge_result = await _merge_child_pr_if_applicable(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    main_branch=main_branch_info["branch"],
                    main_pr_number=main_branch_info["pr_number"],
                    completed_agent=current_agent,
                )
                if merge_result:
                    logger.info(
                        "Merged child PR #%d before posting Done! for agent '%s' on issue #%d",
                        pr_number,
                        current_agent,
                        task.issue_number,
                    )
                    # Wait a moment for GitHub to fully process the merge
                    import asyncio

                    await asyncio.sleep(2)

            # STEP 2: Get PR details for posting .md outputs
            pr_details = await github_projects_service.get_pull_request(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                pr_number=pr_number,
            )

            head_ref = pr_details.get("head_ref", "") if pr_details else ""
            if not head_ref:
                logger.warning(
                    "Could not determine head ref for PR #%d, trying file list",
                    pr_number,
                )

            # Track the "main" branch for this issue (first PR's branch)
            # All subsequent agent branches will be created from and merged into this branch
            if head_ref and not get_issue_main_branch(task.issue_number):
                # Get head commit SHA for subsequent agent branching
                head_sha = ""
                if pr_details and pr_details.get("last_commit", {}).get("sha"):
                    head_sha = pr_details["last_commit"]["sha"]
                set_issue_main_branch(task.issue_number, head_ref, pr_number, head_sha)
                logger.info(
                    "Captured main branch '%s' (PR #%d, SHA: %s) for issue #%d",
                    head_ref,
                    pr_number,
                    head_sha[:8] if head_sha else "none",
                    task.issue_number,
                )

            # Get changed files from the PR
            pr_files = await github_projects_service.get_pr_changed_files(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                pr_number=pr_number,
            )

            # Find .md files that match the agent's expected outputs
            expected_files = AGENT_OUTPUT_FILES.get(current_agent, [])
            posted_count = 0

            for pr_file in pr_files:
                filename = pr_file.get("filename", "")
                basename = filename.rsplit("/", 1)[-1] if "/" in filename else filename

                if basename.lower() in [f.lower() for f in expected_files]:
                    # Fetch file content from the PR branch
                    ref = head_ref or "HEAD"
                    content = await github_projects_service.get_file_content_from_ref(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        path=filename,
                        ref=ref,
                    )

                    if content:
                        # Post file content as an issue comment
                        comment_body = (
                            f"**`{filename}`** (generated by `{current_agent}`)\n\n---\n\n{content}"
                        )
                        comment = await github_projects_service.create_issue_comment(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=task.issue_number,
                            body=comment_body,
                        )
                        if comment:
                            posted_count += 1
                            logger.info(
                                "Posted content of %s as comment on issue #%d",
                                filename,
                                task.issue_number,
                            )
                    else:
                        logger.warning(
                            "Could not fetch content of %s from ref %s for issue #%d",
                            filename,
                            ref,
                            task.issue_number,
                        )

            # Also post any other .md files changed in the PR
            for pr_file in pr_files:
                filename = pr_file.get("filename", "")
                basename = filename.rsplit("/", 1)[-1] if "/" in filename else filename

                if (
                    basename.lower().endswith(".md")
                    and basename.lower() not in [f.lower() for f in expected_files]
                    and pr_file.get("status") in ("added", "modified")
                ):
                    ref = head_ref or "HEAD"
                    content = await github_projects_service.get_file_content_from_ref(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        path=filename,
                        ref=ref,
                    )

                    if content:
                        comment_body = (
                            f"**`{filename}`** (generated by `{current_agent}`)\n\n---\n\n{content}"
                        )
                        await github_projects_service.create_issue_comment(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=task.issue_number,
                            body=comment_body,
                        )
                        posted_count += 1

            # Post the Done! marker
            done_comment = await github_projects_service.create_issue_comment(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                body=marker,
            )

            _posted_agent_outputs.add(cache_key)

            # Mark the child PR as claimed (merge already happened above)
            if is_child_pr:
                claimed_key = f"{task.issue_number}:{pr_number}:{current_agent}"
                _claimed_child_prs.add(claimed_key)
                logger.debug(
                    "Marked child PR #%d as claimed by agent '%s' on issue #%d",
                    pr_number,
                    current_agent,
                    task.issue_number,
                )

            if done_comment:
                logger.info(
                    "Posted '%s' marker on issue #%d (%d .md files posted)",
                    marker,
                    task.issue_number,
                    posted_count,
                )

                # Update the tracking table in the issue body: mark agent as ✅ Done
                await _update_issue_tracking(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    agent_name=current_agent,
                    new_state="done",
                )

                results.append(
                    {
                        "status": "success",
                        "issue_number": task.issue_number,
                        "agent_name": current_agent,
                        "pr_number": pr_number,
                        "files_posted": posted_count,
                        "action": "agent_outputs_posted",
                    }
                )
            else:
                logger.error(
                    "Failed to post Done! marker on issue #%d",
                    task.issue_number,
                )

            # Limit cache size
            if len(_posted_agent_outputs) > 500:
                to_remove = list(_posted_agent_outputs)[:250]
                for key in to_remove:
                    _posted_agent_outputs.discard(key)

            # Also limit claimed child PRs cache
            if len(_claimed_child_prs) > 500:
                to_remove = list(_claimed_child_prs)[:250]
                for key in to_remove:
                    _claimed_child_prs.discard(key)

    except Exception as e:
        logger.error("Error posting agent outputs from PRs: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = str(e)

    return results


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
            tasks = await github_projects_service.get_project_items(access_token, project_id)

        config = get_workflow_config(project_id)
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

        agents = get_agent_slugs(config, config.status_backlog)
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
            tasks = await github_projects_service.get_project_items(access_token, project_id)

        config = get_workflow_config(project_id)
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

        agents = get_agent_slugs(config, config.status_ready)
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


async def _merge_child_pr_if_applicable(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    main_branch: str,
    main_pr_number: int | None,
    completed_agent: str,
) -> dict[str, Any] | None:
    """
    Merge a child PR into the issue's main branch if applicable.

    Child PRs are those created by subsequent agents that target the first
    PR's branch (the "main branch" for the issue). When an agent completes,
    we check if their PR targets the main branch and merge it automatically.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        main_branch: The first PR's branch name (target for child PRs)
        main_pr_number: The first PR's number (to exclude from merging)
        completed_agent: Name of the agent that just completed

    Returns:
        Result dict if a PR was merged, None otherwise
    """
    try:
        # Get all linked PRs for this issue
        linked_prs = await github_projects_service.get_linked_pull_requests(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

        if not linked_prs:
            logger.debug(
                "No linked PRs found for issue #%d, nothing to merge",
                issue_number,
            )
            return None

        # Find a child PR that targets the main branch
        for pr in linked_prs:
            pr_number = pr.get("number")
            if pr_number is None:
                continue
            pr_number = int(pr_number)
            pr_state = pr.get("state", "").upper()
            pr_author = pr.get("author", "").lower()

            # Skip the main PR itself
            if pr_number == main_pr_number:
                continue

            # Skip non-Copilot PRs
            if "copilot" not in pr_author:
                continue

            # Only consider OPEN PRs
            if pr_state != "OPEN":
                logger.debug(
                    "PR #%d is %s (not OPEN), skipping",
                    pr_number,
                    pr_state,
                )
                continue

            # Get full PR details to check base_ref and get node ID
            pr_details = await github_projects_service.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=pr_number,
            )

            if not pr_details:
                logger.warning(
                    "Could not get details for PR #%d, skipping",
                    pr_number,
                )
                continue

            pr_base = pr_details.get("base_ref", "")  # The branch this PR targets

            # Check if this is a child PR for the current issue.
            # A child PR can target either:
            #   1. The main branch name (e.g., "copilot/implement-xxx")
            #   2. "main" — when created from a commit SHA
            # We accept both but need to re-target PRs that hit "main"
            # so they merge into the issue's main branch instead.
            is_child_of_main_branch = pr_base == main_branch
            is_child_of_default = pr_base == "main"

            if not is_child_of_main_branch and not is_child_of_default:
                logger.debug(
                    "PR #%d targets '%s' not main branch '%s' or 'main', skipping",
                    pr_number,
                    pr_base,
                    main_branch,
                )
                continue

            # If the child PR targets "main" instead of the issue's main branch,
            # update the PR base to target the correct branch before merging.
            if is_child_of_default and main_branch != "main":
                logger.info(
                    "Child PR #%d targets 'main' — updating base to '%s' before merge",
                    pr_number,
                    main_branch,
                )
                base_updated = await github_projects_service.update_pr_base(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    pr_number=pr_number,
                    base=main_branch,
                )
                if not base_updated:
                    logger.warning(
                        "Could not re-target PR #%d to '%s', skipping merge",
                        pr_number,
                        main_branch,
                    )
                    continue

            pr_node_id = pr_details.get("id")
            if not pr_node_id:
                logger.warning(
                    "No node ID for PR #%d, skipping merge",
                    pr_number,
                )
                continue

            # Check if PR is mergeable (not draft, no conflicts)
            is_draft = pr_details.get("is_draft", False)
            if is_draft:
                logger.info(
                    "PR #%d is still a draft, marking ready before merge",
                    pr_number,
                )
                await github_projects_service.mark_pr_ready_for_review(
                    access_token=access_token,
                    pr_node_id=pr_node_id,
                )
                _system_marked_ready_prs.add(pr_number)

            # Merge the child PR into the main branch
            logger.info(
                "Merging child PR #%d (by %s) into main branch '%s' for issue #%d",
                pr_number,
                completed_agent,
                main_branch,
                issue_number,
            )

            merge_result = await github_projects_service.merge_pull_request(
                access_token=access_token,
                pr_node_id=pr_node_id,
                pr_number=pr_number,
                commit_headline=f"Merge {completed_agent} changes into {main_branch}",
                merge_method="SQUASH",
            )

            if merge_result:
                # Get the child branch name to delete after merge
                child_branch = pr_details.get("head_ref", "")

                # Update the main branch HEAD SHA to the merge commit
                # so the next agent branches from the post-merge state
                merge_commit_sha = merge_result.get("merge_commit", "")
                if merge_commit_sha:
                    update_issue_main_branch_sha(issue_number, merge_commit_sha)

                logger.info(
                    "Successfully merged child PR #%d into '%s' (commit: %s)",
                    pr_number,
                    main_branch,
                    (
                        merge_result.get("merge_commit", "")[:8]
                        if merge_result.get("merge_commit")
                        else "N/A"
                    ),
                )

                # Mark this PR as claimed by the completed agent
                # This prevents subsequent agents from re-detecting it
                claimed_key = f"{issue_number}:{pr_number}:{completed_agent}"
                _claimed_child_prs.add(claimed_key)
                logger.debug(
                    "Marked merged child PR #%d as claimed by agent '%s' on issue #%d",
                    pr_number,
                    completed_agent,
                    issue_number,
                )

                # Clean up: delete the child branch after successful merge
                if child_branch:
                    logger.info(
                        "Cleaning up child branch '%s' after merge",
                        child_branch,
                    )
                    deleted = await github_projects_service.delete_branch(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        branch_name=child_branch,
                    )
                    if deleted:
                        logger.info(
                            "Deleted child branch '%s' for issue #%d",
                            child_branch,
                            issue_number,
                        )

                return {
                    "status": "merged",
                    "pr_number": pr_number,
                    "main_branch": main_branch,
                    "agent": completed_agent,
                    "merge_commit": merge_result.get("merge_commit"),
                    "branch_deleted": child_branch if child_branch else None,
                }
            else:
                logger.warning(
                    "Failed to merge child PR #%d into '%s'",
                    pr_number,
                    main_branch,
                )

        return None

    except Exception as e:
        logger.error(
            "Error merging child PR for issue #%d: %s",
            issue_number,
            e,
        )
        return None


async def _find_completed_child_pr(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    main_branch: str,
    main_pr_number: int,
    agent_name: str,
) -> dict | None:
    """
    Find a completed child PR created by the current agent.

    For subsequent agents in the pipeline, they create child PRs that target
    the main branch (the first PR's branch). This function finds such PRs
    and returns the PR details if completed.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        main_branch: The first PR's branch name (target for child PRs)
        main_pr_number: The first PR's number (to exclude from checking)
        agent_name: Name of the agent we're checking completion for

    Returns:
        Dict with PR details if a completed child PR exists, None otherwise
    """
    try:
        # Get all linked PRs for this issue
        linked_prs = await github_projects_service.get_linked_pull_requests(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

        if not linked_prs:
            logger.debug(
                "No linked PRs found for issue #%d when looking for child PR",
                issue_number,
            )
            return None

        # Look for a child PR that targets the main branch
        for pr in linked_prs:
            pr_number = pr.get("number")
            if pr_number is None:
                continue
            pr_number = int(pr_number)
            pr_state = pr.get("state", "").upper()
            pr_author = pr.get("author", "").lower()

            # Skip the main PR itself - we're looking for child PRs
            if pr_number == main_pr_number:
                continue

            # Skip non-Copilot PRs
            if "copilot" not in pr_author:
                continue

            # Consider OPEN or MERGED PRs - child PRs get merged after completion
            if pr_state not in ("OPEN", "MERGED"):
                continue

            # Get full PR details to check base_ref
            pr_details = await github_projects_service.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=pr_number,
            )

            if not pr_details:
                continue

            pr_base = pr_details.get("base_ref", "")

            # Check if this PR is a child PR for the current issue.
            # A child PR can target either:
            #   1. The main branch name (e.g., "copilot/implement-xxx") — when Copilot
            #      creates a branch from the main branch name
            #   2. "main" — when Copilot creates a branch from a commit SHA, it may
            #      target the default branch instead of the main PR's branch
            # We accept both, but exclude the main PR itself (already handled above).
            is_child_of_main_branch = pr_base == main_branch
            is_child_of_default = pr_base == "main"

            if not is_child_of_main_branch and not is_child_of_default:
                logger.debug(
                    "PR #%d targets '%s', not main branch '%s' or 'main' - not a child PR",
                    pr_number,
                    pr_base,
                    main_branch,
                )
                continue

            # Check if this PR has already been claimed by another agent
            # This prevents subsequent agents from re-using completed child PRs
            claimed_by_other = False
            for key in _claimed_child_prs:
                if key.startswith(f"{issue_number}:{pr_number}:"):
                    # Extract the agent that claimed this PR
                    claimed_agent = key.split(":")[-1]
                    if claimed_agent != agent_name:
                        logger.debug(
                            "Child PR #%d already claimed by agent '%s', "
                            "skipping for agent '%s' on issue #%d",
                            pr_number,
                            claimed_agent,
                            agent_name,
                            issue_number,
                        )
                        claimed_by_other = True
                        break
            if claimed_by_other:
                continue

            # If PR is MERGED, Copilot has definitely finished
            if pr_state == "MERGED":
                logger.info(
                    "Found MERGED child PR #%d targeting main branch '%s' for issue #%d",
                    pr_number,
                    main_branch,
                    issue_number,
                )
                return {
                    "number": pr_number,
                    "id": pr_details.get("id"),
                    "head_ref": pr_details.get("head_ref", ""),
                    "base_ref": pr_base,
                    "last_commit": pr_details.get("last_commit"),
                    "copilot_finished": True,
                    "is_child_pr": True,
                    "is_merged": True,
                }

            logger.info(
                "Found child PR #%d targeting main branch '%s' for issue #%d",
                pr_number,
                main_branch,
                issue_number,
            )

            # Check if Copilot has finished work on this child PR
            is_draft = pr_details.get("is_draft", True)

            # If not draft, Copilot has finished
            if not is_draft:
                logger.info(
                    "Child PR #%d is ready for review (not draft), agent '%s' completed",
                    pr_number,
                    agent_name,
                )
                return {
                    "number": pr_number,
                    "id": pr_details.get("id"),
                    "head_ref": pr_details.get("head_ref", ""),
                    "base_ref": pr_base,
                    "last_commit": pr_details.get("last_commit"),
                    "copilot_finished": True,
                    "is_child_pr": True,
                }

            # Check timeline events for completion signals
            timeline_events = await github_projects_service.get_pr_timeline_events(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=pr_number,  # Note: PR number for timeline events
            )

            copilot_finished = github_projects_service._check_copilot_finished_events(
                timeline_events
            )

            if copilot_finished:
                logger.info(
                    "Child PR #%d has copilot_finished events, agent '%s' completed",
                    pr_number,
                    agent_name,
                )
                return {
                    "number": pr_number,
                    "id": pr_details.get("id"),
                    "head_ref": pr_details.get("head_ref", ""),
                    "base_ref": pr_base,
                    "last_commit": pr_details.get("last_commit"),
                    "copilot_finished": True,
                    "is_child_pr": True,
                }

            logger.debug(
                "Child PR #%d exists but no completion signals yet for agent '%s'",
                pr_number,
                agent_name,
            )

        logger.debug(
            "No completed child PR found for issue #%d, agent '%s'",
            issue_number,
            agent_name,
        )
        return None

    except Exception as e:
        logger.error(
            "Error finding child PR for issue #%d: %s",
            issue_number,
            e,
        )
        return None


async def _check_child_pr_completion(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    main_branch: str,
    main_pr_number: int | None,
    agent_name: str,
) -> bool:
    """
    Check if the current agent has created and completed a child PR.

    For agents like speckit.implement, they create a child PR that targets
    the main branch. This function checks if such a PR exists and shows
    completion signals (copilot_work_finished or review_requested events).

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        main_branch: The first PR's branch name (target for child PRs)
        main_pr_number: The first PR's number (to exclude from checking)
        agent_name: Name of the agent we're checking completion for

    Returns:
        True if a completed child PR exists, False otherwise
    """
    try:
        # Get all linked PRs for this issue
        linked_prs = await github_projects_service.get_linked_pull_requests(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

        if not linked_prs:
            logger.debug(
                "No linked PRs found for issue #%d, agent '%s' hasn't created PR yet",
                issue_number,
                agent_name,
            )
            return False

        # Look for a child PR that targets the main branch
        for pr in linked_prs:
            pr_number = pr.get("number")
            if pr_number is None:
                continue
            pr_number = int(pr_number)
            pr_state = pr.get("state", "").upper()
            pr_author = pr.get("author", "").lower()

            # Skip the main PR itself - we're looking for child PRs
            if pr_number == main_pr_number:
                continue

            # Skip non-Copilot PRs
            if "copilot" not in pr_author:
                continue

            # Only consider OPEN PRs
            if pr_state != "OPEN":
                continue

            # Get full PR details to check base_ref
            pr_details = await github_projects_service.get_pull_request(
                access_token=access_token,
                owner=owner,
                repo=repo,
                pr_number=pr_number,
            )

            if not pr_details:
                continue

            pr_base = pr_details.get("base_ref", "")

            # Check if this PR targets the main branch (it's a child PR)
            # Accept PRs targeting either the main_branch name or "main"
            # (commit-SHA-based branching may create PRs targeting "main")
            if pr_base != main_branch and pr_base != "main":
                continue

            logger.info(
                "Found child PR #%d targeting '%s' (main branch '%s') for issue #%d",
                pr_number,
                pr_base,
                main_branch,
                issue_number,
            )

            # Check if Copilot has finished work on this child PR
            is_draft = pr_details.get("is_draft", True)

            # If not draft, Copilot has finished
            if not is_draft:
                logger.info(
                    "Child PR #%d is ready for review (not draft), agent '%s' completed",
                    pr_number,
                    agent_name,
                )
                return True

            # Check timeline events for completion signals
            timeline_events = await github_projects_service.get_pr_timeline_events(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=pr_number,
            )

            copilot_finished = github_projects_service._check_copilot_finished_events(
                timeline_events
            )

            if copilot_finished:
                logger.info(
                    "Child PR #%d has copilot_finished event, agent '%s' completed",
                    pr_number,
                    agent_name,
                )
                return True

            logger.debug(
                "Child PR #%d exists but no completion signals yet for agent '%s'",
                pr_number,
                agent_name,
            )
            return False  # Child PR exists but not complete yet

        logger.debug(
            "No child PR found targeting main branch '%s' (or 'main') for issue #%d, agent '%s' hasn't created PR yet",
            main_branch,
            issue_number,
            agent_name,
        )
        return False

    except Exception as e:
        logger.error(
            "Error checking child PR completion for issue #%d: %s",
            issue_number,
            e,
        )
        return False


async def _check_main_pr_completion(
    access_token: str,
    owner: str,
    repo: str,
    main_pr_number: int,
    issue_number: int,
    agent_name: str,
    pipeline_started_at: datetime | None = None,
    agent_assigned_sha: str = "",
) -> bool:
    """
    Check if a Copilot agent completed work directly on the main PR.

    Subsequent agents work on the existing PR branch (not creating a new PR).
    This function detects completion by checking multiple signals:
      1. If the main PR is no longer a draft (Copilot marks it ready when done)
      2. If the main PR has copilot_work_finished or review_requested events
         that occurred after the pipeline started
      3. If new commits exist on the branch (HEAD SHA changed since agent was
         assigned) AND Copilot is no longer assigned to the issue — indicating
         the agent pushed commits and finished its session

    Signal 3 is critical for subsequent agents that push to the existing branch.
    GitHub does not always fire copilot_work_finished timeline events when
    Copilot works on an already-open PR branch.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        main_pr_number: The main PR number to check
        issue_number: GitHub issue number (for logging)
        agent_name: Name of the agent we're checking completion for
        pipeline_started_at: When the pipeline was started (used to filter
            stale events from earlier agents)
        agent_assigned_sha: The HEAD SHA captured when the agent was assigned.
            If empty, commit-based detection is skipped.

    Returns:
        True if the main PR shows fresh completion signals, False otherwise
    """
    try:
        # Get main PR details
        pr_details = await github_projects_service.get_pull_request(
            access_token=access_token,
            owner=owner,
            repo=repo,
            pr_number=main_pr_number,
        )

        if not pr_details:
            logger.debug(
                "Could not get details for main PR #%d, issue #%d",
                main_pr_number,
                issue_number,
            )
            return False

        is_draft = pr_details.get("is_draft", True)
        pr_state = pr_details.get("state", "").upper()

        # Only consider OPEN PRs
        if pr_state != "OPEN":
            logger.debug(
                "Main PR #%d is not open (state=%s), not checking for completion",
                main_pr_number,
                pr_state,
            )
            return False

        # Signal 1: PR is no longer a draft
        # When Copilot finishes, it converts the PR from draft to ready.
        # Since the pipeline keeps the main PR as draft until the final
        # agent completes, a non-draft main PR means the agent finished.
        #
        # GUARD: If OUR system converted the PR from draft → ready (tracked
        # in _system_marked_ready_prs), ignore this signal — it was not
        # caused by Copilot completing its work.
        if not is_draft:
            if main_pr_number in _system_marked_ready_prs:
                logger.info(
                    "Main PR #%d is no longer a draft but was marked ready by "
                    "our system (not Copilot) — ignoring Signal 1 for agent '%s' "
                    "on issue #%d",
                    main_pr_number,
                    agent_name,
                    issue_number,
                )
            else:
                logger.info(
                    "Main PR #%d is no longer a draft — agent '%s' completed "
                    "directly on main PR for issue #%d",
                    main_pr_number,
                    agent_name,
                    issue_number,
                )
                return True

        # Signal 2: Check timeline events for fresh completion signals
        timeline_events = await github_projects_service.get_pr_timeline_events(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=main_pr_number,
        )

        # Filter events to only those after pipeline started (avoid stale
        # events from earlier agents like speckit.specify)
        if pipeline_started_at:
            fresh_events = _filter_events_after(timeline_events, pipeline_started_at)
            logger.debug(
                "Filtered %d/%d timeline events for main PR #%d (after pipeline start %s)",
                len(fresh_events),
                len(timeline_events),
                main_pr_number,
                pipeline_started_at.isoformat(),
            )
        else:
            # No pipeline start time — use all events (less safe but better
            # than missing completion entirely)
            fresh_events = timeline_events
            logger.debug(
                "No pipeline start time for issue #%d, using all %d timeline events",
                issue_number,
                len(timeline_events),
            )

        copilot_finished = github_projects_service._check_copilot_finished_events(fresh_events)

        if copilot_finished:
            logger.info(
                "Main PR #%d has fresh copilot_finished event after pipeline start — "
                "agent '%s' completed directly on main PR for issue #%d",
                main_pr_number,
                agent_name,
                issue_number,
            )
            return True

        # Signal 3: Commit-based detection + Copilot unassigned
        # When an agent works on the existing PR branch, it may not fire
        # timeline events. Instead, check if:
        #   (a) The branch HEAD SHA has changed since the agent was assigned
        #   (b) Copilot is no longer assigned to the issue (it self-unassigns
        #       when done)
        # Both conditions must be true to confirm completion.
        if agent_assigned_sha:
            current_sha = ""
            last_commit = pr_details.get("last_commit")
            if last_commit:
                current_sha = last_commit.get("sha", "")

            has_new_commits = current_sha and current_sha != agent_assigned_sha

            if has_new_commits:
                logger.info(
                    "Main PR #%d has new commits for agent '%s' on issue #%d "
                    "(assigned SHA: %s → current SHA: %s). Checking if Copilot "
                    "is still assigned...",
                    main_pr_number,
                    agent_name,
                    issue_number,
                    agent_assigned_sha[:8],
                    current_sha[:8],
                )

                # Check if Copilot is still assigned to the issue
                copilot_still_assigned = await github_projects_service.is_copilot_assigned_to_issue(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )

                if not copilot_still_assigned:
                    logger.info(
                        "Agent '%s' completed on main PR #%d for issue #%d — "
                        "new commits detected (SHA: %s → %s) and Copilot is "
                        "no longer assigned",
                        agent_name,
                        main_pr_number,
                        issue_number,
                        agent_assigned_sha[:8],
                        current_sha[:8],
                    )
                    return True
                else:
                    logger.debug(
                        "Main PR #%d has new commits but Copilot is still "
                        "assigned to issue #%d — agent '%s' still working",
                        main_pr_number,
                        issue_number,
                        agent_name,
                    )
            else:
                # SHA unchanged — but we should still check if Copilot has
                # unassigned itself (indicating the agent finished or failed
                # without pushing commits). This can happen if:
                #   - The agent completed with no code changes
                #   - The agent failed/timed out
                #   - The assignment didn't take effect
                copilot_still_assigned = await github_projects_service.is_copilot_assigned_to_issue(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
                )
                if not copilot_still_assigned:
                    logger.warning(
                        "Main PR #%d HEAD SHA unchanged (%s) but Copilot is no longer "
                        "assigned to issue #%d for agent '%s'. Agent may have failed "
                        "or completed without changes. Consider re-assigning.",
                        main_pr_number,
                        agent_assigned_sha[:8] if agent_assigned_sha else "none",
                        issue_number,
                        agent_name,
                    )
                    # Return True to trigger the completion flow, which will
                    # allow the polling loop to advance and potentially re-assign
                    # the agent. The Done! marker won't be posted without actual
                    # output files, but the pipeline can attempt recovery.
                    return True
                else:
                    logger.debug(
                        "Main PR #%d HEAD SHA unchanged (%s) for agent '%s', issue #%d "
                        "(Copilot still assigned — waiting)",
                        main_pr_number,
                        agent_assigned_sha[:8] if agent_assigned_sha else "none",
                        agent_name,
                        issue_number,
                    )
        else:
            # No assigned SHA available — also check Copilot assignment as
            # a standalone signal. If Copilot is no longer assigned AND the
            # issue timeline shows the agent was previously assigned, it means
            # the agent has finished (even if we can't confirm new commits).
            copilot_still_assigned = await github_projects_service.is_copilot_assigned_to_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if not copilot_still_assigned:
                # Double-check: make sure there are new commits since pipeline start
                # by checking if the committed_date of the last commit is after
                # pipeline_started_at
                last_commit = pr_details.get("last_commit")
                if last_commit and pipeline_started_at:
                    committed_date_str = last_commit.get("committed_date", "")
                    if committed_date_str:
                        try:
                            commit_time = datetime.fromisoformat(
                                committed_date_str.replace("Z", "+00:00")
                            )
                            cutoff = (
                                pipeline_started_at.replace(tzinfo=commit_time.tzinfo)
                                if pipeline_started_at.tzinfo is None
                                else pipeline_started_at
                            )
                            if commit_time > cutoff:
                                logger.info(
                                    "Agent '%s' completed on main PR #%d for issue #%d — "
                                    "Copilot unassigned and fresh commits exist (commit: %s)",
                                    agent_name,
                                    main_pr_number,
                                    issue_number,
                                    committed_date_str,
                                )
                                return True
                        except (ValueError, TypeError):
                            pass

        logger.debug(
            "Main PR #%d has no fresh completion signals for agent '%s', issue #%d",
            main_pr_number,
            agent_name,
            issue_number,
        )
        return False

    except Exception as e:
        logger.error(
            "Error checking main PR #%d completion for issue #%d: %s",
            main_pr_number,
            issue_number,
            e,
        )
        return False


def _filter_events_after(events: list[dict[str, Any]], cutoff: datetime) -> list[dict[str, Any]]:
    """
    Filter timeline events to only those occurring after a cutoff datetime.

    Args:
        events: List of timeline events from GitHub API
        cutoff: Only include events with created_at after this time

    Returns:
        Filtered list of events
    """
    filtered: list[dict[str, Any]] = []
    for event in events:
        created_at_str = event.get("created_at", "")
        if not created_at_str:
            # If no timestamp, include the event (conservative)
            filtered.append(event)
            continue
        try:
            # GitHub timestamps are ISO 8601 UTC (e.g., "2025-01-15T17:19:47Z")
            event_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            # Make cutoff timezone-aware if needed
            cutoff_aware = (
                cutoff.replace(tzinfo=event_time.tzinfo) if cutoff.tzinfo is None else cutoff
            )
            if event_time > cutoff_aware:
                filtered.append(event)
        except (ValueError, TypeError):
            # If timestamp can't be parsed, include the event (conservative)
            filtered.append(event)
    return filtered


async def _reconstruct_pipeline_state(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
    status: str,
    agents: list[str],
) -> PipelineState:
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
        issue_data = await github_projects_service.get_issue_with_comments(
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
            main_branch_info = get_issue_main_branch(issue_number)
            if main_branch_info:
                main_branch = main_branch_info.get("branch")
                main_pr_number = main_branch_info.get("pr_number")
                if main_branch and main_pr_number:
                    linked_prs = await github_projects_service.get_linked_pull_requests(
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
                            pr_details = await github_projects_service.get_pull_request(
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

    # Try to capture current HEAD SHA for commit-based completion detection
    reconstructed_sha = ""
    main_branch_info = get_issue_main_branch(issue_number)
    if main_branch_info and main_branch_info.get("pr_number"):
        try:
            pr_details = await github_projects_service.get_pull_request(
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

    pipeline = PipelineState(
        issue_number=issue_number,
        project_id=project_id,
        status=status,
        agents=list(agents),
        current_agent_index=len(completed),
        completed_agents=completed,
        started_at=datetime.utcnow(),
        agent_assigned_sha=reconstructed_sha,
    )
    set_pipeline_state(issue_number, pipeline)

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
    _pending_agent_assignments.discard(f"{issue_number}:{completed_agent}")

    logger.info(
        "Agent '%s' completed on issue #%d (%d/%d agents done)",
        completed_agent,
        issue_number,
        len(pipeline.completed_agents),
        len(pipeline.agents),
    )

    # NOTE: Child PR merge now happens in post_agent_outputs_from_pr BEFORE the Done! comment
    # is posted. This ensures GitHub has time to process the merge before we assign the next agent.

    # Send agent_completed WebSocket notification
    await connection_manager.broadcast_to_project(
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
            await connection_manager.broadcast_to_project(
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
    success = await github_projects_service.update_item_status_by_name(
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
            main_pr_details = await github_projects_service.get_pull_request(
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
                    mark_ready_success = await github_projects_service.mark_pr_ready_for_review(
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
                    review_requested = await github_projects_service.request_copilot_review(
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
    await connection_manager.broadcast_to_project(
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
            pt_success = await github_projects_service.update_item_status_by_name(
                access_token=access_token,
                project_id=project_id,
                item_id=item_id,
                status_name=next_actionable,
            )
            if pt_success:
                effective_status = next_actionable
                new_status_agents = get_agent_slugs(config, effective_status)

                await connection_manager.broadcast_to_project(
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
            existing_pr = await github_projects_service.find_existing_pr_for_issue(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
            )
            if existing_pr:
                # Fetch PR details to get commit SHA
                pr_details = await github_projects_service.get_pull_request(
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
            tasks = await github_projects_service.get_project_items(access_token, project_id)

        config = get_workflow_config(project_id)
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

            # Guard: skip issues managed by a pipeline for a different status.
            # When Copilot starts working on an issue, it naturally moves it to
            # "In Progress" even if the agent was assigned for "Backlog". This is
            # expected behaviour — do NOT fight it by restoring the old status, as
            # that re-triggers the agent (causing duplicate PRs).
            #
            # Instead, update the pipeline state to reflect the actual status so
            # the normal "In Progress" monitoring below picks it up.
            pipeline = get_pipeline_state(task.issue_number)
            if pipeline and not pipeline.is_complete:
                pipeline_status = pipeline.status.lower() if pipeline.status else ""
                if pipeline_status != in_progress_label:
                    logger.info(
                        "Issue #%d is in 'In Progress' but pipeline tracks '%s' "
                        "status (agent: %s, %d/%d done). Accepting status change — "
                        "Copilot moved the issue as part of its normal workflow.",
                        task.issue_number,
                        pipeline.status,
                        pipeline.current_agent or "none",
                        len(pipeline.completed_agents),
                        len(pipeline.agents),
                    )
                    # Update the pipeline to reflect actual status so subsequent
                    # polling iterations treat it as an "In Progress" pipeline.
                    pipeline.status = config.status_in_progress if config else "In Progress"
                    set_pipeline_state(task.issue_number, pipeline)
                    # Fall through to the normal In Progress handling below
                    # (don't 'continue')

            # Check for active pipeline (e.g., speckit.implement)
            if (
                pipeline
                and not pipeline.is_complete
                and pipeline.status.lower() == in_progress_label
            ):
                in_review_status = config.status_in_review if config else "In Review"

                # Check if current agent has completed (via Done! comment marker)
                current_agent = pipeline.current_agent
                if current_agent:
                    completed = await github_projects_service.check_agent_completion_comment(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=task.issue_number,
                        agent_name=current_agent,
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
                            from_status=config.status_in_progress if config else "In Progress",
                            to_status=in_review_status,
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


async def check_in_review_issues_for_copilot_review(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
) -> list[dict[str, Any]]:
    """
    Check all issues in "In Review" status to ensure Copilot has reviewed their PRs.

    If a PR has not been reviewed by Copilot yet, request a review.

    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner
        repo: Repository name

    Returns:
        List of results for each processed issue
    """
    results = []

    try:
        # Get all project items
        tasks = await github_projects_service.get_project_items(access_token, project_id)

        # Filter to "In Review" items with issue numbers
        in_review_tasks = [
            task
            for task in tasks
            if task.status and task.status.lower() == "in review" and task.issue_number is not None
        ]

        logger.debug(
            "Found %d issues in 'In Review' status",
            len(in_review_tasks),
        )

        for task in in_review_tasks:
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo

            if not task_owner or not task_repo:
                continue

            assert task.issue_number is not None  # filtered above
            result = await ensure_copilot_review_requested(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
                task_title=task.title,
            )

            if result:
                results.append(result)

    except Exception as e:
        logger.error("Error checking in-review issues for Copilot review: %s", e)

    return results


async def ensure_copilot_review_requested(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    task_title: str,
) -> dict[str, Any] | None:
    """
    Ensure a Copilot review has been requested for the PR linked to an issue.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number
        task_title: Task title for logging

    Returns:
        Result dict if review was requested, None otherwise
    """
    # Check for cache to avoid repeated API calls
    cache_key = cache_key_review_requested(issue_number)
    if cache_key in _processed_issue_prs:
        return None

    try:
        # Get linked PRs for this issue
        result = await github_projects_service.check_copilot_pr_completion(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

        if not result or not result.get("copilot_finished"):
            return None

        # Result has 'number' key from get_linked_pull_requests
        pr_number = result.get("pr_number") or result.get("number")
        pr_id = result.get("id")  # GraphQL node ID

        if not pr_number or not pr_id:
            logger.warning(
                "Missing PR number or ID for issue #%d: pr_number=%s, pr_id=%s",
                issue_number,
                pr_number,
                pr_id,
            )
            return None

        # Check if Copilot has already reviewed
        has_reviewed = await github_projects_service.has_copilot_reviewed_pr(
            access_token=access_token,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
        )

        if has_reviewed:
            # Mark as processed to avoid checking again
            _processed_issue_prs.add(cache_key)
            return None

        # Request Copilot review
        logger.info(
            "Requesting Copilot review for PR #%d (issue #%d: '%s')",
            pr_number,
            issue_number,
            task_title,
        )

        success = await github_projects_service.request_copilot_review(
            access_token=access_token,
            pr_node_id=pr_id,
            pr_number=pr_number,
        )

        if success:
            _processed_issue_prs.add(cache_key)
            return {
                "status": "success",
                "issue_number": issue_number,
                "pr_number": pr_number,
                "task_title": task_title,
                "action": "copilot_review_requested",
            }
        else:
            return {
                "status": "error",
                "issue_number": issue_number,
                "pr_number": pr_number,
                "error": "Failed to request Copilot review",
            }

    except Exception as e:
        logger.error(
            "Error ensuring Copilot review for issue #%d: %s",
            issue_number,
            e,
        )
        return None


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
        pipeline = get_pipeline_state(issue_number)
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
        finished_pr = await github_projects_service.check_copilot_pr_completion(
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
        cache_key = cache_key_issue_pr(issue_number, pr_number)
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

            success = await github_projects_service.mark_pr_ready_for_review(
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
        main_branch_info = get_issue_main_branch(issue_number)
        if main_branch_info:
            merge_result = await _merge_child_pr_if_applicable(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                main_branch=str(main_branch_info["branch"]),
                main_pr_number=main_branch_info["pr_number"],
                completed_agent="speckit.implement",
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

        # Add 2-second delay before status update (matching existing behavior)
        await asyncio.sleep(2)

        success = await github_projects_service.update_item_status_by_name(
            access_token=access_token,
            project_id=project_id,
            item_id=item_id,
            status_name="In Review",
        )

        if success:
            # Mark as processed to avoid duplicate updates
            _processed_issue_prs.add(cache_key)

            # Limit cache size
            if len(_processed_issue_prs) > 1000:
                # Remove oldest entries
                to_remove = list(_processed_issue_prs)[:500]
                for key in to_remove:
                    _processed_issue_prs.discard(key)

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

                review_requested = await github_projects_service.request_copilot_review(
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
            tasks = await github_projects_service.get_project_items(access_token, project_id)

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
                issue_data = await github_projects_service.get_issue_with_comments(
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
            if pending_key in _pending_agent_assignments:
                logger.debug(
                    "Recovery: issue #%d agent '%s' is in pending set — skipping",
                    issue_number,
                    agent_name,
                )
                continue

            # ── Check condition A: Copilot is assigned ────────────────────
            copilot_assigned = await github_projects_service.is_copilot_assigned_to_issue(
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

            linked_prs = await github_projects_service.get_linked_pull_requests(
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
                    pr_details = await github_projects_service.get_pull_request(
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
            already_done = await github_projects_service.check_agent_completion_comment(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=issue_number,
                agent_name=agent_name,
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
                _pending_agent_assignments.add(pending_key)

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
            all_tasks = await github_projects_service.get_project_items(access_token, project_id)

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
    global _polling_task
    _polling_state.is_running = False
    if _polling_task is not None and not _polling_task.done():
        _polling_task.cancel()
        _polling_task = None


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
        tasks = await github_projects_service.get_project_items(access_token, project_id)

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
