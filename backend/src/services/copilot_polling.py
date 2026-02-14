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

from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.services.workflow_orchestrator import (
    PipelineState,
    WorkflowContext,
    WorkflowState,
    get_issue_main_branch,
    get_pipeline_state,
    get_workflow_config,
    get_workflow_orchestrator,
    remove_pipeline_state,
    set_issue_main_branch,
    set_pipeline_state,
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

# Track issues we've already processed to avoid duplicate updates
_processed_issue_prs: set[str] = set()  # "issue_number:pr_number"

# Track issues where we've already posted agent outputs to avoid duplicates
_posted_agent_outputs: set[str] = set()  # "issue_number:agent_name:pr_number"

# Map agent names to the specific .md files they produce
AGENT_OUTPUT_FILES: dict[str, list[str]] = {
    "speckit.specify": ["spec.md"],
    "speckit.plan": ["plan.md"],
    "speckit.tasks": ["tasks.md"],
}


async def post_agent_outputs_from_pr(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list[dict[str, Any]]:
    """
    For all issues with active pipelines, check if the current agent's PR work
    is complete. If so, fetch .md files from the PR, post them as issue comments,
    and post the ``<agent-name>: Done!`` marker.

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

            pipeline = get_pipeline_state(task.issue_number)
            if not pipeline or pipeline.is_complete:
                continue

            current_agent = pipeline.current_agent
            if not current_agent:
                continue

            # Only process agents that produce .md files (not speckit.implement)
            if current_agent not in AGENT_OUTPUT_FILES:
                continue

            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo
            if not task_owner or not task_repo:
                continue

            # Check if we already posted outputs for this agent on this issue
            cache_key_prefix = f"{task.issue_number}:{current_agent}"
            if any(k.startswith(cache_key_prefix) for k in _posted_agent_outputs):
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

            # Check for a completed PR linked to this issue
            finished_pr = await github_projects_service.check_copilot_pr_completion(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=task.issue_number,
            )

            if not finished_pr:
                continue

            pr_number = finished_pr.get("number")
            if not pr_number:
                continue

            cache_key = f"{task.issue_number}:{current_agent}:{pr_number}"
            if cache_key in _posted_agent_outputs:
                continue

            logger.info(
                "Agent '%s' PR #%d complete for issue #%d — posting .md outputs as comments",
                current_agent,
                pr_number,
                task.issue_number,
            )

            # Get PR details for the head branch ref
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
                set_issue_main_branch(task.issue_number, head_ref, pr_number)
                logger.info(
                    "Captured main branch '%s' (PR #%d) for issue #%d",
                    head_ref,
                    pr_number,
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
                            f"**`{filename}`** (generated by `{current_agent}`)\n\n"
                            f"---\n\n{content}"
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
                            f"**`{filename}`** (generated by `{current_agent}`)\n\n"
                            f"---\n\n{content}"
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

            if done_comment:
                logger.info(
                    "Posted '%s' marker on issue #%d (%d .md files posted)",
                    marker,
                    task.issue_number,
                    posted_count,
                )
                results.append({
                    "status": "success",
                    "issue_number": task.issue_number,
                    "agent_name": current_agent,
                    "pr_number": pr_number,
                    "files_posted": posted_count,
                    "action": "agent_outputs_posted",
                })
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

        agents = config.agent_mappings.get(config.status_backlog, [])
        if not agents:
            return results

        for task in backlog_tasks:
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo
            if not task_owner or not task_repo:
                continue

            # Get or create pipeline state
            pipeline = get_pipeline_state(task.issue_number)
            if pipeline is None:
                # Reconstruct from comments
                pipeline = await _reconstruct_pipeline_state(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    project_id=project_id,
                    status=config.status_backlog,
                    agents=agents,
                )

            if pipeline.is_complete:
                # All Backlog agents done → transition to Ready
                result = await _transition_after_pipeline_complete(
                    access_token=access_token,
                    project_id=project_id,
                    item_id=task.github_item_id,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    issue_node_id=task.github_content_id,
                    from_status=config.status_backlog,
                    to_status=config.status_ready,
                    task_title=task.title,
                )
                if result:
                    results.append(result)
                continue

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
                    result = await _advance_pipeline(
                        access_token=access_token,
                        project_id=project_id,
                        item_id=task.github_item_id,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=task.issue_number,
                        issue_node_id=task.github_content_id,
                        pipeline=pipeline,
                        from_status=config.status_backlog,
                        to_status=config.status_ready,
                        task_title=task.title,
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
            if task.status
            and task.status.lower() == status_ready
            and task.issue_number is not None
        ]

        if not ready_tasks:
            return results

        logger.debug("Found %d issues in '%s' status", len(ready_tasks), config.status_ready)

        agents = config.agent_mappings.get(config.status_ready, [])
        if not agents:
            return results

        for task in ready_tasks:
            task_owner = task.repository_owner or owner
            task_repo = task.repository_name or repo
            if not task_owner or not task_repo:
                continue

            # Get or create pipeline state
            pipeline = get_pipeline_state(task.issue_number)
            if pipeline is None or pipeline.status != config.status_ready:
                # Reconstruct from comments
                pipeline = await _reconstruct_pipeline_state(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    project_id=project_id,
                    status=config.status_ready,
                    agents=agents,
                )

            if pipeline.is_complete:
                # All Ready agents done → transition to In Progress
                result = await _transition_after_pipeline_complete(
                    access_token=access_token,
                    project_id=project_id,
                    item_id=task.github_item_id,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    issue_node_id=task.github_content_id,
                    from_status=config.status_ready,
                    to_status=config.status_in_progress,
                    task_title=task.title,
                )
                if result:
                    results.append(result)
                continue

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
                    result = await _advance_pipeline(
                        access_token=access_token,
                        project_id=project_id,
                        item_id=task.github_item_id,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=task.issue_number,
                        issue_node_id=task.github_content_id,
                        pipeline=pipeline,
                        from_status=config.status_ready,
                        to_status=config.status_in_progress,
                        task_title=task.title,
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

            # Skip PRs not targeting the main branch
            if pr_base != main_branch:
                logger.debug(
                    "PR #%d targets '%s' not main branch '%s', skipping",
                    pr_number,
                    pr_base,
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

                logger.info(
                    "Successfully merged child PR #%d into '%s' (commit: %s)",
                    pr_number,
                    main_branch,
                    merge_result.get("merge_commit", "")[:8] if merge_result.get("merge_commit") else "N/A",
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

    except Exception as e:
        logger.warning(
            "Could not reconstruct pipeline state for issue #%d: %s", issue_number, e
        )

    pipeline = PipelineState(
        issue_number=issue_number,
        project_id=project_id,
        status=status,
        agents=list(agents),
        current_agent_index=len(completed),
        completed_agents=completed,
        started_at=datetime.utcnow(),
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
    pipeline.completed_agents.append(completed_agent)
    pipeline.current_agent_index += 1

    logger.info(
        "Agent '%s' completed on issue #%d (%d/%d agents done)",
        completed_agent,
        issue_number,
        len(pipeline.completed_agents),
        len(pipeline.agents),
    )

    # Merge child PR into the main branch if applicable
    # Child PRs are those that target the issue's main branch (first PR's branch), not `main`
    main_branch_info = get_issue_main_branch(issue_number)
    if main_branch_info:
        await _merge_child_pr_if_applicable(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            main_branch=main_branch_info["branch"],
            main_pr_number=main_branch_info.get("pr_number"),
            completed_agent=completed_agent,
        )

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

        logger.info(
            "Assigning next agent '%s' to issue #%d", next_agent, issue_number
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
    new_status_agents = config.agent_mappings.get(to_status, []) if config else []

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
                set_issue_main_branch(
                    issue_number,
                    existing_pr["head_ref"],
                    existing_pr["number"],
                )
                logger.info(
                    "Captured main branch '%s' (PR #%d) for issue #%d before assigning %s",
                    existing_pr["head_ref"],
                    existing_pr["number"],
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
        await orchestrator.assign_agent_for_status(ctx, to_status, agent_index=0)

    return {
        "status": "success",
        "issue_number": issue_number,
        "task_title": task_title,
        "action": "status_transitioned",
        "from_status": from_status,
        "to_status": to_status,
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
            # External GitHub automation (e.g., linking a PR) can move issues
            # to "In Progress" before the agent pipeline is ready.
            pipeline = get_pipeline_state(task.issue_number)
            if pipeline and not pipeline.is_complete:
                pipeline_status = pipeline.status.lower() if pipeline.status else ""
                if pipeline_status != in_progress_label:
                    logger.warning(
                        "Issue #%d is in 'In Progress' but has active pipeline for "
                        "'%s' status (agent: %s, %d/%d done). Skipping — likely "
                        "moved by external automation. Attempting to restore status.",
                        task.issue_number,
                        pipeline.status,
                        pipeline.current_agent or "none",
                        len(pipeline.completed_agents),
                        len(pipeline.agents),
                    )
                    # Try to move the issue back to its pipeline status
                    try:
                        restored = await github_projects_service.update_item_status_by_name(
                            access_token=access_token,
                            project_id=project_id,
                            item_id=task.github_item_id,
                            status_name=pipeline.status,
                        )
                        if restored:
                            logger.info(
                                "Restored issue #%d back to '%s' status",
                                task.issue_number,
                                pipeline.status,
                            )
                        else:
                            logger.warning(
                                "Failed to restore issue #%d to '%s' status",
                                task.issue_number,
                                pipeline.status,
                            )
                    except Exception as e:
                        logger.warning(
                            "Error restoring issue #%d status: %s",
                            task.issue_number,
                            e,
                        )
                    continue

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
    cache_key = f"copilot_review_requested:{issue_number}"
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
        # Check if Copilot has finished work on the PR
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
        pr_id = finished_pr.get("id")
        is_draft = finished_pr.get("is_draft", False)
        check_status = finished_pr.get("check_status", "unknown")

        # Check if we've already processed this issue+PR combination
        cache_key = f"{issue_number}:{pr_number}"
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

        # Step 1.5: Merge child PR into main branch if applicable
        # This handles cases where speckit.implement created a child branch targeting the
        # issue's main branch (first PR's branch). We merge it before transitioning to In Review.
        main_branch_info = get_issue_main_branch(issue_number)
        if main_branch_info:
            merge_result = await _merge_child_pr_if_applicable(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                main_branch=str(main_branch_info["branch"]),
                main_pr_number=main_branch_info.get("pr_number"),
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

    while _polling_state.is_running:
        try:
            _polling_state.last_poll_time = datetime.utcnow()
            _polling_state.poll_count += 1

            logger.debug("Polling for Copilot PR completions (poll #%d)", _polling_state.poll_count)

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

        except Exception as e:
            logger.error("Error in polling loop: %s", e)
            _polling_state.errors_count += 1
            _polling_state.last_error = str(e)

        # Wait for next poll
        await asyncio.sleep(interval_seconds)

    logger.info("Copilot PR completion polling stopped")


def stop_polling() -> None:
    """Stop the background polling loop."""
    _polling_state.is_running = False


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
