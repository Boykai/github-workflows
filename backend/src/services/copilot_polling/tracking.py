"""
Issue tracking & pipeline state helpers for the Copilot polling service.
"""

import logging
from datetime import datetime
from typing import Any

from src.services.agent_tracking import (
    mark_agent_active,
    mark_agent_done,
)
from . import _deps
from src.services.workflow_orchestrator import (
    PipelineState,
    get_issue_main_branch,
    get_pipeline_state,
    set_pipeline_state,
)

from .state import _claimed_child_prs

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Issue Body Tracking Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _get_sub_issue_number(
    pipeline: "PipelineState | None",
    agent_name: str,
    parent_issue_number: int,
) -> int:
    """Return the sub-issue number for an agent, falling back to the parent.

    All agent comments (markdown files AND Done! markers) should be posted on
    the sub-issue when one exists.
    """
    if pipeline and pipeline.agent_sub_issues:
        sub_info = pipeline.agent_sub_issues.get(agent_name)
        if sub_info and sub_info.get("number"):
            return sub_info["number"]
    return parent_issue_number


async def _check_agent_done_on_sub_or_parent(
    access_token: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    agent_name: str,
    pipeline: "PipelineState | None" = None,
) -> bool:
    """Check if an agent's Done! marker exists on its sub-issue (preferred) or parent.

    Checks the sub-issue first (new behavior). Falls back to the parent issue
    for backward compatibility with issues created before the sub-issue-only
    comment policy.
    """
    sub_number = _get_sub_issue_number(pipeline, agent_name, parent_issue_number)

    # Check sub-issue first (if different from parent)
    if sub_number != parent_issue_number:
        done = await _deps.github_projects_service.check_agent_completion_comment(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=sub_number,
            agent_name=agent_name,
        )
        if done:
            return True

    # Fall back to parent issue for backward compat
    return await _deps.github_projects_service.check_agent_completion_comment(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=parent_issue_number,
        agent_name=agent_name,
    )


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
        issue_data = await _deps.github_projects_service.get_issue_with_comments(
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

        success = await _deps.github_projects_service.update_issue_body(
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
    issue_data = await _deps.github_projects_service.get_issue_with_comments(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )
    return issue_data.get("body", ""), issue_data.get("comments", [])


async def _reconstruct_sub_issue_mappings(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
) -> dict[str, dict]:
    """Fetch sub-issues from GitHub and build ``agent_name → sub-issue`` mapping.

    Sub-issue titles follow the pattern ``[agent-name] Title``.  This parses
    the agent name from the bracketed prefix.
    """
    try:
        raw_subs = await _deps.github_projects_service.get_sub_issues(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )
        mappings: dict[str, dict] = {}
        for si in raw_subs:
            si_title = si.get("title", "")
            if si_title.startswith("[") and "]" in si_title:
                si_agent = si_title[1 : si_title.index("]")]
                mappings[si_agent] = {
                    "number": si.get("number"),
                    "node_id": si.get("node_id", ""),
                    "url": si.get("html_url", ""),
                }
        if mappings:
            logger.info(
                "Reconstructed %d sub-issue mappings for issue #%d",
                len(mappings),
                issue_number,
            )
        return mappings
    except Exception as e:
        logger.debug(
            "Could not reconstruct sub-issue mappings for issue #%d: %s",
            issue_number,
            e,
        )
        return {}


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
        issue_data = await _deps.github_projects_service.get_issue_with_comments(
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
                    linked_prs = await _deps.github_projects_service.get_linked_pull_requests(
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
                            pr_details = await _deps.github_projects_service.get_pull_request(
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
            pr_details = await _deps.github_projects_service.get_pull_request(
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

    # Reconstruct sub-issue mappings from GitHub API
    pipeline.agent_sub_issues = await _reconstruct_sub_issue_mappings(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
    )

    set_pipeline_state(issue_number, pipeline)

    logger.info(
        "Reconstructed pipeline state for issue #%d: %d/%d agents completed",
        issue_number,
        len(completed),
        len(agents),
    )

    return pipeline


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
