"""Agent output extraction and posting from completed PRs."""

import asyncio
import logging
from typing import Any

import src.services.copilot_polling as _cp
from src.utils import utcnow

from .state import (
    _claimed_child_prs,
    _polling_state,
    _posted_agent_outputs,
)

logger = logging.getLogger(__name__)


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
    as comments on the **sub-issue**, and post the ``<agent-name>: Done!``
    marker on the **parent issue** only.

    Comment routing policy:
      - ``<agent>: Done!`` marker → parent (main) issue ONLY
      - Markdown file comments     → sub-issue ONLY (skipped if no sub-issue)
      - All other agent outputs    → sub-issue ONLY

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
        config = await _cp.get_workflow_config(project_id)
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

            pipeline = _cp.get_pipeline_state(task.issue_number)

            # If in-memory pipeline state is missing (e.g., after container
            # restart), reconstruct from the durable tracking table in the
            # issue body.  This ensures agent completions are detected and
            # Done! markers posted even when volatile state has been lost.
            # Without this, Step 0 skips the issue entirely, the Done!
            # marker is never posted, and recovery (Step 5) mistakenly
            # re-assigns the same agent — causing duplicate PRs.
            if pipeline is None:
                try:
                    body, comments = await _cp._get_tracking_state_from_issue(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=task.issue_number,
                    )
                    steps = _cp.parse_tracking_from_body(body)
                    active_step = _cp.get_current_agent_from_tracking(body)
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

                        pipeline = _cp.PipelineState(
                            issue_number=task.issue_number,
                            project_id=project_id,
                            status=status_key,
                            agents=status_agents,
                            current_agent_index=len(completed),
                            completed_agents=completed,
                            started_at=utcnow(),
                        )

                        # Reconstruct sub-issue mappings from GitHub API
                        pipeline.agent_sub_issues = await _cp._reconstruct_sub_issue_mappings(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            issue_number=task.issue_number,
                        )

                        _cp.set_pipeline_state(task.issue_number, pipeline)
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
                        if not _cp.get_issue_main_branch(task.issue_number):
                            try:
                                existing_pr = (
                                    await _cp.github_projects_service.find_existing_pr_for_issue(
                                        access_token=access_token,
                                        owner=task_owner,
                                        repo=task_repo,
                                        issue_number=task.issue_number,
                                    )
                                )
                                if existing_pr:
                                    pr_det = await _cp.github_projects_service.get_pull_request(
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
                                    _cp.set_issue_main_branch(
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

                        # Claim merged child PRs for completed agents to prevent
                        # misattribution.  After a container restart _claimed_child_prs
                        # is empty.  Without this, _find_completed_child_pr can return
                        # a MERGED child PR from a completed agent as if it belongs to
                        # the current (not-yet-completed) agent — posting a false Done!
                        # marker and skipping the current agent entirely.
                        main_branch_recon = _cp.get_issue_main_branch(task.issue_number)
                        if main_branch_recon and completed:
                            try:
                                linked_prs_recon = (
                                    await _cp.github_projects_service.get_linked_pull_requests(
                                        access_token=access_token,
                                        owner=task_owner,
                                        repo=task_repo,
                                        issue_number=task.issue_number,
                                    )
                                )
                                main_pr_num_recon = main_branch_recon.get("pr_number")
                                for pr_recon in linked_prs_recon or []:
                                    pr_num_r = pr_recon.get("number")
                                    pr_state_r = (pr_recon.get("state") or "").upper()
                                    if (
                                        pr_state_r == "MERGED"
                                        and pr_num_r is not None
                                        and pr_num_r != main_pr_num_recon
                                    ):
                                        for done_agent in completed:
                                            claim_key = (
                                                f"{task.issue_number}:{pr_num_r}:{done_agent}"
                                            )
                                            if claim_key not in _claimed_child_prs:
                                                _claimed_child_prs.add(claim_key)
                                                logger.debug(
                                                    "Reconstructed claim for merged PR #%d "
                                                    "(agent '%s') on issue #%d",
                                                    pr_num_r,
                                                    done_agent,
                                                    task.issue_number,
                                                )
                            except Exception as e:
                                logger.debug(
                                    "Could not reconstruct child PR claims for issue #%d: %s",
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
            already_done = await _cp._check_agent_done_on_sub_or_parent(
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
            main_branch_info = _cp.get_issue_main_branch(task.issue_number)
            main_pr_number = main_branch_info["pr_number"] if main_branch_info else None
            main_branch = main_branch_info["branch"] if main_branch_info else None
            is_subsequent_agent = main_branch_info is not None

            finished_pr = None

            # For subsequent agents, check child PR completion FIRST
            # Subsequent agents create child PRs targeting the main branch (not 'main')
            if is_subsequent_agent and main_branch and main_pr_number:
                child_pr_info = await _cp._find_completed_child_pr(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                    main_branch=main_branch,
                    main_pr_number=main_pr_number,
                    agent_name=current_agent,
                    pipeline=pipeline,
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
            # Search both parent issue AND current agent's sub-issue.
            if not finished_pr:
                finished_pr = await _cp.github_projects_service.check_copilot_pr_completion(
                    access_token=access_token,
                    owner=task_owner,
                    repo=task_repo,
                    issue_number=task.issue_number,
                )

            # Still nothing: check agent's sub-issue for PR completion
            if not finished_pr:
                sub_num = _cp._get_sub_issue_number(pipeline, current_agent, task.issue_number)
                if sub_num and sub_num != task.issue_number:
                    finished_pr = await _cp.github_projects_service.check_copilot_pr_completion(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=sub_num,
                    )
                    if finished_pr:
                        # Link the sub-issue PR to the parent for future detection
                        pr_num = finished_pr.get("number")
                        if pr_num:
                            try:
                                await _cp.github_projects_service.link_pull_request_to_issue(
                                    access_token=access_token,
                                    owner=task_owner,
                                    repo=task_repo,
                                    pr_number=pr_num,
                                    issue_number=task.issue_number,
                                )
                            except Exception:
                                pass

                        # If this is a subsequent agent (main branch exists)
                        # and the PR is NOT the main PR itself, it must be a
                        # child PR.  Flag it so the merge step below runs.
                        # Without this, child PRs found via the sub-issue
                        # fallback skip the merge, and Done! is posted before
                        # the child PR is merged into the main branch (#740).
                        if (
                            is_subsequent_agent
                            and main_pr_number is not None
                            and pr_num != main_pr_number
                        ):
                            finished_pr["is_child_pr"] = True
                            logger.info(
                                "Marked sub-issue PR #%s as child PR for agent '%s' "
                                "(parent issue #%d, main PR #%d)",
                                pr_num,
                                current_agent,
                                task.issue_number,
                                main_pr_number,
                            )
                        logger.info(
                            "Found completed PR #%s for agent '%s' via sub-issue #%d "
                            "(parent issue #%d)",
                            finished_pr.get("number"),
                            current_agent,
                            sub_num,
                            task.issue_number,
                        )

            if not finished_pr:
                # No completed PR found via standard detection.
                # For subsequent agents, also check if work was done directly
                # on the main PR (Copilot pushes commits to the same branch
                # rather than creating a child PR).
                if is_subsequent_agent and main_pr_number is not None:
                    main_pr_completed = await _cp._check_main_pr_completion(
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
                        pr_details = await _cp.github_projects_service.get_pull_request(
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
                main_pr_completed = await _cp._check_main_pr_completion(
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

            cache_key = _cp.cache_key_agent_output(task.issue_number, current_agent, pr_number)
            if cache_key in _posted_agent_outputs:
                continue

            logger.info(
                "Agent '%s' PR #%d complete for issue #%d — processing completion",
                current_agent,
                pr_number,
                task.issue_number,
            )

            # Track whether this is a child PR for later merging
            is_child_pr = finished_pr.get("is_child_pr", False)

            # STEP 1: Get PR details for posting .md outputs
            pr_details = await _cp.github_projects_service.get_pull_request(
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
            if head_ref and not _cp.get_issue_main_branch(task.issue_number):
                # Get head commit SHA for subsequent agent branching
                head_sha = ""
                if pr_details and pr_details.get("last_commit", {}).get("sha"):
                    head_sha = pr_details["last_commit"]["sha"]
                _cp.set_issue_main_branch(task.issue_number, head_ref, pr_number, head_sha)
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
                    await _cp.github_projects_service.link_pull_request_to_issue(
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
            pr_files = await _cp.github_projects_service.get_pr_changed_files(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                pr_number=pr_number,
            )

            # Find .md files that match the agent's expected outputs
            expected_files = _cp.AGENT_OUTPUT_FILES.get(current_agent, [])
            posted_count = 0

            # Determine which issue to post markdown file comments on.
            # Markdown files are ONLY posted on the sub-issue — never on the parent.
            # The Done! marker is posted on the parent issue separately below.
            comment_issue_number: int | None = None
            if pipeline and pipeline.agent_sub_issues:
                sub_info = pipeline.agent_sub_issues.get(current_agent)
                if sub_info and sub_info.get("number"):
                    comment_issue_number = sub_info["number"]
                    logger.info(
                        "Posting agent '%s' markdown outputs on sub-issue #%d (parent #%d)",
                        current_agent,
                        comment_issue_number,
                        task.issue_number,
                    )

            # Fall back to the global sub-issue store (survives pipeline resets)
            if comment_issue_number is None:
                global_subs = _cp.get_issue_sub_issues(task.issue_number)
                sub_info = global_subs.get(current_agent)
                if sub_info and sub_info.get("number"):
                    comment_issue_number = sub_info["number"]
                    logger.info(
                        "Using sub-issue #%d from global store for agent '%s' (parent #%d)",
                        comment_issue_number,
                        current_agent,
                        task.issue_number,
                    )

            if comment_issue_number is None:
                logger.info(
                    "No sub-issue for agent '%s' on issue #%d — "
                    "skipping markdown file comments (only Done! on parent)",
                    current_agent,
                    task.issue_number,
                )

            # Only post markdown file comments if a sub-issue exists.
            # Markdown files are NEVER posted on the parent issue.
            if comment_issue_number is not None:
                for pr_file in pr_files:
                    filename = pr_file.get("filename", "")
                    basename = filename.rsplit("/", 1)[-1] if "/" in filename else filename

                    if basename.lower() in [f.lower() for f in expected_files]:
                        # Fetch file content from the PR branch
                        ref = head_ref or "HEAD"
                        content = await _cp.github_projects_service.get_file_content_from_ref(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            path=filename,
                            ref=ref,
                        )

                        if content:
                            # Post file content as a comment on the sub-issue only
                            comment_body = f"**`{filename}`** (generated by `{current_agent}`)\n\n---\n\n{content}"
                            comment = await _cp.github_projects_service.create_issue_comment(
                                access_token=access_token,
                                owner=task_owner,
                                repo=task_repo,
                                issue_number=comment_issue_number,
                                body=comment_body,
                            )
                            if comment:
                                posted_count += 1
                                logger.info(
                                    "Posted content of %s as comment on sub-issue #%d",
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

                # Also post any other .md files changed in the PR (on sub-issue only)
                for pr_file in pr_files:
                    filename = pr_file.get("filename", "")
                    basename = filename.rsplit("/", 1)[-1] if "/" in filename else filename

                    if (
                        basename.lower().endswith(".md")
                        and basename.lower() not in [f.lower() for f in expected_files]
                        and pr_file.get("status") in ("added", "modified")
                    ):
                        ref = head_ref or "HEAD"
                        content = await _cp.github_projects_service.get_file_content_from_ref(
                            access_token=access_token,
                            owner=task_owner,
                            repo=task_repo,
                            path=filename,
                            ref=ref,
                        )

                        if content:
                            comment_body = f"**`{filename}`** (generated by `{current_agent}`)\n\n---\n\n{content}"
                            await _cp.github_projects_service.create_issue_comment(
                                access_token=access_token,
                                owner=task_owner,
                                repo=task_repo,
                                issue_number=comment_issue_number,
                                body=comment_body,
                            )
                            posted_count += 1

            # STEP 4: Merge child PR into the main branch BEFORE posting
            # Done! so that the next agent starts from the correct base.
            # If the merge fails we skip this issue entirely (no Done!,
            # no cache entry) so it will be retried on the next poll cycle.
            main_branch_info = _cp.get_issue_main_branch(task.issue_number)
            if is_child_pr and main_branch_info:
                if finished_pr.get("is_merged", False):
                    # Child PR was already merged (e.g., container restarted
                    # between merge and Done! posting).  Skip the merge step
                    # and proceed to post the Done! marker.
                    logger.info(
                        "Child PR #%d for agent '%s' on issue #%d is already "
                        "merged — proceeding to post Done! marker",
                        pr_number,
                        current_agent,
                        task.issue_number,
                    )
                else:
                    merge_result = await _cp._merge_child_pr_if_applicable(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=task.issue_number,
                        main_branch=main_branch_info["branch"],
                        main_pr_number=main_branch_info["pr_number"],
                        completed_agent=current_agent,
                        pipeline=pipeline,
                    )
                    if merge_result:
                        logger.info(
                            "Merged child PR #%d for agent '%s' on issue #%d",
                            pr_number,
                            current_agent,
                            task.issue_number,
                        )
                        # Wait a moment for GitHub to fully process the merge
                        await asyncio.sleep(2)
                    else:
                        logger.warning(
                            "Failed to merge child PR #%d for agent '%s' on issue #%d "
                            "— skipping Done! marker, will retry next cycle",
                            pr_number,
                            current_agent,
                            task.issue_number,
                        )
                        continue

            # Mark the child PR as claimed (before Done! so it won't be
            # misattributed even if Done! posting fails)
            if is_child_pr:
                claimed_key = f"{task.issue_number}:{pr_number}:{current_agent}"
                _claimed_child_prs.add(claimed_key)
                logger.debug(
                    "Marked child PR #%d as claimed by agent '%s' on issue #%d",
                    pr_number,
                    current_agent,
                    task.issue_number,
                )

            # Post the Done! marker on the PARENT issue only.
            # This is the ONLY comment that goes on the main issue.
            done_issue_number = task.issue_number  # Always the parent
            done_comment = await _cp.github_projects_service.create_issue_comment(
                access_token=access_token,
                owner=task_owner,
                repo=task_repo,
                issue_number=done_issue_number,
                body=marker,
            )

            if done_comment:
                # Only add to cache AFTER we know Done! was posted successfully
                _posted_agent_outputs.add(cache_key)

                logger.info(
                    "Posted '%s' marker on parent issue #%d (%d .md files posted on %s)",
                    marker,
                    done_issue_number,
                    posted_count,
                    f"sub-issue #{comment_issue_number}"
                    if comment_issue_number
                    else "no sub-issue",
                )

                # STEP 5: Close the sub-issue as completed.
                if comment_issue_number is not None and comment_issue_number != task.issue_number:
                    closed = await _cp.github_projects_service.update_issue_state(
                        access_token=access_token,
                        owner=task_owner,
                        repo=task_repo,
                        issue_number=comment_issue_number,
                        state="closed",
                        state_reason="completed",
                    )
                    if closed:
                        logger.info(
                            "Closed sub-issue #%d as completed (agent '%s' done)",
                            comment_issue_number,
                            current_agent,
                        )
                    else:
                        logger.warning(
                            "Failed to close sub-issue #%d after agent '%s' completion",
                            comment_issue_number,
                            current_agent,
                        )

                # Update the tracking table in the issue body: mark agent as ✅ Done
                await _cp._update_issue_tracking(
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
