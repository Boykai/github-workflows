"""Pipeline state, branch tracking, and sub-issue map management."""

import logging

from .models import MainBranchInfo, PipelineState

logger = logging.getLogger(__name__)

# In-memory storage for pipeline states (per issue number)
_pipeline_states: dict[int, PipelineState] = {}

# In-memory storage for the "main" PR branch per issue
# The first PR's branch becomes the base for all subsequent agent branches
# Maps issue_number -> {branch: str, pr_number: int}
_issue_main_branches: dict[int, MainBranchInfo] = {}

# Global sub-issue mapping store that persists across pipeline state resets.
# When pipeline state is removed during status transitions (e.g., Backlog → Ready),
# the agent_sub_issues on PipelineState are lost.  This global store retains the
# mapping so subsequent agents can still look up (and close) their sub-issues.
# Maps issue_number → {agent_name → {"number": int, "node_id": str, "url": str}}
_issue_sub_issue_map: dict[int, dict[str, dict]] = {}


def get_pipeline_state(issue_number: int) -> PipelineState | None:
    """Get pipeline state for a specific issue."""
    return _pipeline_states.get(issue_number)


def get_all_pipeline_states() -> dict[int, PipelineState]:
    """Get all pipeline states."""
    return dict(_pipeline_states)


def set_pipeline_state(issue_number: int, state: PipelineState) -> None:
    """Set or update pipeline state for an issue."""
    _pipeline_states[issue_number] = state


def remove_pipeline_state(issue_number: int) -> None:
    """Remove pipeline state for an issue (e.g., after status transition)."""
    _pipeline_states.pop(issue_number, None)


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


def clear_issue_sub_issues(issue_number: int) -> None:
    """Clear the global sub-issue mapping for an issue.

    Should be called when the issue lifecycle is complete (e.g., moved to
    Done/In Review or closed) to free memory.  Pair with
    ``clear_issue_main_branch`` for full cleanup.
    """
    _issue_sub_issue_map.pop(issue_number, None)


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
    logger.info(
        "Updated HEAD SHA for issue #%d main branch '%s': %s → %s",
        issue_number,
        _issue_main_branches[issue_number].get("branch", ""),
        old_sha[:8] if old_sha else "none",
        head_sha[:8] if head_sha else "none",
    )
