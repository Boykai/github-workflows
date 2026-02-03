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

from src.config import get_settings
from src.services.github_projects import github_projects_service

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


async def check_in_progress_issues(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
) -> list[dict[str, Any]]:
    """
    Check all issues in "In Progress" status for completed Copilot PRs.
    
    Args:
        access_token: GitHub access token
        project_id: GitHub Project V2 node ID
        owner: Repository owner (fallback if not in task)
        repo: Repository name (fallback if not in task)
        
    Returns:
        List of results for each processed issue
    """
    results = []
    
    try:
        # Get all project items
        tasks = await github_projects_service.get_project_items(
            access_token, project_id
        )
        
        # Filter to "In Progress" items with issue numbers
        in_progress_tasks = [
            task for task in tasks 
            if task.status and task.status.lower() == "in progress"
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
        tasks = await github_projects_service.get_project_items(
            access_token, project_id
        )
        
        # Filter to "In Review" items with issue numbers
        in_review_tasks = [
            task for task in tasks 
            if task.status and task.status.lower() == "in review"
            and task.issue_number is not None
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
            
            # Step 1: Check "In Progress" issues for completed Copilot PRs
            results = await check_in_progress_issues(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
            )
            
            if results:
                logger.info(
                    "Poll #%d: Processed %d in-progress issues",
                    _polling_state.poll_count,
                    len(results),
                )
            
            # Step 2: Check "In Review" issues to ensure Copilot has reviewed their PRs
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
        "last_poll_time": _polling_state.last_poll_time.isoformat() if _polling_state.last_poll_time else None,
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
        tasks = await github_projects_service.get_project_items(
            access_token, project_id
        )
        
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
