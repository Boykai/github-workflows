"""
Status-based issue checking for the Copilot polling service.
"""

import asyncio
import logging
from typing import Any

from src.constants import (
    cache_key_issue_pr,
    cache_key_review_requested,
)
from . import _deps
from src.services.workflow_orchestrator import (
    get_agent_slugs,
    get_issue_main_branch,
    get_pipeline_state,
    get_workflow_config,
    set_pipeline_state,
)

from .state import (
    _polling_state,
    _processed_issue_prs,
    _system_marked_ready_prs,
)
from .tracking import (
    _check_agent_done_on_sub_or_parent,
    _get_or_reconstruct_pipeline,
)
from .pipeline import (
    _advance_pipeline,
    _process_pipeline_completion,
)
from .pr_detection import _merge_child_pr_if_applicable

logger = logging.getLogger(__name__)


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
            tasks = await _deps.github_projects_service.get_project_items(access_token, project_id)

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
            tasks = await _deps.github_projects_service.get_project_items(access_token, project_id)

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
            tasks = await _deps.github_projects_service.get_project_items(access_token, project_id)

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
                    completed = await _check_agent_done_on_sub_or_parent(
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
        tasks = await _deps.github_projects_service.get_project_items(access_token, project_id)

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
        result = await _deps.github_projects_service.check_copilot_pr_completion(
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
        has_reviewed = await _deps.github_projects_service.has_copilot_reviewed_pr(
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

        success = await _deps.github_projects_service.request_copilot_review(
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
        finished_pr = await _deps.github_projects_service.check_copilot_pr_completion(
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

            success = await _deps.github_projects_service.mark_pr_ready_for_review(
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

        success = await _deps.github_projects_service.update_item_status_by_name(
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

                review_requested = await _deps.github_projects_service.request_copilot_review(
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
