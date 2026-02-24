"""
Background Polling Service for Copilot PR Completion Detection

This service polls GitHub Issues in "In Progress" status to detect when
GitHub Copilot has completed work on linked Pull Requests.

When a Copilot PR is detected as complete (no longer a draft):
1. Convert the draft PR to ready for review (if still draft)
2. Update the linked issue status to "In Review"

This provides a fallback mechanism in addition to webhooks.
"""

# ──────────────────────────────────────────────────────────────────────────────
# Phase 1: Import all EXTERNAL dependencies so that mock.patch targets like
# ``src.services.copilot_polling.github_projects_service`` resolve on THIS
# module's namespace.  Sub-modules use ``import src.services.copilot_polling
# as _cp`` for late-bound access to these.
# ──────────────────────────────────────────────────────────────────────────────

import asyncio  # noqa: F401  — needed for mock.patch("...asyncio.sleep")

from src.constants import (  # noqa: F401
    AGENT_OUTPUT_FILES,
    cache_key_agent_output,
    cache_key_issue_pr,
    cache_key_review_requested,
)
from src.models.workflow import WorkflowConfiguration  # noqa: F401
from src.services.agent_tracking import (  # noqa: F401
    get_current_agent_from_tracking,
    get_next_pending_agent,
    mark_agent_active,
    mark_agent_done,
    parse_tracking_from_body,
)
from src.services.github_projects import github_projects_service  # noqa: F401
from src.services.websocket import connection_manager  # noqa: F401
from src.services.workflow_orchestrator import (  # noqa: F401
    PipelineState,
    WorkflowContext,
    WorkflowState,
    find_next_actionable_status,
    get_agent_slugs,
    get_issue_main_branch,
    get_issue_sub_issues,
    get_next_status,
    get_pipeline_state,
    get_status_order,
    get_workflow_config,
    get_workflow_orchestrator,
    remove_pipeline_state,
    set_issue_main_branch,
    set_issue_sub_issues,
    set_pipeline_state,
    set_workflow_config,
    update_issue_main_branch_sha,
)

from .agent_output import (  # noqa: F401
    post_agent_outputs_from_pr,
)
from .completion import (  # noqa: F401
    _check_child_pr_completion,
    _check_main_pr_completion,
    _filter_events_after,
    _find_completed_child_pr,
    _merge_child_pr_if_applicable,
    check_in_review_issues_for_copilot_review,
    check_issue_for_copilot_completion,
    ensure_copilot_review_requested,
)
from .helpers import (  # noqa: F401
    _check_agent_done_on_parent,
    _check_agent_done_on_sub_or_parent,
    _get_linked_prs_including_sub_issues,
    _get_sub_issue_number,
    _get_sub_issue_numbers_for_issue,
    _get_tracking_state_from_issue,
    _link_prs_to_parent,
    _reconstruct_sub_issue_mappings,
    _update_issue_tracking,
)
from .pipeline import (  # noqa: F401
    _advance_pipeline,
    _get_or_reconstruct_pipeline,
    _process_pipeline_completion,
    _reconstruct_pipeline_state,
    _transition_after_pipeline_complete,
    check_backlog_issues,
    check_in_progress_issues,
    check_ready_issues,
    process_in_progress_issue,
)
from .polling_loop import (  # noqa: F401
    _poll_loop,
    get_polling_status,
    poll_for_copilot_completion,
    stop_polling,
)
from .recovery import (  # noqa: F401
    recover_stalled_issues,
)

# ──────────────────────────────────────────────────────────────────────────────
# Phase 2: Import sub-module contents.  The ``from .xxx import *`` idiom
# brings every public name into THIS namespace so that existing
# ``mock.patch("src.services.copilot_polling.<func>")`` targets still work.
# ──────────────────────────────────────────────────────────────────────────────
from .state import (  # noqa: F401
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    RECOVERY_COOLDOWN_SECONDS,
    PollingState,
    _claimed_child_prs,
    _pending_agent_assignments,
    _polling_state,
    _polling_task,
    _posted_agent_outputs,
    _processed_issue_prs,
    _recovery_last_attempt,
    _system_marked_ready_prs,
)

# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

__all__ = [
    # State
    "PollingState",
    "ASSIGNMENT_GRACE_PERIOD_SECONDS",
    "RECOVERY_COOLDOWN_SECONDS",
    "_polling_state",
    "_polling_task",
    "_processed_issue_prs",
    "_posted_agent_outputs",
    "_claimed_child_prs",
    "_pending_agent_assignments",
    "_system_marked_ready_prs",
    "_recovery_last_attempt",
    # Helpers
    "_get_sub_issue_number",
    "_get_sub_issue_numbers_for_issue",
    "_get_linked_prs_including_sub_issues",
    "_link_prs_to_parent",
    "_check_agent_done_on_sub_or_parent",
    "_check_agent_done_on_parent",
    "_update_issue_tracking",
    "_get_tracking_state_from_issue",
    "_reconstruct_sub_issue_mappings",
    # Completion / review
    "_merge_child_pr_if_applicable",
    "_find_completed_child_pr",
    "_check_child_pr_completion",
    "_check_main_pr_completion",
    "_filter_events_after",
    "check_in_review_issues_for_copilot_review",
    "ensure_copilot_review_requested",
    "check_issue_for_copilot_completion",
    # Pipeline
    "_get_or_reconstruct_pipeline",
    "_process_pipeline_completion",
    "check_backlog_issues",
    "check_ready_issues",
    "_reconstruct_pipeline_state",
    "_advance_pipeline",
    "_transition_after_pipeline_complete",
    "check_in_progress_issues",
    "process_in_progress_issue",
    # Agent output
    "post_agent_outputs_from_pr",
    # Recovery
    "recover_stalled_issues",
    # Polling loop
    "poll_for_copilot_completion",
    "_poll_loop",
    "stop_polling",
    "get_polling_status",
    # Re-exported external dependencies (for mock.patch compatibility)
    "github_projects_service",
    "connection_manager",
    "get_workflow_config",
    "set_workflow_config",
    "get_pipeline_state",
    "set_pipeline_state",
    "remove_pipeline_state",
    "get_issue_main_branch",
    "set_issue_main_branch",
    "update_issue_main_branch_sha",
    "get_issue_sub_issues",
    "set_issue_sub_issues",
    "get_workflow_orchestrator",
    "get_agent_slugs",
    "find_next_actionable_status",
    "get_next_status",
    "get_status_order",
    "PipelineState",
    "WorkflowContext",
    "WorkflowState",
    "WorkflowConfiguration",
    "mark_agent_active",
    "mark_agent_done",
    "parse_tracking_from_body",
    "get_current_agent_from_tracking",
    "get_next_pending_agent",
    "AGENT_OUTPUT_FILES",
    "cache_key_agent_output",
    "cache_key_issue_pr",
    "cache_key_review_requested",
    "asyncio",
    # Convenience
    "ensure_polling_started",
]


# ──────────────────────────────────────────────────────────────────────────────
# Convenience helpers
# ──────────────────────────────────────────────────────────────────────────────

import logging as _logging

_logger = _logging.getLogger(__name__)


async def ensure_polling_started(
    *,
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    interval_seconds: int = 15,
    caller: str = "",
) -> bool:
    """Start Copilot polling if not already running.

    Consolidates the duplicated "check-status → create_task → assign" pattern
    used by ``chat.confirm_proposal``, ``workflow.confirm_recommendation``, and
    ``projects._start_copilot_polling``.

    Args:
        access_token: GitHub access token.
        project_id: GitHub Project node ID.
        owner: Repository owner.
        repo: Repository name.
        interval_seconds: Polling interval (default 15 s).
        caller: Human-readable label for log messages (e.g. ``"confirm_proposal"``).

    Returns:
        ``True`` if polling was started, ``False`` if it was already running.
    """
    global _polling_task  # noqa: PLW0603

    try:
        status = get_polling_status()
        if status["is_running"]:
            return False

        import asyncio as _aio

        task = _aio.create_task(
            poll_for_copilot_completion(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                interval_seconds=interval_seconds,
            )
        )

        # Store on the package namespace so stop_polling() can cancel it and
        # tests that patch ``src.services.copilot_polling._polling_task`` still
        # work.
        import src.services.copilot_polling as _self

        _self._polling_task = task

        log_suffix = f" from {caller}" if caller else ""
        _logger.info(
            "Auto-started Copilot polling%s for project %s",
            log_suffix,
            project_id,
        )
        return True
    except Exception as err:
        _logger.warning("Failed to start polling: %s", err)
        return False
