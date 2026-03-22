"""Pipeline state, branch tracking, and sub-issue map management.

State is stored in-memory (BoundedDict L1 cache) and persisted to SQLite
via ``pipeline_state_store`` for durability across container restarts.
"""

from src.logging_utils import get_logger
from src.services.pipeline_state_store import (
    _agent_trigger_inflight,
    _issue_main_branches,
    _issue_sub_issue_map,
    _pipeline_states,
)
from src.services.pipeline_state_store import (
    clear_all_trigger_inflights as _clear_all_trigger_inflights_async,
)
from src.services.pipeline_state_store import (
    count_active_pipelines_for_project as count_active_pipelines_for_project,
)
from src.services.pipeline_state_store import (
    delete_main_branch as _delete_main_branch_async,
)
from src.services.pipeline_state_store import (
    delete_pipeline_state as _delete_pipeline_state_async,
)
from src.services.pipeline_state_store import (
    delete_sub_issue_map as _delete_sub_issue_map_async,
)
from src.services.pipeline_state_store import (
    delete_trigger_inflight as _delete_trigger_inflight_async,
)
from src.services.pipeline_state_store import (
    get_project_launch_lock as get_project_launch_lock,
)
from src.services.pipeline_state_store import (
    get_queued_pipelines_for_project as get_queued_pipelines_for_project,
)
from src.services.pipeline_state_store import (
    persist_pipeline_state_to_db as _persist_pipeline_state_to_db,
)
from src.services.pipeline_state_store import (
    set_main_branch as _set_main_branch_async,
)
from src.services.pipeline_state_store import (
    set_sub_issue_map as _set_sub_issue_map_async,
)
from src.services.pipeline_state_store import (
    set_trigger_inflight as _set_trigger_inflight_async,
)
from src.utils import utcnow

from .models import MainBranchInfo, PipelineState

logger = get_logger(__name__)

AGENT_TRIGGER_STALE_SECONDS = 120


def _schedule_persist(coro) -> None:
    """Schedule a persistence coroutine in the background (fire-and-forget).

    If no event loop is running (e.g. in sync tests), the persist is skipped
    and data remains in the L1 cache only.
    """
    try:
        from src.services.task_registry import task_registry

        task_registry.create_task(coro, name="wf-persist")
    except RuntimeError:
        coro.close()


def _agent_trigger_key(issue_number: int, status: str, agent_name: str) -> str:
    return f"{issue_number}:{status.lower()}:{agent_name}"


def should_skip_agent_trigger(
    issue_number: int,
    status: str,
    agent_name: str,
    stale_seconds: int = AGENT_TRIGGER_STALE_SECONDS,
) -> tuple[bool, float]:
    """Return (should_skip, age_seconds) for an agent trigger.

    This function also *claims* the trigger when it returns ``False`` by
    recording it in the in-flight map. Callers should release via
    ``release_agent_trigger`` when done.
    """
    key = _agent_trigger_key(issue_number, status, agent_name)
    now = utcnow()

    inflight_started = _agent_trigger_inflight.get(key)
    if inflight_started is not None:
        age_seconds = (now - inflight_started).total_seconds()
        if age_seconds < stale_seconds:
            return True, age_seconds
        # Stale in-flight marker (e.g. crash/exception path) — replace it.
        logger.warning(
            "Replacing stale in-flight trigger marker for issue=%d status='%s' agent='%s' "
            "(age=%.1fs)",
            issue_number,
            status,
            agent_name,
            age_seconds,
        )

    _agent_trigger_inflight[key] = now
    _schedule_persist(_set_trigger_inflight_async(key, now))
    return False, 0.0


def release_agent_trigger(issue_number: int, status: str, agent_name: str) -> None:
    """Release in-flight marker for an agent trigger."""
    key = _agent_trigger_key(issue_number, status, agent_name)
    _agent_trigger_inflight.pop(key, None)
    _schedule_persist(_delete_trigger_inflight_async(key))


def clear_agent_trigger_buffer(issue_number: int, status: str, agent_name: str) -> None:
    """Backward-compatible alias for clearing an in-flight marker."""
    release_agent_trigger(issue_number, status, agent_name)


def clear_all_agent_trigger_buffers() -> None:
    """Clear all trigger buffer entries."""
    _agent_trigger_inflight.clear()
    _schedule_persist(_clear_all_trigger_inflights_async())


def get_pipeline_state(issue_number: int) -> PipelineState | None:
    """Get pipeline state for a specific issue."""
    return _pipeline_states.get(issue_number)


def get_all_pipeline_states() -> dict[int, PipelineState]:
    """Get all pipeline states."""
    return dict(_pipeline_states)


def set_pipeline_state(issue_number: int, state: PipelineState) -> None:
    """Set or update pipeline state for an issue (L1 + SQLite write-behind)."""
    _pipeline_states[issue_number] = state
    _schedule_persist(_persist_pipeline_state_to_db(issue_number, state))


def remove_pipeline_state(issue_number: int) -> None:
    """Remove pipeline state for an issue (e.g., after status transition)."""
    _pipeline_states.pop(issue_number, None)
    _schedule_persist(_delete_pipeline_state_async(issue_number))


def get_issue_main_branch(issue_number: int) -> MainBranchInfo | None:
    """
    Get the main PR branch for an issue.

    The first PR's branch becomes the "main" branch for all subsequent
    agent work on that issue.

    Returns:
        Dict with 'branch' and 'pr_number' keys, or None if not set.
    """
    return _issue_main_branches.get(issue_number)


def get_issue_sub_issues(issue_number: int) -> dict[str, dict]:
    """Get the global sub-issue mapping for an issue.

    This store persists across pipeline state resets so that agents
    assigned after a status transition can still find their sub-issues.

    Returns:
        Dict mapping agent_name → {"number": int, "node_id": str, "url": str},
        or empty dict if not set.
    """
    mappings = _issue_sub_issue_map.get(issue_number)
    return dict(mappings) if mappings is not None else {}


def set_issue_sub_issues(issue_number: int, mappings: dict[str, dict]) -> None:
    """Store sub-issue mappings globally for an issue.

    Called when sub-issues are created upfront (create_all_sub_issues) or
    reconstructed from GitHub API.  Merges with existing mappings so that
    partial reconstructions don't overwrite earlier data.
    """
    existing = _issue_sub_issue_map.get(issue_number, {})
    existing.update(mappings)
    _issue_sub_issue_map[issue_number] = existing
    _schedule_persist(_set_sub_issue_map_async(issue_number, mappings))


def set_issue_main_branch(
    issue_number: int, branch: str, pr_number: int, head_sha: str = ""
) -> None:
    """
    Set the main PR branch for an issue.

    This should only be called once when the first PR is created for an issue.
    All subsequent agents will branch from and merge back into this branch.

    Args:
        issue_number: GitHub issue number
        branch: The first PR's head branch name (e.g., copilot/update-app-title-workflows)
        pr_number: The first PR's number
        head_sha: The commit SHA of the branch head (needed for baseRef)
    """
    if issue_number in _issue_main_branches:
        logger.debug(
            "Issue #%d already has main branch set to '%s', not overwriting",
            issue_number,
            _issue_main_branches[issue_number].get("branch"),
        )
        return
    _issue_main_branches[issue_number] = {
        "branch": branch,
        "pr_number": pr_number,
        "head_sha": head_sha,
    }
    _schedule_persist(
        _set_main_branch_async(
            issue_number,
            MainBranchInfo(branch=branch, pr_number=pr_number, head_sha=head_sha),
        )
    )
    logger.info(
        "Set main branch for issue #%d: '%s' (PR #%d, SHA: %s)",
        issue_number,
        branch,
        pr_number,
        head_sha[:8] if head_sha else "none",
    )


def clear_issue_main_branch(issue_number: int) -> None:
    """Clear the main branch tracking for an issue (e.g., when issue is closed)."""
    _issue_main_branches.pop(issue_number, None)
    _schedule_persist(_delete_main_branch_async(issue_number))


def clear_issue_sub_issues(issue_number: int) -> None:
    """Clear the global sub-issue mapping for an issue.

    Should be called when the issue lifecycle is complete (e.g., moved to
    Done/In Review or closed) to free memory.  Pair with
    ``clear_issue_main_branch`` for full cleanup.
    """
    _issue_sub_issue_map.pop(issue_number, None)
    _schedule_persist(_delete_sub_issue_map_async(issue_number))


def update_issue_main_branch_sha(issue_number: int, head_sha: str) -> None:
    """
    Update the HEAD SHA for an issue's main branch.

    Called after merging a child PR into the main branch so the next agent
    gets the correct (post-merge) commit SHA as its base_ref.

    Args:
        issue_number: GitHub issue number
        head_sha: New HEAD SHA after the child PR merge
    """
    if issue_number not in _issue_main_branches:
        logger.warning(
            "Cannot update HEAD SHA for issue #%d — no main branch set",
            issue_number,
        )
        return
    old_sha = _issue_main_branches[issue_number].get("head_sha", "")
    _issue_main_branches[issue_number]["head_sha"] = head_sha
    _schedule_persist(_set_main_branch_async(issue_number, _issue_main_branches[issue_number]))
    logger.info(
        "Updated HEAD SHA for issue #%d main branch '%s': %s → %s",
        issue_number,
        _issue_main_branches[issue_number].get("branch", ""),
        old_sha[:8] if old_sha else "none",
        head_sha[:8] if head_sha else "none",
    )
