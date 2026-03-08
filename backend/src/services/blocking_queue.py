"""Core blocking queue service — serial issue activation & branch ancestry control.

Manages the blocking queue state machine. Key responsibilities:
- Enqueue issues and determine immediate activation
- Implement batch activation rules (try_activate_next)
- Track branch ancestry from oldest open blocking issue
- Per-repo asyncio.Lock for concurrency control
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

from src.models.blocking import BlockingQueueEntry, BlockingQueueStatus
from src.services import blocking_queue_store as store

logger = logging.getLogger(__name__)

# Per-repo locks to prevent double-activation race conditions
_repo_locks: dict[str, asyncio.Lock] = {}


def _get_lock(repo_key: str) -> asyncio.Lock:
    """Get or create an asyncio.Lock for the given repo."""
    if repo_key not in _repo_locks:
        _repo_locks[repo_key] = asyncio.Lock()
    return _repo_locks[repo_key]


async def enqueue_issue(
    repo_key: str,
    issue_number: int,
    project_id: str,
    is_blocking: bool,
) -> tuple[BlockingQueueEntry, bool]:
    """Insert issue into the blocking queue and determine initial activation.

    Returns:
        Tuple of (entry, activated) — activated is True if the issue was
        immediately activated and agents should be assigned.
    """
    lock = _get_lock(repo_key)
    async with lock:
        try:
            entry = await store.insert(repo_key, issue_number, project_id, is_blocking)
        except Exception:
            # UNIQUE constraint — issue already enqueued
            existing = await store.get_by_issue(repo_key, issue_number)
            if existing:
                logger.warning(
                    "Issue #%d already in blocking queue for %s (status=%s)",
                    issue_number,
                    repo_key,
                    existing.queue_status,
                )
                return existing, existing.queue_status == BlockingQueueStatus.ACTIVE
            raise

        # Determine if this issue can activate immediately
        activated_issues = await _try_activate_next_unlocked(repo_key)
        activated = any(e.issue_number == issue_number for e in activated_issues)

        return await store.get_by_issue(repo_key, issue_number) or entry, activated


async def try_activate_next(repo_key: str) -> list[BlockingQueueEntry]:
    """Evaluate the queue and activate the next batch of pending issues.

    This is the core state machine entry point. Called on:
    - Issue enqueue
    - Issue transitions to in_review
    - Issue completion
    - Startup recovery

    Returns list of newly activated entries for agent assignment.
    """
    lock = _get_lock(repo_key)
    async with lock:
        return await _try_activate_next_unlocked(repo_key)


async def _try_activate_next_unlocked(repo_key: str) -> list[BlockingQueueEntry]:
    """Internal activation logic — must be called under the repo lock.

    Activation rules:
    1. If any entry is 'active' (not in_review), wait — nothing to activate.
    2. Gather pending entries (ordered by created_at ASC).
    3. If no pending → nothing to do.
    4. Check if any open blocking issues exist (active or in_review).
    5a. If open blocking exists → serial mode:
        - Next pending is blocking → activate alone
        - Next pending is non-blocking → activate consecutive non-blocking up to next blocking
    5b. If no open blocking → concurrent mode:
        - Next pending is non-blocking → activate all consecutive non-blocking up to next blocking
        - Next pending is blocking → activate alone (starts serial mode)
    6. For each activated entry: determine base branch, call mark_active.
    """
    # Check for any currently active (not yet in_review) entries
    active_or_review = await store.get_active_or_in_review(repo_key)
    has_active = any(
        e.queue_status == BlockingQueueStatus.ACTIVE for e in active_or_review
    )

    if has_active:
        logger.debug("Repo %s has active entries — skipping activation", repo_key)
        return []

    pending = await store.get_pending(repo_key)
    if not pending:
        return []

    open_blocking = await store.get_open_blocking(repo_key)
    has_open_blocking = len(open_blocking) > 0

    # Determine which pending entries to activate
    to_activate: list[BlockingQueueEntry] = []

    if has_open_blocking:
        # Serial mode — open blocking issues exist
        first = pending[0]
        if first.is_blocking:
            to_activate = [first]
        else:
            # Batch consecutive non-blocking entries up to next blocking
            for entry in pending:
                if entry.is_blocking:
                    break
                to_activate.append(entry)
    else:
        # Concurrent mode — no open blocking issues
        first = pending[0]
        if first.is_blocking:
            to_activate = [first]
        else:
            for entry in pending:
                if entry.is_blocking:
                    break
                to_activate.append(entry)

    if not to_activate:
        return []

    # Determine base branch for activation
    base_branch = _resolve_base_branch(open_blocking)
    source_issue = open_blocking[0].issue_number if open_blocking else None

    # Activate each entry
    activated: list[BlockingQueueEntry] = []
    for entry in to_activate:
        updated = await _mark_active_unlocked(
            repo_key,
            entry.issue_number,
            parent_branch=base_branch,
            blocking_source_issue=source_issue,
        )
        if updated:
            activated.append(updated)

    if activated:
        logger.info(
            "Activated %d issue(s) for %s: %s (base_branch=%s)",
            len(activated),
            repo_key,
            [e.issue_number for e in activated],
            base_branch,
        )

    return activated


def _resolve_base_branch(open_blocking: list[BlockingQueueEntry]) -> str:
    """Return the oldest open blocking issue's branch, or 'main'.

    Iterates through open blocking entries in order to find one with a valid
    parent_branch set. If the oldest entry's branch is None (e.g. branch was
    deleted or not yet created), falls through to subsequent entries. If no
    open blocking entry has a valid branch, falls back to 'main' with a
    warning log.
    """
    for entry in open_blocking:
        if entry.parent_branch:
            return entry.parent_branch
    if open_blocking:
        logger.warning(
            "No open blocking issue has a valid parent_branch for repo "
            "(oldest blocking issue #%d) — falling back to 'main'",
            open_blocking[0].issue_number,
        )
    return "main"


async def _mark_active_unlocked(
    repo_key: str,
    issue_number: int,
    parent_branch: str,
    blocking_source_issue: int | None = None,
) -> BlockingQueueEntry | None:
    """Mark an entry as active (internal, no lock)."""
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return await store.update_status(
        repo_key,
        issue_number,
        queue_status=BlockingQueueStatus.ACTIVE,
        parent_branch=parent_branch,
        blocking_source_issue=blocking_source_issue,
        activated_at=now,
    )


async def mark_active(
    repo_key: str,
    issue_number: int,
    parent_branch: str,
    blocking_source_issue: int | None = None,
) -> BlockingQueueEntry | None:
    """Mark an entry as active with the given parent branch."""
    lock = _get_lock(repo_key)
    async with lock:
        return await _mark_active_unlocked(
            repo_key, issue_number, parent_branch, blocking_source_issue
        )


async def mark_in_review(repo_key: str, issue_number: int) -> list[BlockingQueueEntry]:
    """Mark an entry as in_review and activate next pending issues.

    Handles edge cases:
    - Issues not in the queue (returns empty list)
    - Issues not in active state (logs debug, returns empty list)

    Returns list of newly activated entries for agent assignment.
    """
    lock = _get_lock(repo_key)
    async with lock:
        entry = await store.get_by_issue(repo_key, issue_number)
        if not entry:
            logger.debug(
                "Issue #%d not in blocking queue for %s, skipping mark_in_review",
                issue_number,
                repo_key,
            )
            return []

        if entry.queue_status != BlockingQueueStatus.ACTIVE:
            logger.debug(
                "Issue #%d not active in %s queue (status=%s), skipping mark_in_review",
                issue_number,
                repo_key,
                entry.queue_status,
            )
            return []

        await store.update_status(
            repo_key, issue_number, queue_status=BlockingQueueStatus.IN_REVIEW
        )
        logger.info("Issue #%d marked in_review for %s", issue_number, repo_key)

        activated = await _try_activate_next_unlocked(repo_key)

        # Broadcast WebSocket event for queue state change
        if activated:
            await _broadcast_queue_update(
                entry.project_id, repo_key,
                activated_issues=[e.issue_number for e in activated],
                completed_issues=[],
            )

        return activated


async def mark_completed(repo_key: str, issue_number: int) -> list[BlockingQueueEntry]:
    """Mark an entry as completed and activate next pending issues.

    Handles edge cases:
    - Issues not in the queue (returns empty list)
    - Issues already completed (idempotent — returns empty list)
    - Issues in any non-completed state (pending, active, in_review) are all
      transitioned to completed (supports manually closed issues detected during polling)

    Returns list of newly activated entries for agent assignment.
    """
    lock = _get_lock(repo_key)
    async with lock:
        entry = await store.get_by_issue(repo_key, issue_number)
        if not entry:
            logger.debug(
                "Issue #%d not in blocking queue for %s — ignoring mark_completed",
                issue_number,
                repo_key,
            )
            return []

        if entry.queue_status == BlockingQueueStatus.COMPLETED:
            logger.debug(
                "Issue #%d already completed for %s — idempotent skip",
                issue_number,
                repo_key,
            )
            return []

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        await store.update_status(
            repo_key,
            issue_number,
            queue_status=BlockingQueueStatus.COMPLETED,
            completed_at=now,
        )
        logger.info("Issue #%d marked completed for %s", issue_number, repo_key)

        activated = await _try_activate_next_unlocked(repo_key)

        # Broadcast WebSocket event for queue state change
        await _broadcast_queue_update(
            entry.project_id, repo_key,
            activated_issues=[e.issue_number for e in activated],
            completed_issues=[issue_number],
        )

        return activated


async def get_base_ref_for_issue(repo_key: str, issue_number: int) -> str:
    """Return the correct base branch for this issue.

    If there's an oldest open blocking issue with a branch, use that.
    Otherwise return 'main'.
    """
    open_blocking = await store.get_open_blocking(repo_key)
    return _resolve_base_branch(open_blocking)


async def get_current_base_branch(repo_key: str) -> str:
    """Return the current base branch for the repo's blocking queue."""
    open_blocking = await store.get_open_blocking(repo_key)
    return _resolve_base_branch(open_blocking)


async def has_open_blocking_issues(repo_key: str) -> bool:
    """Quick boolean check for whether the repo has open blocking issues."""
    open_blocking = await store.get_open_blocking(repo_key)
    return len(open_blocking) > 0


async def recover_all_repos() -> None:
    """Startup recovery: call try_activate_next for all repos with non-completed entries.

    This catches any pending issues that should have been activated during downtime.
    """
    repos = await store.get_repos_with_non_completed()
    if not repos:
        return

    logger.info("Blocking queue startup recovery: checking %d repo(s)", len(repos))
    for repo_key in repos:
        try:
            activated = await try_activate_next(repo_key)
            if activated:
                logger.info(
                    "Recovery activated %d issue(s) for %s: %s",
                    len(activated),
                    repo_key,
                    [e.issue_number for e in activated],
                )
        except Exception:
            logger.exception("Recovery failed for repo %s", repo_key)


async def _broadcast_queue_update(
    project_id: str,
    repo_key: str,
    activated_issues: list[int],
    completed_issues: list[int],
) -> None:
    """Broadcast a blocking_queue_updated WebSocket event."""
    try:
        from src.services.websocket import connection_manager

        current_base = await get_current_base_branch(repo_key)
        await connection_manager.broadcast_to_project(
            project_id,
            {
                "type": "blocking_queue_updated",
                "repo_key": repo_key,
                "activated_issues": activated_issues,
                "completed_issues": completed_issues,
                "current_base_branch": current_base,
            },
        )
    except Exception:
        logger.debug("Failed to broadcast blocking_queue_updated event")
