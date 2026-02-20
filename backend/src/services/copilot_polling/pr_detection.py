"""
PR completion detection & merging for the Copilot polling service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from src.constants import (
    AGENT_OUTPUT_FILES,
    cache_key_agent_output,
)
from src.services.agent_tracking import (
    get_current_agent_from_tracking,
    parse_tracking_from_body,
)
from . import _deps
from src.services.workflow_orchestrator import (
    PipelineState,
    get_issue_main_branch,
    get_pipeline_state,
    set_issue_main_branch,
    set_pipeline_state,
    update_issue_main_branch_sha,
    get_workflow_config,
)

from .state import (
    _claimed_child_prs,
    _polling_state,
    _posted_agent_outputs,
    _system_marked_ready_prs,
)
from .tracking import (
    _check_agent_done_on_sub_or_parent,
    _filter_events_after,
    _get_tracking_state_from_issue,
    _reconstruct_sub_issue_mappings,
    _update_issue_tracking,
)

logger = logging.getLogger(__name__)


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
        linked_prs = await _deps.github_projects_service.get_linked_pull_requests(
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
            pr_details = await _deps.github_projects_service.get_pull_request(
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
                base_updated = await _deps.github_projects_service.update_pr_base(
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
                await _deps.github_projects_service.mark_pr_ready_for_review(
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

            merge_result = await _deps.github_projects_service.merge_pull_request(
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
                    deleted = await _deps.github_projects_service.delete_branch(
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
        linked_prs = await _deps.github_projects_service.get_linked_pull_requests(
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
            pr_details = await _deps.github_projects_service.get_pull_request(
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
            timeline_events = await _deps.github_projects_service.get_pr_timeline_events(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=pr_number,  # Note: PR number for timeline events
            )

            copilot_finished = _deps.github_projects_service._check_copilot_finished_events(
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
        linked_prs = await _deps.github_projects_service.get_linked_pull_requests(
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
            pr_details = await _deps.github_projects_service.get_pull_request(
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
            timeline_events = await _deps.github_projects_service.get_pr_timeline_events(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=pr_number,
            )

            copilot_finished = _deps.github_projects_service._check_copilot_finished_events(
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
        pr_details = await _deps.github_projects_service.get_pull_request(
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
        timeline_events = await _deps.github_projects_service.get_pr_timeline_events(
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

        copilot_finished = _deps.github_projects_service._check_copilot_finished_events(fresh_events)

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
                copilot_still_assigned = await _deps.github_projects_service.is_copilot_assigned_to_issue(
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
                copilot_still_assigned = await _deps.github_projects_service.is_copilot_assigned_to_issue(
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
            copilot_still_assigned = await _deps.github_projects_service.is_copilot_assigned_to_issue(
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
                        status_agents = [s.agent_name for s in steps if s.status == status_key]
                        # Determine completed agents by checking Done! comments
                        completed: list[str] = []
                        for agent in status_agents:
                            done_marker = f"{agent}: Done!"
                            if any(done_marker in c.get("body", "") for c in comments):
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

                        # Reconstruct sub-issue mappings from GitHub API
                        pipeline.agent_sub_issues = await _reconstruct_sub_issue_mappings(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=task.issue_number,
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
                                existing_pr = (
                                    await _deps.github_projects_service.find_existing_pr_for_issue(
                                        access_token=access_token,
                                        owner=task_owner,
                                        repo=task_repo,
                                        issue_number=task.issue_number,
                                    )
                                )
                                if existing_pr:
                                    pr_det = await _deps.github_projects_service.get_pull_request(
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
                                        "Reconstructed main branch '%s' (PR #%d) for issue #%d",
                                        existing_pr["head_ref"],
                                        existing_pr["number"],
                                        task.issue_number,
                                    )
                            except Exception as e:
                                logger.debug(
                                    "Could not reconstruct main branch for issue #%d: %s",
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
            already_done = await _check_agent_done_on_sub_or_parent(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                parent_issue_number=task.issue_number,
                agent_name=current_agent,
                pipeline=pipeline,
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
                finished_pr = await _deps.github_projects_service.check_copilot_pr_completion(
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
                        pr_details = await _deps.github_projects_service.get_pull_request(
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
                    await asyncio.sleep(2)

            # STEP 2: Get PR details for posting .md outputs
            pr_details = await _deps.github_projects_service.get_pull_request(
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

                # Link the first PR to the GitHub Issue so it appears in the
                # Development sidebar and auto-closes the issue on merge.
                try:
                    await _deps.github_projects_service.link_pull_request_to_issue(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        pr_number=pr_number,
                        issue_number=task.issue_number,
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to link PR #%d to issue #%d: %s",
                        pr_number,
                        task.issue_number,
                        e,
                    )

            # Get changed files from the PR
            pr_files = await _deps.github_projects_service.get_pr_changed_files(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                pr_number=pr_number,
            )

            # Find .md files that match the agent's expected outputs
            expected_files = AGENT_OUTPUT_FILES.get(current_agent, [])
            posted_count = 0

            # Determine which issue to post comments on.
            # If the agent has a sub-issue, post there; otherwise fall back to the parent issue.
            comment_issue_number = task.issue_number
            if pipeline and pipeline.agent_sub_issues:
                sub_info = pipeline.agent_sub_issues.get(current_agent)
                if sub_info and sub_info.get("number"):
                    comment_issue_number = sub_info["number"]
                    logger.info(
                        "Posting agent '%s' outputs on sub-issue #%d (parent #%d)",
                        current_agent,
                        comment_issue_number,
                        task.issue_number,
                    )

            for pr_file in pr_files:
                filename = pr_file.get("filename", "")
                basename = filename.rsplit("/", 1)[-1] if "/" in filename else filename

                if basename.lower() in [f.lower() for f in expected_files]:
                    # Fetch file content from the PR branch
                    ref = head_ref or "HEAD"
                    content = await _deps.github_projects_service.get_file_content_from_ref(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        path=filename,
                        ref=ref,
                    )

                    if content:
                        # Post file content as a comment on the sub-issue (or parent)
                        comment_body = (
                            f"**`{filename}`** (generated by `{current_agent}`)\n\n---\n\n{content}"
                        )
                        comment = await _deps.github_projects_service.create_issue_comment(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=comment_issue_number,
                            body=comment_body,
                        )
                        if comment:
                            posted_count += 1
                            logger.info(
                                "Posted content of %s as comment on issue #%d",
                                filename,
                                comment_issue_number,
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
                    content = await _deps.github_projects_service.get_file_content_from_ref(
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
                        await _deps.github_projects_service.create_issue_comment(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=comment_issue_number,
                            body=comment_body,
                        )
                        posted_count += 1

            # Post the Done! marker on the SUB-ISSUE (same issue that
            # received the markdown file comments above).
            done_issue_number = comment_issue_number  # already resolved above
            done_comment = await _deps.github_projects_service.create_issue_comment(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=done_issue_number,
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
                    "Posted '%s' marker on issue #%d (%d .md files posted on #%d)",
                    marker,
                    done_issue_number,
                    posted_count,
                    comment_issue_number,
                )

                # Close the sub-issue as completed now that the agent is done.
                # Only close when messaging a real sub-issue (not the parent).
                if done_issue_number != task.issue_number:
                    closed = await _deps.github_projects_service.update_issue_state(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=done_issue_number,
                        state="closed",
                        state_reason="completed",
                    )
                    if closed:
                        logger.info(
                            "Closed sub-issue #%d as completed (agent '%s' done)",
                            done_issue_number,
                            current_agent,
                        )
                    else:
                        logger.warning(
                            "Failed to close sub-issue #%d after agent '%s' completion",
                            done_issue_number,
                            current_agent,
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
