"""PR completion detection — merge, child PR, main PR, and review logic."""

import logging
from datetime import datetime
from typing import Any

import src.services.copilot_polling as _cp

from .state import (
    _claimed_child_prs,
    _processed_issue_prs,
    _system_marked_ready_prs,
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
    pipeline: "object | None" = None,
) -> dict[str, Any] | None:
    """
    Merge a child PR into the issue's main branch if applicable.

    Child PRs are those created by subsequent agents that target the first
    PR's branch (the "main branch" for the issue). When an agent completes,
    we check if their PR targets the main branch and merge it automatically.

    Searches both the parent issue AND the agent's sub-issue for linked PRs,
    so PRs created via sub-issue assignments are still discovered.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number (parent)
        main_branch: The first PR's branch name (target for child PRs)
        main_pr_number: The first PR's number (to exclude from merging)
        completed_agent: Name of the agent that just completed
        pipeline: Optional pipeline state for sub-issue lookup

    Returns:
        Result dict if a PR was merged, None otherwise
    """
    try:
        # Get all linked PRs for this issue (including sub-issues)
        linked_prs = await _cp._get_linked_prs_including_sub_issues(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=issue_number,
            pipeline=pipeline,
            current_agent=completed_agent,
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
            if not _cp.github_projects_service.is_copilot_author(pr_author):
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
            pr_details = await _cp.github_projects_service.get_pull_request(
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
                base_updated = await _cp.github_projects_service.update_pr_base(
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
                await _cp.github_projects_service.mark_pr_ready_for_review(
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

            merge_result = await _cp.github_projects_service.merge_pull_request(
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
                    _cp.update_issue_main_branch_sha(issue_number, merge_commit_sha)

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
                    deleted = await _cp.github_projects_service.delete_branch(
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
    pipeline: "object | None" = None,
) -> dict | None:
    """
    Find a completed child PR created by the current agent.

    For subsequent agents in the pipeline, they create child PRs that target
    the main branch (the first PR's branch). This function finds such PRs
    and returns the PR details if completed.

    Searches both the parent issue AND the agent's sub-issue for linked PRs,
    so PRs created via sub-issue assignments are still discovered.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: GitHub issue number (parent)
        main_branch: The first PR's branch name (target for child PRs)
        main_pr_number: The first PR's number (to exclude from checking)
        agent_name: Name of the agent we're checking completion for
        pipeline: Optional pipeline state for sub-issue lookup

    Returns:
        Dict with PR details if a completed child PR exists, None otherwise
    """
    try:
        # Get all linked PRs for this issue (including sub-issues)
        linked_prs = await _cp._get_linked_prs_including_sub_issues(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=issue_number,
            pipeline=pipeline,
            current_agent=agent_name,
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
            if not _cp.github_projects_service.is_copilot_author(pr_author):
                continue

            # Consider OPEN or MERGED PRs - child PRs get merged after completion
            if pr_state not in ("OPEN", "MERGED"):
                continue

            # Get full PR details to check base_ref
            pr_details = await _cp.github_projects_service.get_pull_request(
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
            timeline_events = await _cp.github_projects_service.get_pr_timeline_events(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=pr_number,  # Note: PR number for timeline events
            )

            copilot_finished = _cp.github_projects_service.check_copilot_finished_events(
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
    pipeline: "object | None" = None,
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
        issue_number: GitHub issue number (parent)
        main_branch: The first PR's branch name (target for child PRs)
        main_pr_number: The first PR's number (to exclude from checking)
        agent_name: Name of the agent we're checking completion for
        pipeline: Optional pipeline state for sub-issue lookup

    Returns:
        True if a completed child PR exists, False otherwise
    """
    try:
        # Get all linked PRs for this issue (including sub-issues)
        linked_prs = await _cp._get_linked_prs_including_sub_issues(
            access_token=access_token,
            owner=owner,
            repo=repo,
            parent_issue_number=issue_number,
            pipeline=pipeline,
            current_agent=agent_name,
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
            if not _cp.github_projects_service.is_copilot_author(pr_author):
                continue

            # Only consider OPEN PRs
            if pr_state != "OPEN":
                continue

            # Get full PR details to check base_ref
            pr_details = await _cp.github_projects_service.get_pull_request(
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
            timeline_events = await _cp.github_projects_service.get_pr_timeline_events(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=pr_number,
            )

            copilot_finished = _cp.github_projects_service.check_copilot_finished_events(
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
        pr_details = await _cp.github_projects_service.get_pull_request(
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
        timeline_events = await _cp.github_projects_service.get_pr_timeline_events(
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

        copilot_finished = _cp.github_projects_service.check_copilot_finished_events(fresh_events)

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
                copilot_still_assigned = (
                    await _cp.github_projects_service.is_copilot_assigned_to_issue(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                    )
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
                copilot_still_assigned = (
                    await _cp.github_projects_service.is_copilot_assigned_to_issue(
                        access_token=access_token,
                        owner=owner,
                        repo=repo,
                        issue_number=issue_number,
                    )
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
                    # Return False — without a SHA change we cannot confirm the
                    # agent actually committed code.  Advancing the pipeline here
                    # would be a false-positive (FR-007).  The operator should
                    # re-assign the agent or manually advance the pipeline.
                    return False
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
            copilot_still_assigned = await _cp.github_projects_service.is_copilot_assigned_to_issue(
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
        tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

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
    cache_key = _cp.cache_key_review_requested(issue_number)
    if cache_key in _processed_issue_prs:
        return None

    try:
        # Get linked PRs for this issue
        result = await _cp.github_projects_service.check_copilot_pr_completion(
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
        has_reviewed = await _cp.github_projects_service.has_copilot_reviewed_pr(
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

        success = await _cp.github_projects_service.request_copilot_review(
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
        tasks = await _cp.github_projects_service.get_project_items(access_token, project_id)

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

        result = await _cp.process_in_progress_issue(
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
