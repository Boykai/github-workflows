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

    status: Literal["merged", "devops_needed", "merge_failed"]
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
    from src.services.copilot_polling import state as _cp
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

    # Step 3: Check CI status
    if head_ref:
        check_runs = await _cp.github_projects_service.get_check_runs_for_ref(
            access_token=access_token,
            owner=owner,
            repo=repo,
            ref=head_ref,
        )
        if check_runs is not None:
            failed_checks = [
                cr
                for cr in check_runs
                if cr.get("status") == "completed"
                and cr.get("conclusion") in ("failure", "timed_out")
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

            # Check if there are still running checks
            in_progress = [
                cr for cr in check_runs if cr.get("status") in ("queued", "in_progress")
            ]
            if in_progress:
                logger.info(
                    "Auto-merge: %d checks still running on PR #%d, will retry later",
                    len(in_progress),
                    pr_number,
                )
                return AutoMergeResult(
                    status="devops_needed",
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
            status="devops_needed",
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
            merge_commit = merge_result.get("mergeCommit", {}).get("oid", "")
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


async def dispatch_devops_agent(
    access_token: str,
    owner: str,
    repo: str,
    issue_number: int,
    pipeline_metadata: dict[str, Any],
    project_id: str,
) -> bool:
    """Dispatch the DevOps agent for CI failure recovery.

    Checks deduplication (devops_active) and retry cap (devops_attempts < 2).
    Dispatches via standard Copilot agent dispatch.

    Args:
        access_token: GitHub access token
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        pipeline_metadata: Pipeline metadata dict (mutated in place)
        project_id: Project ID for broadcast

    Returns:
        True if agent was dispatched, False if skipped.
    """
    from src.services.copilot_polling import state as _cp

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

    # Dispatch DevOps agent via standard Copilot dispatch
    logger.info(
        "Dispatching DevOps agent for issue #%d (attempt %d)",
        issue_number,
        devops_attempts + 1,
    )

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
