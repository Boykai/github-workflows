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

import asyncio

from src.constants import (
    AGENT_OUTPUT_FILES,
    cache_key_agent_output,
    cache_key_issue_pr,
    cache_key_review_requested,
)
from src.models.workflow import WorkflowConfiguration
from src.services.agent_tracking import (
    STATE_ACTIVE,
    STATE_DONE,
    STATE_PENDING,
    get_current_agent_from_tracking,
    get_next_pending_agent,
    mark_agent_active,
    mark_agent_done,
    parse_tracking_from_body,
)
from src.services.github_projects import github_projects_service
from src.services.websocket import connection_manager
from src.services.workflow_orchestrator import (
    PipelineGroupInfo,
    PipelineState,
    WorkflowContext,
    WorkflowState,
    count_active_pipelines_for_project,
    find_next_actionable_status,
    get_agent_slugs,
    get_issue_main_branch,
    get_issue_sub_issues,
    get_next_status,
    get_pipeline_state,
    get_queued_pipelines_for_project,
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

from .agent_output import (
    post_agent_outputs_from_pr,
)
from .completion import (
    _check_child_pr_completion,
    _check_main_pr_completion,
    _filter_events_after,
    _find_completed_child_pr,
    _merge_child_pr_if_applicable,
    check_in_review_issues_for_copilot_review,
    check_issue_for_copilot_completion,
    ensure_copilot_review_requested,
)
from .helpers import (
    _check_agent_done_on_parent,
    _check_agent_done_on_sub_or_parent,
    _check_copilot_review_done,
    _discover_main_pr_for_review,
    _get_linked_prs_including_sub_issues,
    _get_sub_issue_number,
    _get_sub_issue_numbers_for_issue,
    _get_tracking_state_from_issue,
    _link_prs_to_parent,
    _reconstruct_sub_issue_mappings,
    _update_issue_tracking,
    is_sub_issue,
)
from .pipeline import (
    _advance_pipeline,
    _close_completed_sub_issues,
    _get_or_reconstruct_pipeline,
    _process_pipeline_completion,
    _reconstruct_pipeline_state,
    _self_heal_tracking_table,
    _transition_after_pipeline_complete,
    check_backlog_issues,
    check_in_progress_issues,
    check_in_review_issues,
    check_ready_issues,
    process_in_progress_issue,
)
from .polling_loop import (  # noqa: F401
    _check_rate_limit_budget,
    _pause_if_rate_limited,
    _poll_loop,
    get_polling_status,
    poll_app_pipeline,
    poll_for_copilot_completion,
    stop_polling,
)
from .recovery import (
    _validate_and_reconcile_tracking_table,  # noqa: F401
    recover_stalled_issues,
)

# ──────────────────────────────────────────────────────────────────────────────
# Phase 2: Import sub-module contents.  The ``from .xxx import *`` idiom
# brings every public name into THIS namespace so that existing
# ``mock.patch("src.services.copilot_polling.<func>")`` targets still work.
# ──────────────────────────────────────────────────────────────────────────────
from .state import (  # noqa: F401
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    POST_ACTION_DELAY_SECONDS,
    RATE_LIMIT_PAUSE_THRESHOLD,
    RATE_LIMIT_SKIP_EXPENSIVE_THRESHOLD,
    RATE_LIMIT_SLOW_THRESHOLD,
    RECOVERY_COOLDOWN_SECONDS,
    MonitoredProject,
    PollingState,
    _app_polling_tasks,
    _claimed_child_prs,
    _monitored_projects,
    _pending_agent_assignments,
    _polling_state,
    _polling_task,
    _posted_agent_outputs,
    _processed_issue_prs,
    _recovery_last_attempt,
    _review_requested_cache,
    _system_marked_ready_prs,
    get_monitored_projects,
    register_project,
    unregister_project,
)

# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

__all__ = [
    "AGENT_OUTPUT_FILES",
    "ASSIGNMENT_GRACE_PERIOD_SECONDS",
    "RECOVERY_COOLDOWN_SECONDS",
    "STATE_ACTIVE",
    "STATE_DONE",
    "STATE_PENDING",
    "PipelineGroupInfo",
    "PipelineState",
    "PollingState",
    "WorkflowConfiguration",
    "WorkflowContext",
    "WorkflowState",
    "_advance_pipeline",
    "_app_polling_tasks",
    "_check_agent_done_on_parent",
    "_check_agent_done_on_sub_or_parent",
    "_check_child_pr_completion",
    "_check_copilot_review_done",
    "_check_main_pr_completion",
    "_claimed_child_prs",
    "_close_completed_sub_issues",
    "_discover_main_pr_for_review",
    "_filter_events_after",
    "_find_completed_child_pr",
    "_get_linked_prs_including_sub_issues",
    "_get_or_reconstruct_pipeline",
    "_get_sub_issue_number",
    "_get_sub_issue_numbers_for_issue",
    "_get_tracking_state_from_issue",
    "_link_prs_to_parent",
    "_merge_child_pr_if_applicable",
    "_monitored_projects",
    "_pending_agent_assignments",
    "_poll_loop",
    "_polling_state",
    "_polling_task",
    "_posted_agent_outputs",
    "_process_pipeline_completion",
    "_processed_issue_prs",
    "_reconstruct_pipeline_state",
    "_reconstruct_sub_issue_mappings",
    "_recovery_last_attempt",
    "_review_requested_cache",
    "_self_heal_tracking_table",
    "_system_marked_ready_prs",
    "_transition_after_pipeline_complete",
    "_update_issue_tracking",
    "asyncio",
    "cache_key_agent_output",
    "cache_key_issue_pr",
    "cache_key_review_requested",
    "check_backlog_issues",
    "check_in_progress_issues",
    "check_in_review_issues",
    "check_in_review_issues_for_copilot_review",
    "check_issue_for_copilot_completion",
    "check_ready_issues",
    "connection_manager",
    "count_active_pipelines_for_project",
    "ensure_app_pipeline_polling",
    "ensure_copilot_review_requested",
    "ensure_polling_started",
    "find_next_actionable_status",
    "get_agent_slugs",
    "get_current_agent_from_tracking",
    "get_issue_main_branch",
    "get_issue_sub_issues",
    "get_monitored_projects",
    "get_next_pending_agent",
    "get_next_status",
    "get_pipeline_state",
    "get_polling_status",
    "get_queued_pipelines_for_project",
    "get_status_order",
    "get_workflow_config",
    "get_workflow_orchestrator",
    "github_projects_service",
    "is_sub_issue",
    "mark_agent_active",
    "mark_agent_done",
    "parse_tracking_from_body",
    "poll_app_pipeline",
    "poll_for_copilot_completion",
    "post_agent_outputs_from_pr",
    "process_in_progress_issue",
    "recover_stalled_issues",
    "register_project",
    "remove_pipeline_state",
    "set_issue_main_branch",
    "set_issue_sub_issues",
    "set_pipeline_state",
    "set_workflow_config",
    "stop_polling",
    "unregister_project",
    "update_issue_main_branch_sha",
]


# ──────────────────────────────────────────────────────────────────────────────
# Convenience helpers
# ──────────────────────────────────────────────────────────────────────────────

from src.logging_utils import get_logger as _get_logger

_logger = _get_logger(__name__)


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
    global _polling_task

    # Always register the project so the multi-project polling loop
    # picks it up even if the loop is already running for another project.
    from .state import register_project as _register

    _register(project_id, owner, repo, access_token)

    try:
        status = get_polling_status()
        if status["is_running"]:
            return False

        from src.services.task_registry import task_registry

        task = task_registry.create_task(
            poll_for_copilot_completion(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                interval_seconds=interval_seconds,
            ),
            name="copilot-polling",
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


async def ensure_app_pipeline_polling(
    *,
    access_token: str,
    project_id: str,
    owner: str,
    repo: str,
    parent_issue_number: int,
    interval_seconds: int = 15,
) -> bool:
    """Start a scoped polling loop for a new-repo / external-repo app pipeline.

    Unlike :func:`ensure_polling_started`, this creates a **secondary** polling
    task that monitors only the given parent issue and its sub-issues on the
    app's own project board.  It auto-stops when the pipeline is complete.

    Multiple app pipelines can run concurrently (one per ``project_id``).

    Returns ``True`` if a new loop was started, ``False`` if one is already
    running for this project.
    """
    from .state import _app_polling_tasks

    if project_id in _app_polling_tasks:
        task = _app_polling_tasks[project_id]
        if not task.done():
            _logger.debug("App-pipeline polling already running for project %s", project_id)
            return False
        # Clean up completed task
        del _app_polling_tasks[project_id]

    try:
        from src.services.task_registry import task_registry

        task = task_registry.create_task(
            poll_app_pipeline(
                access_token=access_token,
                project_id=project_id,
                owner=owner,
                repo=repo,
                parent_issue_number=parent_issue_number,
                interval_seconds=interval_seconds,
            ),
            name=f"app-pipeline-polling-{project_id[:12]}",
        )
        _app_polling_tasks[project_id] = task
        _logger.info(
            "Started scoped app-pipeline polling for issue #%d on %s/%s (project %s)",
            parent_issue_number,
            owner,
            repo,
            project_id,
        )
        return True
    except Exception as err:
        _logger.warning("Failed to start app-pipeline polling: %s", err)
        return False
