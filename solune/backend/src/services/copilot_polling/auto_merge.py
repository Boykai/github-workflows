"""Auto-merge logic for squash-merging parent PRs on pipeline completion.

Implements _attempt_auto_merge() which discovers the main PR, checks CI and
mergeability, and performs a squash merge when all conditions are met.
Also implements dispatch_devops_agent() for CI failure recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from src.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class AutoMergeResult:
    """Structured result from an auto-merge attempt."""

    status: Literal["merged", "devops_needed", "merge_failed", "retry_later"]
    pr_number: int | None = None
    merge_commit: str | None = None
    error: str | None = None
    context: dict[str, Any] | None = field(default=None)


async def _attempt_auto_merge(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
) -> AutoMergeResult:
    """Attempt to auto-squash-merge the main PR for an issue.

    Steps:
    1. Discover the main PR via existing multi-strategy logic.
    2. If draft, mark ready-for-review.
    3. Check CI status via get_check_runs_for_ref().
    4. Check mergeability via get_pr_mergeable_state().
    5. If all pass, squash merge via merge_pull_request().

    Returns:
        AutoMergeResult with status indicating outcome.
    """
    import src.services.copilot_polling as _cp

    from .helpers import _discover_main_pr_for_review

    # Step 1: Discover main PR
    discovered = await _discover_main_pr_for_review(
        access_token=access_token,
        owner=owner,
        repo=repo,
        parent_issue_number=issue_number,
    )

    if not discovered:
        logger.warning(
            "Auto-merge: no main PR found for issue #%d",
            issue_number,
        )
        return AutoMergeResult(
            status="merge_failed",
            error="No main PR found for issue",
        )

    pr_number = discovered["pr_number"]
    pr_id = discovered.get("pr_id", "")
    head_ref = discovered.get("head_ref", "")
    is_draft = discovered.get("is_draft", False)

    logger.info(
        "Auto-merge: discovered main PR #%d for issue #%d (draft=%s)",
        pr_number,
        issue_number,
        is_draft,
    )

    # Step 2: Mark draft PR ready-for-review
    if is_draft and pr_id:
        logger.info("Auto-merge: converting PR #%d from draft to ready", pr_number)
        mark_success = await _cp.github_projects_service.mark_pr_ready_for_review(
            access_token=access_token,
            pr_node_id=str(pr_id),
        )
        if not mark_success:
            logger.warning(
                "Auto-merge: failed to convert PR #%d from draft to ready",
                pr_number,
            )

    # Step 3: Check CI status — fail closed (never merge when CI status unknown)
    if not head_ref:
        logger.warning(
            "Auto-merge: missing head_ref for PR #%d; cannot determine CI status",
            pr_number,
        )
        return AutoMergeResult(
            status="retry_later",
            pr_number=pr_number,
            context={"reason": "ci_status_unavailable", "details": "Missing head_ref"},
        )

    check_runs = await _cp.github_projects_service.get_check_runs_for_ref(
        access_token=access_token,
        owner=owner,
        repo=repo,
        ref=head_ref,
    )
    if check_runs is None:
        logger.warning(
            "Auto-merge: unable to fetch CI check runs for PR #%d (ref=%s)",
            pr_number,
            head_ref,
        )
        return AutoMergeResult(
            status="retry_later",
            pr_number=pr_number,
            context={"reason": "ci_status_unavailable", "details": "Failed to fetch check runs"},
        )

    failed_checks = [
        cr
        for cr in check_runs
        if cr.get("status") == "completed" and cr.get("conclusion") in ("failure", "timed_out")
    ]
    if failed_checks:
        logger.info(
            "Auto-merge: CI failures found on PR #%d (%d failed checks)",
            pr_number,
            len(failed_checks),
        )
        return AutoMergeResult(
            status="devops_needed",
            pr_number=pr_number,
            context={
                "reason": "ci_failure",
                "failed_checks": [
                    {"name": cr.get("name", ""), "conclusion": cr.get("conclusion", "")}
                    for cr in failed_checks
                ],
            },
        )

    # Check if there are still running checks — retry later, don't dispatch DevOps
    in_progress = [cr for cr in check_runs if cr.get("status") in ("queued", "in_progress")]
    if in_progress:
        logger.info(
            "Auto-merge: %d checks still running on PR #%d, will retry later",
            len(in_progress),
            pr_number,
        )
        return AutoMergeResult(
            status="retry_later",
            pr_number=pr_number,
            context={
                "reason": "checks_pending",
                "pending_count": len(in_progress),
            },
        )

    # Step 4: Check mergeability
    mergeable_state = await _cp.github_projects_service.get_pr_mergeable_state(
        access_token=access_token,
        owner=owner,
        repo=repo,
        pr_number=pr_number,
    )

    if mergeable_state == "CONFLICTING":
        logger.info("Auto-merge: PR #%d has merge conflicts", pr_number)
        return AutoMergeResult(
            status="devops_needed",
            pr_number=pr_number,
            context={"reason": "conflicting"},
        )

    if mergeable_state == "UNKNOWN":
        logger.info("Auto-merge: PR #%d mergeability is UNKNOWN, will retry", pr_number)
        return AutoMergeResult(
            status="retry_later",
            pr_number=pr_number,
            context={"reason": "unknown_mergeability"},
        )

    # Step 5: Squash merge
    if not pr_id:
        # Fetch full PR details to get node ID
        pr_details = await _cp.github_projects_service.get_pull_request(
            access_token=access_token,
            owner=owner,
            repo=repo,
            pr_number=pr_number,
        )
        if pr_details:
            pr_id = pr_details.get("id", "")

    if not pr_id:
        return AutoMergeResult(
            status="merge_failed",
            pr_number=pr_number,
            error="Could not resolve PR node ID for merge",
        )

    try:
        merge_result = await _cp.github_projects_service.merge_pull_request(
            access_token=access_token,
            pr_node_id=str(pr_id),
            pr_number=pr_number,
            merge_method="SQUASH",
        )
        if merge_result and merge_result.get("merged"):
            merge_commit = merge_result.get("merge_commit", "")
            logger.info(
                "Auto-merge: successfully squash-merged PR #%d (commit=%s)",
                pr_number,
                merge_commit[:8] if merge_commit else "unknown",
            )
            return AutoMergeResult(
                status="merged",
                pr_number=pr_number,
                merge_commit=merge_commit,
            )
        else:
            logger.error(
                "Auto-merge: merge API call returned without merged state for PR #%d",
                pr_number,
            )
            return AutoMergeResult(
                status="merge_failed",
                pr_number=pr_number,
                error="Merge API call did not confirm merge",
            )
    except Exception as exc:
        logger.error(
            "Auto-merge: merge API call failed for PR #%d: %s",
            pr_number,
            exc,
            exc_info=True,
        )
        return AutoMergeResult(
            status="merge_failed",
            pr_number=pr_number,
            error=str(exc),
        )


def _build_devops_instructions(
    owner: str,
    repo: str,
    issue_number: int,
    merge_result_context: dict[str, Any] | None = None,
) -> str:
    """Build custom instructions for the DevOps agent based on merge failure context."""
    lines = [
        f"Fix merge/CI issues for issue #{issue_number} in {owner}/{repo}.",
        "",
    ]

    if not merge_result_context:
        lines.append("The auto-merge attempt failed. Investigate and resolve the issue.")
        return "\n".join(lines)

    reason = merge_result_context.get("reason", "unknown")

    if reason == "ci_failure":
        failed_checks = merge_result_context.get("failed_checks", [])
        lines.append("## CI Failures")
        for check in failed_checks:
            name = check.get("name", "unknown")
            conclusion = check.get("conclusion", "unknown")
            lines.append(f"- **{name}**: {conclusion}")
        lines.append("")
        lines.append("Investigate the CI failures above. Fix the code so all checks pass.")
    elif reason == "conflicting":
        lines.append("## Merge Conflicts")
        lines.append(
            "The PR has merge conflicts with the base branch. "
            "Resolve all conflicts and ensure the branch is up to date."
        )
    else:
        lines.append(f"## Issue: {reason}")
        details = merge_result_context.get("details", "")
        if details:
            lines.append(details)

    return "\n".join(lines)


async def dispatch_devops_agent(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    pipeline_metadata: dict[str, Any],
    project_id: str,
    merge_result_context: dict[str, Any] | None = None,
) -> bool:
    """Dispatch the DevOps agent for CI failure / merge conflict recovery.

    Checks deduplication (devops_active) and retry cap (devops_attempts < 2).
    Resolves the issue node ID and assigns Copilot with the ``devops`` custom
    agent via ``assign_copilot_to_issue()``.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        pipeline_metadata: Pipeline metadata dict (mutated in place)
        project_id: Project ID for broadcast
        merge_result_context: Context from AutoMergeResult (CI failures, conflicts, etc.)

    Returns:
        True if agent was dispatched, False if skipped.
    """
    import src.services.copilot_polling as _cp

    devops_active = pipeline_metadata.get("devops_active", False)
    devops_attempts = pipeline_metadata.get("devops_attempts", 0)

    if devops_active:
        logger.info(
            "DevOps agent already active on issue #%d, skipping dispatch",
            issue_number,
        )
        return False

    if devops_attempts >= 2:
        logger.warning(
            "DevOps retry cap reached for issue #%d (%d attempts)",
            issue_number,
            devops_attempts,
        )
        return False

    # Resolve issue node ID for Copilot assignment
    issue_node_id: str | None = None
    try:
        issue_node_id, _ = await _cp.github_projects_service.get_issue_node_and_project_item(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_number=issue_number,
            project_id=project_id,
        )
    except Exception:
        logger.warning(
            "DevOps dispatch: failed to resolve issue node ID for #%d",
            issue_number,
            exc_info=True,
        )

    if not issue_node_id:
        logger.error(
            "DevOps dispatch: cannot resolve issue node ID for #%d — skipping",
            issue_number,
        )
        return False

    # Build context-aware instructions for the DevOps agent
    instructions = _build_devops_instructions(
        owner=owner,
        repo=repo,
        issue_number=issue_number,
        merge_result_context=merge_result_context,
    )

    # Dispatch DevOps agent via Copilot assignment
    logger.info(
        "Dispatching DevOps agent for issue #%d (attempt %d)",
        issue_number,
        devops_attempts + 1,
    )

    try:
        assigned = await _cp.github_projects_service.assign_copilot_to_issue(
            access_token=access_token,
            owner=owner,
            repo=repo,
            issue_node_id=issue_node_id,
            issue_number=issue_number,
            custom_agent="devops",
            custom_instructions=instructions,
        )
    except Exception:
        logger.error(
            "DevOps dispatch: assign_copilot_to_issue failed for #%d",
            issue_number,
            exc_info=True,
        )
        return False

    if not assigned:
        logger.error(
            "DevOps dispatch: Copilot assignment returned False for #%d",
            issue_number,
        )
        return False

    pipeline_metadata["devops_active"] = True
    pipeline_metadata["devops_attempts"] = devops_attempts + 1

    # Broadcast devops_triggered event
    await _cp.connection_manager.broadcast_to_project(
        project_id,
        {
            "type": "devops_triggered",
            "issue_number": issue_number,
            "attempt": devops_attempts + 1,
        },
    )

    return True
