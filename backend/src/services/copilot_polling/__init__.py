"""
Copilot Polling Service Package

Background Polling Service for Copilot PR Completion Detection.
This package polls GitHub Issues in "In Progress" status to detect when
GitHub Copilot has completed work on linked Pull Requests.

Re-exports all public symbols that were available from the original
``copilot_polling`` module so that ``from src.services.copilot_polling import X``
continues to work.
"""

# --- State (module-level variables accessed by external code) ---
from .state import (  # noqa: F401
    ASSIGNMENT_GRACE_PERIOD_SECONDS,
    _claimed_child_prs,
    _pending_agent_assignments,
    _polling_state,
    _polling_task,
    _posted_agent_outputs,
    _processed_issue_prs,
    _recovery_last_attempt,
    _system_marked_ready_prs,
)

# --- Tracking (internal helpers re-exported for tests) ---
from .tracking import (  # noqa: F401
    _filter_events_after,
    _reconstruct_pipeline_state,
)

# --- Pipeline (internal helpers re-exported for tests) ---
from .pipeline import (  # noqa: F401
    _advance_pipeline,
    _transition_after_pipeline_complete,
)

# --- PR detection ---
from .pr_detection import (  # noqa: F401
    _check_child_pr_completion,
    _check_main_pr_completion,
    _find_completed_child_pr,
    _merge_child_pr_if_applicable,
    post_agent_outputs_from_pr,
)

# --- Status checks ---
from .status_checks import (  # noqa: F401
    check_backlog_issues,
    check_in_progress_issues,
    check_in_review_issues_for_copilot_review,
    check_ready_issues,
    ensure_copilot_review_requested,
    process_in_progress_issue,
)

# --- Lifecycle ---
from .lifecycle import (  # noqa: F401
    check_issue_for_copilot_completion,
    get_polling_status,
    poll_for_copilot_completion,
    recover_stalled_issues,
    stop_polling,
)
