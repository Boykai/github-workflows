"""Integration test: pipeline with blocking=True creates all issues as blocking.

T034 — Verifies pipeline-level blocking flag propagation:
- All issues created by a blocking pipeline are enqueued as blocking
- Blocking pipeline issues enforce serial activation
- Mixed pipelines (some blocking, some non-blocking) work correctly
- Branch ancestry follows the oldest open blocking issue's branch
"""

from __future__ import annotations

from unittest.mock import patch

import aiosqlite
import pytest

from src.models.blocking import BlockingQueueStatus
from src.services import blocking_queue as bq
from src.services import blocking_queue_store as store

REPO = "test-owner/test-repo"
PROJECT = "PVT_pipeline_test"


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


class TestPipelineBlockingFlag:
    """Integration tests for pipeline-level blocking flag."""

    @pytest.mark.asyncio
    async def test_all_pipeline_issues_enqueued_as_blocking(self, db):
        """When pipeline.blocking=True, every issue it creates is enqueued as blocking."""
        # Simulate a blocking pipeline creating 3 issues
        pipeline_blocking = True
        for issue_num in [100, 101, 102]:
            entry, activated = await bq.enqueue_issue(
                REPO, issue_num, PROJECT, is_blocking=pipeline_blocking
            )
            assert entry.is_blocking is True

        # Only first should be active (serial activation)
        e100 = await store.get_by_issue(REPO, 100)
        e101 = await store.get_by_issue(REPO, 101)
        e102 = await store.get_by_issue(REPO, 102)
        assert e100 is not None and e100.queue_status == BlockingQueueStatus.ACTIVE
        assert e101 is not None and e101.queue_status == BlockingQueueStatus.PENDING
        assert e102 is not None and e102.queue_status == BlockingQueueStatus.PENDING

    @pytest.mark.asyncio
    async def test_blocking_pipeline_serial_activation(self, db):
        """Blocking pipeline issues activate one at a time (serial)."""
        # Create 3 blocking issues from pipeline
        for issue_num in [100, 101, 102]:
            await bq.enqueue_issue(REPO, issue_num, PROJECT, is_blocking=True)

        await store.update_status(REPO, 100, queue_status="active", parent_branch="copilot/issue-100")

        # #100 → in_review → #101 activates alone (blocking)
        activated = await bq.mark_in_review(REPO, 100)
        assert len(activated) == 1
        assert activated[0].issue_number == 101
        assert activated[0].parent_branch == "copilot/issue-100"

        await store.update_status(REPO, 101, queue_status="active", parent_branch="copilot/issue-101")

        # #101 → in_review → #102 activates alone (blocking)
        activated2 = await bq.mark_in_review(REPO, 101)
        assert len(activated2) == 1
        assert activated2[0].issue_number == 102

    @pytest.mark.asyncio
    async def test_mixed_pipelines(self, db):
        """Issues from blocking and non-blocking pipelines coexist correctly."""
        # Blocking pipeline creates #100
        await bq.enqueue_issue(REPO, 100, PROJECT, is_blocking=True)
        await store.update_status(REPO, 100, queue_status="active", parent_branch="copilot/issue-100")

        # Non-blocking pipeline creates #200, #201
        e200, act200 = await bq.enqueue_issue(REPO, 200, PROJECT, is_blocking=False)
        e201, act201 = await bq.enqueue_issue(REPO, 201, PROJECT, is_blocking=False)
        assert act200 is False  # blocked by #100
        assert act201 is False  # blocked by #100

        # #100 → in_review: #200 and #201 are consecutive non-blocking → batch activate
        activated = await bq.mark_in_review(REPO, 100)
        assert len(activated) == 2
        assert [e.issue_number for e in activated] == [200, 201]
        # Both branch from #100's branch
        assert activated[0].parent_branch == "copilot/issue-100"
        assert activated[1].parent_branch == "copilot/issue-100"

    @pytest.mark.asyncio
    async def test_blocking_pipeline_branch_ancestry(self, db):
        """Issues from a blocking pipeline branch from the oldest open blocking issue's branch."""
        # Issue #100 activates from main
        entry, _ = await bq.enqueue_issue(REPO, 100, PROJECT, is_blocking=True)
        assert entry.parent_branch == "main"

        # Simulate branch creation
        await store.update_status(REPO, 100, queue_status="active", parent_branch="copilot/issue-100")

        # Issues #101, #102 are created and pending
        await bq.enqueue_issue(REPO, 101, PROJECT, is_blocking=True)
        await bq.enqueue_issue(REPO, 102, PROJECT, is_blocking=True)

        # #100 → in_review → #101 activates from #100's branch
        activated = await bq.mark_in_review(REPO, 100)
        assert len(activated) == 1
        assert activated[0].issue_number == 101
        assert activated[0].parent_branch == "copilot/issue-100"
        assert activated[0].blocking_source_issue == 100

    @pytest.mark.asyncio
    async def test_non_blocking_pipeline_no_serialization(self, db):
        """Non-blocking pipeline issues don't serialize — they activate concurrently."""
        # All non-blocking
        for issue_num in [100, 101, 102]:
            await store.insert(REPO, issue_num, PROJECT, is_blocking=False)

        # Activate all at once
        activated = await bq.try_activate_next(REPO)
        assert len(activated) == 3
        assert all(e.queue_status == BlockingQueueStatus.ACTIVE for e in activated)
        assert all(e.parent_branch == "main" for e in activated)

    @pytest.mark.asyncio
    async def test_completion_returns_to_main(self, db):
        """After all blocking pipeline issues complete, branching returns to main."""
        # Create and complete two blocking issues
        await bq.enqueue_issue(REPO, 100, PROJECT, is_blocking=True)
        await bq.mark_in_review(REPO, 100)

        activated = await bq.mark_in_review(REPO, 100)  # Already in_review
        # Actually need to enqueue #101 first, then complete both
        await bq.enqueue_issue(REPO, 101, PROJECT, is_blocking=True)

        await bq.mark_completed(REPO, 100)
        # #101 should now be active
        e101 = await store.get_by_issue(REPO, 101)
        assert e101 is not None and e101.queue_status == BlockingQueueStatus.ACTIVE

        await bq.mark_in_review(REPO, 101)
        await bq.mark_completed(REPO, 101)

        # All done — base branch returns to main
        base = await bq.get_current_base_branch(REPO)
        assert base == "main"
        assert await bq.has_open_blocking_issues(REPO) is False
