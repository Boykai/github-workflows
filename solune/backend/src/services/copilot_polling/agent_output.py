"""Agent output extraction and posting from completed PRs."""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import src.services.copilot_polling as _cp
from src.logging_utils import get_logger

from .state import (
    _claimed_child_prs,
    _polling_state,
    _posted_agent_outputs,
    _system_marked_ready_prs,
)

logger = get_logger(__name__)


@dataclass(frozen=True)
class CommentScanResult:
    """Result of scanning PR/issue comments for completion signals."""

    has_done_marker: bool
    done_comment_id: str | None = None
    agent_output_files: list[str] = field(default_factory=list)
    merge_candidates: list[str] = field(default_factory=list)


def _format_changed_file_list(paths: list[str], *, limit: int = 5) -> str:
    """Render a bounded, human-readable file list for issue comments."""
    if not paths:
        return "none"

    visible = [f"`{path}`" for path in paths[:limit]]
    remaining = len(paths) - limit
    if remaining > 0:
        visible.append(f"... and {remaining} more")
    return ", ".join(visible)


def _build_agent_output_summary(
    current_agent: str,
    pr_number: int,
    pr_files: list[dict[str, Any]],
) -> str:
    """Build a concise sub-issue summary for agents without explicit output artifacts."""
    changed_files = [
        pr_file.get("filename", "")
        for pr_file in pr_files
        if pr_file.get("filename") and pr_file.get("status") != "removed"
    ]
    markdown_files = [path for path in changed_files if path.lower().endswith(".md")]
    non_markdown_files = [path for path in changed_files if not path.lower().endswith(".md")]

    lines = [
        f"`{current_agent}` completed PR #{pr_number}.",
        "",
        "Summary:",
        f"- Changed files: {len(changed_files)}",
    ]

    if markdown_files:
        lines.append(
            f"- Markdown touched: {len(markdown_files)} ({_format_changed_file_list(markdown_files)})"
        )
    if non_markdown_files:
        lines.append(
            f"- Non-markdown touched: {len(non_markdown_files)} ({_format_changed_file_list(non_markdown_files)})"
        )
    if not changed_files:
        lines.append("- No changed files were reported for the PR")

    lines.append("- Full file contents were intentionally not reposted here")
    return "\n".join(lines)


async def _reconstruct_pipeline_if_missing(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    project_id: str,
) -> "_cp.PipelineState | None":
    """Reconstruct in-memory pipeline state from the durable tracking table.

    When volatile state is lost (e.g. after a container restart), this reads
    the issue body and comments to rebuild a PipelineState so that agent
    completions are detected and Done! markers posted correctly.

    Returns the reconstructed pipeline, or None if reconstruction failed.
    """
    try:
        body, comments = await _cp._get_tracking_state_from_issue(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )
        steps = _cp.parse_tracking_from_body(body)
        active_step = _cp.get_current_agent_from_tracking(body)
        if not steps or not active_step:
            return None

        status_key = active_step.status
        status_agents = [s.agent_name for s in steps if s.status == status_key]

        # Determine completed agents by checking Done! comments
        completed: list[str] = []
        last_done_ts: str | None = None
        for agent in status_agents:
            done_marker = f"{agent}: Done!"
            done_c = next(
                (
                    c
                    for c in comments
                    if any(line.strip() == done_marker for line in c.get("body", "").split("\n"))
                ),
                None,
            )
            if done_c:
                completed.append(agent)
                last_done_ts = done_c.get("created_at") or last_done_ts
            else:
                break  # Sequential — stop at first incomplete

        # Derive started_at from the last Done! marker
        recon_started: datetime | None = None
        if last_done_ts:
            try:
                recon_started = datetime.fromisoformat(last_done_ts)
            except (ValueError, TypeError):
                pass
        if recon_started is None:
            latest_any_done_ts: str | None = None
            for c in comments:
                body_text = c.get("body", "")
                for bline in body_text.split("\n"):
                    if bline.strip().endswith(": Done!"):
                        ts = c.get("created_at", "")
                        if ts and (latest_any_done_ts is None or ts > latest_any_done_ts):
                            latest_any_done_ts = ts
            if latest_any_done_ts:
                try:
                    recon_started = datetime.fromisoformat(latest_any_done_ts)
                except (ValueError, TypeError):
                    pass
        if recon_started is None:
            recon_started = datetime(2020, 1, 1, tzinfo=UTC)

        # Capture HEAD SHA from the main PR
        recon_sha = ""
        main_br = _cp.get_issue_main_branch(issue_number)
        if main_br and main_br.get("head_sha"):
            recon_sha = main_br["head_sha"]

        pipeline = _cp.PipelineState(
            issue_number=issue_number,
            project_id=project_id,
            status=status_key,
            agents=status_agents,
            current_agent_index=len(completed),
            completed_agents=completed,
            started_at=recon_started,
            agent_assigned_sha=recon_sha,
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
            "Reconstructed pipeline for issue #%d from tracking "
            "table: active agent '%s', status '%s', %d/%d done",
            issue_number,
            active_step.agent_name,
            status_key,
            len(completed),
            len(status_agents),
        )

        # Reconstruct main branch info if missing
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
                        "Reconstructed main branch '%s' (PR #%d) for issue #%d",
                        existing_pr["head_ref"],
                        existing_pr["number"],
                        issue_number,
                    )
                    if pr_det and not pr_det.get("is_draft", True):
                        _system_marked_ready_prs.add(existing_pr["number"])
                        logger.info(
                            "Marked main PR #%d as ready during "
                            "agent_output reconstruction for issue #%d",
                            existing_pr["number"],
                            issue_number,
                        )
            except Exception as e:
                logger.debug(
                    "Could not reconstruct main branch for issue #%d: %s",
                    issue_number,
                    e,
                )

        # Claim merged child PRs for ALL agents to prevent misattribution
        main_branch_recon = _cp.get_issue_main_branch(issue_number)
        if main_branch_recon:
            try:
                linked_prs_recon = await _cp.github_projects_service.get_linked_pull_requests(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
                    issue_number=issue_number,
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
                        for recon_agent in status_agents:
                            claim_key = f"{issue_number}:{pr_num_r}:{recon_agent}"
                            if claim_key not in _claimed_child_prs:
                                _claimed_child_prs.add(claim_key)
                                logger.debug(
                                    "Reconstructed claim for merged PR #%d "
                                    "(agent '%s') on issue #%d",
                                    pr_num_r,
                                    recon_agent,
                                    issue_number,
                                )
            except Exception as e:
                logger.debug(
                    "Could not reconstruct child PR claims for issue #%d: %s",
                    issue_number,
                    e,
                )
        return pipeline
    except Exception as e:
        logger.debug(
            "Could not reconstruct pipeline for issue #%d: %s",
            issue_number,
            e,
        )
        return None


async def _detect_completion_signals(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    current_agent: str,
    pipeline: "_cp.PipelineState",
) -> dict[str, Any] | None:
    """Detect whether the current agent's PR work is complete.

    Checks child PRs, standard Copilot PR completion, sub-issue PRs,
    and main PR completion signals.

    Returns the finished PR dict, or None if no completion detected.
    """
    if current_agent in ("copilot-review", "human"):
        return None

    main_branch_info = _cp.get_issue_main_branch(issue_number)
    main_pr_number = main_branch_info["pr_number"] if main_branch_info else None
    main_branch = main_branch_info["branch"] if main_branch_info else None
    is_subsequent_agent = main_branch_info is not None

    finished_pr = None

    # For subsequent agents, check child PR completion FIRST
    if is_subsequent_agent and main_branch and main_pr_number:
        child_pr_info = await _cp._find_completed_child_pr(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
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
                issue_number,
            )

    # If no child PR, check standard Copilot PR completion (first agent only)
    if not finished_pr and not is_subsequent_agent:
        finished_pr = await _cp.github_projects_service.check_copilot_pr_completion(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
        )

    # Check agent's sub-issue for PR completion (first agent only)
    if not finished_pr and not is_subsequent_agent:
        sub_num = _cp._get_sub_issue_number(pipeline, current_agent, issue_number)
        if sub_num and sub_num != issue_number:
            finished_pr = await _cp.github_projects_service.check_copilot_pr_completion(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=sub_num,
            )
            if finished_pr:
                pr_num = finished_pr.get("number")
                if pr_num:
                    try:
                        await _cp.github_projects_service.link_pull_request_to_issue(
                            access_token=access_token,
                            owner=owner,
                            repo=repo,
                            pr_number=pr_num,
                            issue_number=issue_number,
                        )
                    except Exception as e:
                        logger.debug("Suppressed error: %s", e)

                if is_subsequent_agent and main_pr_number is not None and pr_num != main_pr_number:
                    finished_pr["is_child_pr"] = True
                    logger.info(
                        "Marked sub-issue PR #%s as child PR for agent '%s' "
                        "(parent issue #%d, main PR #%d)",
                        pr_num,
                        current_agent,
                        issue_number,
                        main_pr_number,
                    )
                logger.info(
                    "Found completed PR #%s for agent '%s' via sub-issue #%d (parent issue #%d)",
                    finished_pr.get("number"),
                    current_agent,
                    sub_num,
                    issue_number,
                )

    # Check if work was done directly on the main PR (subsequent agents)
    if not finished_pr and is_subsequent_agent and main_pr_number is not None:
        agent_sub_number = _cp._get_sub_issue_number(pipeline, current_agent, issue_number)
        main_pr_completed = await _cp._check_main_pr_completion(
            access_token=access_token,
            owner=owner,
            repo=repo,
            main_pr_number=main_pr_number,
            issue_number=issue_number,
            agent_name=current_agent,
            pipeline_started_at=pipeline.started_at,
            agent_assigned_sha=pipeline.agent_assigned_sha,
            is_subsequent_agent=True,
            sub_issue_number=agent_sub_number,
        )
        if main_pr_completed:
            from .completion import _find_open_child_pr

            open_child_pr = await _find_open_child_pr(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                main_branch=main_branch or "main",
                main_pr_number=main_pr_number,
                agent_name=current_agent,
                pipeline=pipeline,
            )
            if open_child_pr:
                finished_pr = open_child_pr
                finished_pr["copilot_finished"] = True
                logger.info(
                    "Main PR completion confirmed for agent '%s' on issue #%d, but child PR #%d is still open — merging child PR before Done!",
                    current_agent,
                    issue_number,
                    open_child_pr.get("number"),
                )
            else:
                pr_details = await _cp.github_projects_service.get_pull_request(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
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
        return None

    pr_number = finished_pr.get("number")
    if not pr_number:
        return None

    # For subsequent agents, verify fresh completion signals on main PR
    if is_subsequent_agent and pr_number == main_pr_number and main_pr_number is not None:
        verify_sub_number = _cp._get_sub_issue_number(pipeline, current_agent, issue_number)
        main_pr_completed = await _cp._check_main_pr_completion(
            access_token=access_token,
            owner=owner,
            repo=repo,
            main_pr_number=main_pr_number,
            issue_number=issue_number,
            agent_name=current_agent,
            pipeline_started_at=pipeline.started_at,
            agent_assigned_sha=pipeline.agent_assigned_sha,
            is_subsequent_agent=True,
            sub_issue_number=verify_sub_number,
        )
        if not main_pr_completed:
            logger.debug(
                "Main PR #%d has no fresh completion signals for agent '%s' "
                "on issue #%d — still in progress",
                pr_number,
                current_agent,
                issue_number,
            )
            return None

    return finished_pr


async def _post_markdown_outputs(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    current_agent: str,
    pipeline: "_cp.PipelineState",
    pr_number: int,
    head_ref: str,
    pr_files: list[dict[str, Any]],
) -> int:
    """Post agent output artifacts or a summary comment on the agent's sub-issue.

    If the agent has declared output files (via ``AGENT_OUTPUT_FILES``), each
    matching ``.md`` file from the PR is posted as a comment on the sub-issue.
    If the agent has no declared output artifacts, a single concise summary
    comment is posted instead.

    Returns the number of files posted (0 for summary-only agents).
    """
    expected_files = _cp.AGENT_OUTPUT_FILES.get(current_agent, [])
    posted_count = 0

    # Determine which sub-issue to post on
    comment_issue_number: int | None = None
    if pipeline and pipeline.agent_sub_issues:
        sub_info = pipeline.agent_sub_issues.get(current_agent)
        if sub_info and sub_info.get("number"):
            comment_issue_number = sub_info["number"]
            logger.info(
                "Posting agent '%s' markdown outputs on sub-issue #%d (parent #%d)",
                current_agent,
                comment_issue_number,
                issue_number,
            )

    # Fall back to the global sub-issue store
    if comment_issue_number is None:
        global_subs = _cp.get_issue_sub_issues(issue_number)
        sub_info = global_subs.get(current_agent)
        if sub_info and sub_info.get("number"):
            comment_issue_number = sub_info["number"]
            logger.info(
                "Using sub-issue #%d from global store for agent '%s' (parent #%d)",
                comment_issue_number,
                current_agent,
                issue_number,
            )

    if comment_issue_number is None:
        logger.info(
            "No sub-issue for agent '%s' on issue #%d — "
            "skipping markdown file comments (only Done! on parent)",
            current_agent,
            issue_number,
        )
        return 0

    if not expected_files:
        summary_body = _build_agent_output_summary(
            current_agent=current_agent,
            pr_number=pr_number,
            pr_files=pr_files,
        )
        comment = await _cp.github_projects_service.create_issue_comment(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=comment_issue_number,
            body=summary_body,
        )
        if comment:
            logger.info(
                "Posted summary comment for agent '%s' on sub-issue #%d",
                current_agent,
                comment_issue_number,
            )
        return 0

    # Post expected output files
    expected_lower = {f.lower() for f in expected_files}
    for pr_file in pr_files:
        filename = pr_file.get("filename", "")
        basename = filename.rsplit("/", 1)[-1] if "/" in filename else filename

        if basename.lower() in expected_lower:
            ref = head_ref or "HEAD"
            content = await _cp.github_projects_service.get_file_content_from_ref(
                access_token=access_token,
                owner=owner,
                repo=repo,
                path=filename,
                ref=ref,
            )

            if content:
                comment_body = (
                    f"**`{filename}`** (generated by `{current_agent}`)\n\n---\n\n{content}"
                )
                comment = await _cp.github_projects_service.create_issue_comment(
                    access_token=access_token,
                    owner=owner,
                    repo=repo,
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
                    issue_number,
                )

    # Post other .md files not in the expected list
    for pr_file in pr_files:
        filename = pr_file.get("filename", "")
        basename = filename.rsplit("/", 1)[-1] if "/" in filename else filename

        if not basename.lower().endswith(".md"):
            continue
        if basename.lower() in expected_lower:
            continue

        ref = head_ref or "HEAD"
        content = await _cp.github_projects_service.get_file_content_from_ref(
            access_token=access_token,
            owner=owner,
            repo=repo,
            path=filename,
            ref=ref,
        )

        if content:
            comment_body = f"**`{filename}`** (generated by `{current_agent}`)\n\n---\n\n{content}"
            comment = await _cp.github_projects_service.create_issue_comment(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=comment_issue_number,
                body=comment_body,
            )
            if comment:
                posted_count += 1
                logger.info(
                    "Posted content of %s (other .md) as comment on sub-issue #%d",
                    filename,
                    comment_issue_number,
                )

    return posted_count


async def _merge_and_claim_child_pr(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    current_agent: str,
    pipeline: "_cp.PipelineState",
    finished_pr: dict[str, Any],
    pr_number: int,
    is_child_pr: bool,
) -> bool:
    """Merge child PR into main branch and claim it.

    Always returns True so the Done! marker is posted regardless of
    merge outcome.  Merge failures are retried by the safety-net in
    ``_advance_pipeline``; gating the Done! marker on merge success
    caused recovery to re-assign agents and create duplicate PRs.
    """
    main_branch_info = _cp.get_issue_main_branch(issue_number)

    if is_child_pr and main_branch_info:
        if finished_pr.get("is_merged", False):
            logger.info(
                "Child PR #%d for agent '%s' on issue #%d is already "
                "merged — proceeding to post Done! marker",
                pr_number,
                current_agent,
                issue_number,
            )
        else:
            merge_result = await _cp._merge_child_pr_if_applicable(
                access_token=access_token,
                owner=owner,
                repo=repo,
                issue_number=issue_number,
                main_branch=main_branch_info["branch"],
                main_pr_number=main_branch_info["pr_number"],
                completed_agent=current_agent,
                pipeline=pipeline,
            )
            if merge_result and merge_result.get("status") == "merged":
                logger.info(
                    "Merged child PR #%d for agent '%s' on issue #%d",
                    pr_number,
                    current_agent,
                    issue_number,
                )
                await asyncio.sleep(_cp.POST_ACTION_DELAY_SECONDS)
            else:
                logger.warning(
                    "Failed to merge child PR #%d for agent '%s' on issue #%d "
                    "— posting Done! marker anyway; safety-net in "
                    "_advance_pipeline will retry the merge",
                    pr_number,
                    current_agent,
                    issue_number,
                )

    # Mark the child PR as claimed
    if is_child_pr:
        claimed_key = f"{issue_number}:{pr_number}:{current_agent}"
        _claimed_child_prs.add(claimed_key)
        logger.debug(
            "Marked child PR #%d as claimed by agent '%s' on issue #%d",
            pr_number,
            current_agent,
            issue_number,
        )

    return True


async def _post_done_marker(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    current_agent: str,
    pipeline: "_cp.PipelineState",
    pr_number: int,
    posted_count: int,
    cache_key: str,
) -> dict[str, Any] | None:
    """Post the Done! marker on the parent issue and close the sub-issue.

    Returns a result dict on success, or None on failure.
    """
    marker = f"{current_agent}: Done!"
    done_comment = await _cp.github_projects_service.create_issue_comment(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        body=marker,
    )

    if not done_comment:
        logger.error("Failed to post Done! marker on issue #%d", issue_number)
        return None

    _posted_agent_outputs.add(cache_key)

    # Determine sub-issue for closing
    comment_issue_number: int | None = None
    if pipeline and pipeline.agent_sub_issues:
        sub_info = pipeline.agent_sub_issues.get(current_agent)
        if sub_info and sub_info.get("number"):
            comment_issue_number = sub_info["number"]
    if comment_issue_number is None:
        global_subs = _cp.get_issue_sub_issues(issue_number)
        sub_info = global_subs.get(current_agent)
        if sub_info and sub_info.get("number"):
            comment_issue_number = sub_info["number"]

    logger.info(
        "Posted '%s' marker on parent issue #%d (%d .md files posted on %s)",
        marker,
        issue_number,
        posted_count,
        f"sub-issue #{comment_issue_number}" if comment_issue_number else "no sub-issue",
    )

    # Close the sub-issue as completed
    if comment_issue_number is not None and comment_issue_number != issue_number:
        closed = await _cp.github_projects_service.update_issue_state(
            access_token=access_token,
            owner=owner,
            repo=repo,
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

    # Update the tracking table
    await _cp._update_issue_tracking(
        access_token=access_token,
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        agent_name=current_agent,
        new_state="done",
    )

    return {
        "status": "success",
        "issue_number": issue_number,
        "agent_name": current_agent,
        "pr_number": pr_number,
        "files_posted": posted_count,
        "action": "agent_outputs_posted",
    }


async def _process_task_agent_completion(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    task: Any,
    config: Any,
) -> dict[str, Any] | None:
    """Process a single task's agent completion for output posting.

    Returns a result dict if the agent's PR work is complete and outputs
    were posted, or None if no action was taken.
    """
    if task.issue_number is None:
        return None

    task_owner = task.repository_owner or owner
    task_repo = task.repository_name or repo
    if not task_owner or not task_repo:
        return None

    pipeline = _cp.get_pipeline_state(task.issue_number)

    # Reconstruct pipeline from tracking table if volatile state is lost
    if pipeline is None:
        pipeline = await _reconstruct_pipeline_if_missing(
            access_token=access_token,
            owner=task_owner,
            repo=task_repo,
            issue_number=task.issue_number,
            project_id=project_id,
        )

    if not pipeline or pipeline.is_complete:
        return None

    current_agent = pipeline.current_agent
    if not current_agent:
        return None

    # Check if we already posted outputs for this agent on this issue
    cache_prefix = f"{task.issue_number}:{current_agent}"
    if any(k.startswith(cache_prefix) for k in _posted_agent_outputs):
        return None

    # Check if the Done! marker is already posted (agent did it itself)
    already_done = await _cp._check_agent_done_on_sub_or_parent(
        access_token=access_token,
        owner=task_owner,
        repo=task_repo,
        parent_issue_number=task.issue_number,
        agent_name=current_agent,
        pipeline=pipeline,
    )
    if already_done:
        return None

    # Detect completion signals from PRs
    finished_pr = await _detect_completion_signals(
        access_token=access_token,
        owner=task_owner,
        repo=task_repo,
        issue_number=task.issue_number,
        current_agent=current_agent,
        pipeline=pipeline,
    )
    if not finished_pr:
        return None

    pr_number = finished_pr.get("number")
    if not pr_number:
        return None

    cache_key = _cp.cache_key_agent_output(
        task.issue_number,
        current_agent,
        pr_number,
        project_id,
    )
    if cache_key in _posted_agent_outputs:
        return None

    logger.info(
        "Agent '%s' PR #%d complete for issue #%d — processing completion",
        current_agent,
        pr_number,
        task.issue_number,
    )

    is_child_pr = finished_pr.get("is_child_pr", False)

    # Get PR details for posting .md outputs
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
    try:
        await _track_main_branch_if_needed(
            access_token=access_token,
            owner=task_owner,
            repo=task_repo,
            issue_number=task.issue_number,
            pr_number=pr_number,
            pr_details=pr_details,
            head_ref=head_ref,
        )
    except Exception:
        logger.warning(
            "Failed to track main branch for issue #%d PR #%d — continuing with completion",
            task.issue_number,
            pr_number,
            exc_info=True,
        )

    # Get changed files and post markdown outputs
    pr_files = await _cp.github_projects_service.get_pr_changed_files(
        access_token=access_token,
        owner=task_owner,
        repo=task_repo,
        pr_number=pr_number,
    )

    posted_count = await _post_markdown_outputs(
        access_token=access_token,
        owner=task_owner,
        repo=task_repo,
        issue_number=task.issue_number,
        current_agent=current_agent,
        pipeline=pipeline,
        pr_number=pr_number,
        head_ref=head_ref,
        pr_files=pr_files,
    )

    # Merge child PR into main branch before posting Done!
    await _merge_and_claim_child_pr(
        access_token=access_token,
        owner=task_owner,
        repo=task_repo,
        issue_number=task.issue_number,
        current_agent=current_agent,
        pipeline=pipeline,
        finished_pr=finished_pr,
        pr_number=pr_number,
        is_child_pr=is_child_pr,
    )

    # Post the Done! marker and close sub-issue
    return await _post_done_marker(
        access_token=access_token,
        owner=task_owner,
        repo=task_repo,
        issue_number=task.issue_number,
        current_agent=current_agent,
        pipeline=pipeline,
        pr_number=pr_number,
        posted_count=posted_count,
        cache_key=cache_key,
    )


async def _track_main_branch_if_needed(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    pr_number: int,
    pr_details: dict[str, Any] | None,
    head_ref: str,
) -> None:
    """Track the main branch for an issue if not already tracked."""
    if not head_ref or _cp.get_issue_main_branch(issue_number):
        return

    head_sha = ""
    if pr_details and pr_details.get("last_commit", {}).get("sha"):
        head_sha = pr_details["last_commit"]["sha"]
    _cp.set_issue_main_branch(issue_number, head_ref, pr_number, head_sha)
    logger.info(
        "Captured main branch '%s' (PR #%d, SHA: %s) for issue #%d",
        head_ref,
        pr_number,
        head_sha[:8] if head_sha else "none",
        issue_number,
    )

    if pr_details and not pr_details.get("is_draft", True):
        _system_marked_ready_prs.add(pr_number)
        logger.info(
            "Marked main PR #%d as ready (first agent completed) "
            "to prevent false positives for subsequent agents",
            pr_number,
        )

    try:
        await _cp.github_projects_service.link_pull_request_to_issue(
            access_token=access_token,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            issue_number=issue_number,
        )
    except Exception as e:
        logger.warning(
            "Failed to link PR #%d to issue #%d: %s",
            pr_number,
            issue_number,
            e,
        )


async def post_agent_outputs_from_pr(
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    tasks: list,
) -> list[dict[str, Any]]:
    """
    For all issues with active pipelines, check if the current agent's PR work
    is complete. If so, post explicit agent output artifacts or a concise
    summary comment on the **sub-issue**, and post the ``<agent-name>: Done!``
    marker on the **parent issue** only.

    Comment routing policy:

    - ``<agent>: Done!`` marker → parent (main) issue ONLY
    - Declared output artifacts → sub-issue ONLY (skipped if no sub-issue)
    - Agents without declared outputs → one summary comment on the sub-issue

    All agents are eligible — output files are optional, not required.

    This runs BEFORE the status-specific checks (backlog/ready/in-progress) so
    that the Done! markers are in place for the existing comment-based detection.
    """
    results = []

    try:
        config = await _cp.get_workflow_config(project_id)
        if not config:
            return results

        for task in tasks:
            result = await _process_task_agent_completion(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                task=task,
                config=config,
            )
            if result:
                results.append(result)

    except Exception as e:
        logger.error("Error posting agent outputs from PRs: %s", e)
        _polling_state.errors_count += 1
        _polling_state.last_error = str(e)

    return results
