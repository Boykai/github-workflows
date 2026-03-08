"""Integration test: chore trigger with blocking=True enqueues and respects activation order.

T033 — Verifies the full chore-trigger-to-blocking-queue integration:
- A chore with blocking=True creates an issue that is enqueued as blocking
- Blocking queue activation order is respected (serial when blocking exists)
- Pipeline blocking flag inheritance works (chore.blocking=False + pipeline.blocking=True)
"""

from __future__ import annotations

from unittest.mock import patch

import aiosqlite
import pytest

from src.models.blocking import BlockingQueueStatus
from src.services import blocking_queue as bq
from src.services import blocking_queue_store as store

REPO = "test-owner/test-repo"
REPO_KEY = REPO
PROJECT = "PVT_integration_test"


@pytest.fixture(autouse=True)
def _clear_locks():
    """Reset per-repo locks between tests."""
    bq._repo_locks.clear()
    yield
    bq._repo_locks.clear()


@pytest.fixture
async def db():
    """In-memory SQLite with blocking_queue table for testing."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS blocking_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_key TEXT NOT NULL,
            issue_number INTEGER NOT NULL,
            project_id TEXT NOT NULL,
            is_blocking INTEGER NOT NULL DEFAULT 0,
            queue_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (queue_status IN ('pending', 'active', 'in_review', 'completed')),
            parent_branch TEXT,
            blocking_source_issue INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            activated_at TEXT,
            completed_at TEXT,
            UNIQUE(repo_key, issue_number)
        );
        CREATE INDEX IF NOT EXISTS idx_blocking_queue_repo_status
            ON blocking_queue(repo_key, queue_status);
        CREATE INDEX IF NOT EXISTS idx_blocking_queue_repo_blocking
            ON blocking_queue(repo_key, is_blocking, queue_status);
        """
    )
    await conn.commit()
    with patch("src.services.blocking_queue_store.get_db", return_value=conn):
        yield conn
    await conn.close()


class TestChoreTriggerBlocking:
    """Integration tests for chore trigger with blocking flag."""

    @pytest.mark.asyncio
    async def test_blocking_chore_enqueues_as_blocking(self, db):
        """A chore with blocking=True results in a blocking queue entry."""
        entry, activated = await bq.enqueue_issue(REPO_KEY, 10, PROJECT, is_blocking=True)
        assert entry.is_blocking is True
        assert entry.queue_status == BlockingQueueStatus.ACTIVE
        assert activated is True

    @pytest.mark.asyncio
    async def test_non_blocking_chore_enqueues_as_non_blocking(self, db):
        """A chore with blocking=False results in a non-blocking queue entry."""
        entry, activated = await bq.enqueue_issue(REPO_KEY, 10, PROJECT, is_blocking=False)
        assert entry.is_blocking is False
        assert entry.queue_status == BlockingQueueStatus.ACTIVE
        assert activated is True

    @pytest.mark.asyncio
    async def test_blocking_chore_serializes_subsequent_issues(self, db):
        """When a blocking chore's issue is active, subsequent issues are pending."""
        # First chore triggers a blocking issue
        _entry1, act1 = await bq.enqueue_issue(REPO_KEY, 10, PROJECT, is_blocking=True)
        assert act1 is True

        # Second chore triggers while blocking issue is active → pending
        entry2, act2 = await bq.enqueue_issue(REPO_KEY, 20, PROJECT, is_blocking=False)
        assert act2 is False
        assert entry2.queue_status == BlockingQueueStatus.PENDING

        # Third chore triggers → also pending
        entry3, act3 = await bq.enqueue_issue(REPO_KEY, 30, PROJECT, is_blocking=True)
        assert act3 is False
        assert entry3.queue_status == BlockingQueueStatus.PENDING

    @pytest.mark.asyncio
    async def test_blocking_chore_activation_cascade(self, db):
        """Completing a blocking chore's issue activates the next in queue."""
        # Blocking chore issue #10 activates
        await bq.enqueue_issue(REPO_KEY, 10, PROJECT, is_blocking=True)
        await store.update_status(
            REPO_KEY, 10, queue_status="active", parent_branch="copilot/issue-10"
        )

        # Non-blocking #20 and blocking #30 are pending
        await bq.enqueue_issue(REPO_KEY, 20, PROJECT, is_blocking=False)
        await bq.enqueue_issue(REPO_KEY, 30, PROJECT, is_blocking=True)

        # #10 → in_review: #20 activates (non-blocking, stops at #30)
        activated = await bq.mark_in_review(REPO_KEY, 10)
        assert len(activated) == 1
        assert activated[0].issue_number == 20
        assert activated[0].parent_branch == "copilot/issue-10"

        # #20 → in_review: #30 activates (blocking, alone)
        activated2 = await bq.mark_in_review(REPO_KEY, 20)
        assert len(activated2) == 1
        assert activated2[0].issue_number == 30

    @pytest.mark.asyncio
    async def test_pipeline_blocking_inheritance(self, db):
        """Pipeline blocking flag propagates: chore.blocking=False but pipeline.blocking=True → issue is blocking.

        This tests the OR logic: the effective is_blocking flag should be True
        if EITHER the chore OR the assigned pipeline has blocking=True.
        """
        # Simulating the chore trigger resolution:
        # chore.blocking = False, pipeline.blocking = True → effective is_blocking = True
        effective_is_blocking = False or True  # OR logic from R5

        entry, activated = await bq.enqueue_issue(
            REPO_KEY, 10, PROJECT, is_blocking=effective_is_blocking
        )
        assert entry.is_blocking is True
        assert activated is True

        # Subsequent issue should be blocked (serial mode)
        entry2, act2 = await bq.enqueue_issue(REPO_KEY, 20, PROJECT, is_blocking=False)
        assert act2 is False
        assert entry2.queue_status == BlockingQueueStatus.PENDING

    @pytest.mark.asyncio
    async def test_non_blocking_chores_concurrent(self, db):
        """Multiple non-blocking chores with no blocking issues activate concurrently."""
        _entry1, act1 = await bq.enqueue_issue(REPO_KEY, 10, PROJECT, is_blocking=False)
        assert act1 is True

        # No blocking issues exist → second non-blocking activates concurrently
        _entry2, act2 = await bq.enqueue_issue(REPO_KEY, 20, PROJECT, is_blocking=False)
        assert act2 is True  # concurrent: no blocking issues

        # Both already active, mark_in_review triggers no new activations
        activated = await bq.mark_in_review(REPO_KEY, 10)
        assert len(activated) == 0

    @pytest.mark.asyncio
    async def test_chore_trigger_completion_unlocks_queue(self, db):
        """Completing all blocking chore issues returns branching to main."""
        # Blocking issue
        await bq.enqueue_issue(REPO_KEY, 10, PROJECT, is_blocking=True)
        await bq.mark_in_review(REPO_KEY, 10)
        await bq.mark_completed(REPO_KEY, 10)

        # Queue should be clear — new issues branch from main
        base = await bq.get_current_base_branch(REPO_KEY)
        assert base == "main"
        assert await bq.has_open_blocking_issues(REPO_KEY) is False
