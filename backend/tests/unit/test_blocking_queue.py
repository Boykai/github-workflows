"""Unit tests for the blocking queue state machine.

Tests the 8-issue mixed scenario: creation order, activation order, batch rules,
and completion cascades — verifying serial activation, concurrent non-blocking
activation, and branch ancestry resolution.
"""

from __future__ import annotations

from unittest.mock import patch

import aiosqlite
import pytest

from src.models.blocking import BlockingQueueStatus
from src.services import blocking_queue as bq
from src.services import blocking_queue_store as store

REPO = "owner/repo"
PROJECT = "PVT_test"


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


# ─── Helper ──────────────────────────────────────────────────────────


async def _enqueue(issue: int, blocking: bool, db_conn) -> tuple:
    """Enqueue an issue and return (entry, activated)."""
    return await bq.enqueue_issue(REPO, issue, PROJECT, blocking)


async def _status(issue: int) -> str:
    """Get queue status for an issue."""
    entry = await store.get_by_issue(REPO, issue)
    assert entry is not None, f"Issue #{issue} not in queue"
    return entry.queue_status


# ─── Basic Tests ─────────────────────────────────────────────────────


class TestEnqueue:
    """Tests for enqueue_issue."""

    @pytest.mark.asyncio
    async def test_enqueue_non_blocking_no_queue(self, db):
        """Non-blocking issue with empty queue activates immediately."""
        entry, activated = await _enqueue(1, blocking=False, db_conn=db)
        assert activated is True
        assert entry.queue_status == BlockingQueueStatus.ACTIVE
        assert entry.parent_branch == "main"

    @pytest.mark.asyncio
    async def test_enqueue_blocking_empty_queue(self, db):
        """First blocking issue activates immediately with main as base."""
        entry, activated = await _enqueue(1, blocking=True, db_conn=db)
        assert activated is True
        assert entry.queue_status == BlockingQueueStatus.ACTIVE
        assert entry.parent_branch == "main"

    @pytest.mark.asyncio
    async def test_enqueue_while_blocking_active(self, db):
        """Issue enqueued while a blocking issue is active stays pending."""
        await _enqueue(1, blocking=True, db_conn=db)
        entry, activated = await _enqueue(2, blocking=False, db_conn=db)
        assert activated is False
        assert entry.queue_status == BlockingQueueStatus.PENDING

    @pytest.mark.asyncio
    async def test_duplicate_enqueue(self, db):
        """Duplicate enqueue returns existing entry."""
        await _enqueue(1, blocking=True, db_conn=db)
        entry, activated = await _enqueue(1, blocking=True, db_conn=db)
        assert entry.issue_number == 1
        assert activated is True


class TestActivation:
    """Tests for try_activate_next."""

    @pytest.mark.asyncio
    async def test_no_pending(self, db):
        """No pending entries → no activation."""
        activated = await bq.try_activate_next(REPO)
        assert activated == []

    @pytest.mark.asyncio
    async def test_non_blocking_concurrent(self, db):
        """Multiple non-blocking issues with no blocking issues activate together."""
        # Manually insert as pending
        for i in range(1, 4):
            await store.insert(REPO, i, PROJECT, is_blocking=False)

        activated = await bq.try_activate_next(REPO)
        assert len(activated) == 3
        for e in activated:
            assert e.queue_status == BlockingQueueStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_blocking_activates_alone(self, db):
        """A blocking issue at the front activates alone."""
        await store.insert(REPO, 1, PROJECT, is_blocking=True)
        await store.insert(REPO, 2, PROJECT, is_blocking=False)

        activated = await bq.try_activate_next(REPO)
        assert len(activated) == 1
        assert activated[0].issue_number == 1

    @pytest.mark.asyncio
    async def test_non_blocking_batch_up_to_blocking(self, db):
        """Non-blocking issues activate together up to the next blocking entry."""
        await store.insert(REPO, 1, PROJECT, is_blocking=False)
        await store.insert(REPO, 2, PROJECT, is_blocking=False)
        await store.insert(REPO, 3, PROJECT, is_blocking=True)
        await store.insert(REPO, 4, PROJECT, is_blocking=False)

        activated = await bq.try_activate_next(REPO)
        assert len(activated) == 2
        assert [e.issue_number for e in activated] == [1, 2]


class TestMarkInReview:
    """Tests for mark_in_review."""

    @pytest.mark.asyncio
    async def test_mark_in_review_triggers_next(self, db):
        """Moving active issue to in_review triggers next activation."""
        await _enqueue(1, blocking=True, db_conn=db)
        await store.insert(REPO, 2, PROJECT, is_blocking=False)

        activated = await bq.mark_in_review(REPO, 1)
        assert await _status(1) == BlockingQueueStatus.IN_REVIEW
        assert len(activated) == 1
        assert activated[0].issue_number == 2


class TestMarkCompleted:
    """Tests for mark_completed."""

    @pytest.mark.asyncio
    async def test_mark_completed_triggers_next(self, db):
        """Completing an issue triggers next activation."""
        await _enqueue(1, blocking=True, db_conn=db)
        await store.insert(REPO, 2, PROJECT, is_blocking=True)

        # Move #1 to in_review first
        await bq.mark_in_review(REPO, 1)
        # #2 activates
        assert await _status(2) == BlockingQueueStatus.ACTIVE

        # Now #2 to in_review
        await bq.mark_in_review(REPO, 2)

        # Complete #1
        activated = await bq.mark_completed(REPO, 1)
        assert await _status(1) == BlockingQueueStatus.COMPLETED
        # No more pending to activate
        assert activated == []


class TestBaseRef:
    """Tests for get_base_ref_for_issue."""

    @pytest.mark.asyncio
    async def test_no_blocking_returns_main(self, db):
        """With no open blocking issues, base ref is 'main'."""
        ref = await bq.get_base_ref_for_issue(REPO, 1)
        assert ref == "main"

    @pytest.mark.asyncio
    async def test_blocking_returns_branch(self, db):
        """With an open blocking issue, base ref is that issue's branch."""
        entry, _ = await _enqueue(1, blocking=True, db_conn=db)
        # Simulate the branch being set (orchestrator would do this)
        await store.update_status(REPO, 1, queue_status="active", parent_branch="copilot/issue-1")

        ref = await bq.get_base_ref_for_issue(REPO, 2)
        assert ref == "copilot/issue-1"


class TestHasOpenBlocking:
    """Tests for has_open_blocking_issues."""

    @pytest.mark.asyncio
    async def test_no_blocking(self, db):
        """Returns False when no blocking issues open."""
        assert await bq.has_open_blocking_issues(REPO) is False

    @pytest.mark.asyncio
    async def test_with_blocking(self, db):
        """Returns True when blocking issues are active."""
        await _enqueue(1, blocking=True, db_conn=db)
        assert await bq.has_open_blocking_issues(REPO) is True


# ─── Full 8-Issue Scenario ──────────────────────────────────────────


class TestEightIssueScenario:
    """Full 8-issue mixed blocking/non-blocking scenario from the spec.

    Queue (creation order):
      1. Issue #1 — blocking
      2. Issue #2 — non-blocking
      3. Issue #3 — non-blocking
      4. Issue #4 — blocking
      5. Issue #5 — non-blocking
      6. Issue #6 — blocking
      7. Issue #7 — non-blocking
      8. Issue #8 — non-blocking
    """

    @pytest.mark.asyncio
    async def test_full_scenario(self, db):
        """Validate the complete 8-issue activation cascade."""

        # Step 1: Issue #1 created (blocking) → activates immediately from "main"
        entry1, activated1 = await _enqueue(1, blocking=True, db_conn=db)
        assert activated1 is True
        assert entry1.queue_status == BlockingQueueStatus.ACTIVE
        assert entry1.parent_branch == "main"

        # Simulate orchestrator setting the branch name
        await store.update_status(REPO, 1, queue_status="active", parent_branch="copilot/issue-1")

        # Step 2: Issues #2-#8 created while #1 is active → all pending
        for issue_num, blocking in [
            (2, False), (3, False), (4, True),
            (5, False), (6, True), (7, False), (8, False),
        ]:
            entry, activated = await _enqueue(issue_num, blocking, db_conn=db)
            assert activated is False, f"Issue #{issue_num} should be pending"
            assert entry.queue_status == BlockingQueueStatus.PENDING

        # Step 3: Issue #1 → "in review"
        # Should activate #2 and #3 (consecutive non-blocking, stop at #4 blocking)
        activated = await bq.mark_in_review(REPO, 1)
        assert len(activated) == 2
        assert [e.issue_number for e in activated] == [2, 3]
        # #2 and #3 branch from #1's branch
        assert activated[0].parent_branch == "copilot/issue-1"
        assert activated[1].parent_branch == "copilot/issue-1"

        assert await _status(1) == BlockingQueueStatus.IN_REVIEW
        assert await _status(2) == BlockingQueueStatus.ACTIVE
        assert await _status(3) == BlockingQueueStatus.ACTIVE
        assert await _status(4) == BlockingQueueStatus.PENDING

        # Step 4: Issues #2 and #3 → "in review"
        # #2 → in_review: #3 still active, so no new activations
        activated_2 = await bq.mark_in_review(REPO, 2)
        assert activated_2 == []  # #3 is still active

        # #3 → in_review: no more active, next is #4 (blocking) → activate alone
        activated_3 = await bq.mark_in_review(REPO, 3)
        assert len(activated_3) == 1
        assert activated_3[0].issue_number == 4
        assert activated_3[0].parent_branch == "copilot/issue-1"  # #1 is still oldest open blocking

        assert await _status(4) == BlockingQueueStatus.ACTIVE

        # Step 5: Issue #1 → "completed"
        # #4 is active (blocking) → can't activate more
        activated_1c = await bq.mark_completed(REPO, 1)
        assert activated_1c == []
        assert await _status(1) == BlockingQueueStatus.COMPLETED

        # Simulate orchestrator setting #4's branch
        await store.update_status(REPO, 4, queue_status="active", parent_branch="copilot/issue-4")

        # Step 6: Issues #2, #3 → "completed", #4 → "in review"
        await bq.mark_completed(REPO, 2)
        await bq.mark_completed(REPO, 3)

        # #4 → in_review: next is #5 (non-blocking, only one before #6 blocking)
        activated_4r = await bq.mark_in_review(REPO, 4)
        assert len(activated_4r) == 1
        assert activated_4r[0].issue_number == 5
        assert activated_4r[0].parent_branch == "copilot/issue-4"  # #4 is oldest open blocking

        # Step 7: #5 → "in review"
        # Next pending is #6 (blocking) → activate alone
        activated_5r = await bq.mark_in_review(REPO, 5)
        assert len(activated_5r) == 1
        assert activated_5r[0].issue_number == 6
        assert activated_5r[0].parent_branch == "copilot/issue-4"  # #4 still oldest open blocking

        # Step 8: #4 → "completed"
        # #6 is active (blocking) → can't activate more
        activated_4c = await bq.mark_completed(REPO, 4)
        assert activated_4c == []

        # Simulate orchestrator setting #6's branch
        await store.update_status(REPO, 6, queue_status="active", parent_branch="copilot/issue-6")

        # Step 9: #5 → "completed", #6 → "in review"
        await bq.mark_completed(REPO, 5)

        activated_6r = await bq.mark_in_review(REPO, 6)
        # Next pending is #7 (non-blocking), then #8 (non-blocking) → activate both
        assert len(activated_6r) == 2
        assert [e.issue_number for e in activated_6r] == [7, 8]
        assert activated_6r[0].parent_branch == "copilot/issue-6"
        assert activated_6r[1].parent_branch == "copilot/issue-6"

        # Step 10: All complete
        await bq.mark_completed(REPO, 6)
        await bq.mark_completed(REPO, 7)
        await bq.mark_completed(REPO, 8)

        # Verify all completed
        for i in range(1, 9):
            assert await _status(i) == BlockingQueueStatus.COMPLETED

        # Future issues branch from "main"
        ref = await bq.get_base_ref_for_issue(REPO, 9)
        assert ref == "main"
        assert await bq.has_open_blocking_issues(REPO) is False


class TestEdgeCases:
    """Tests for edge case handling."""

    @pytest.mark.asyncio
    async def test_mark_completed_unknown_issue(self, db):
        """Completing an issue not in the queue returns empty list."""
        activated = await bq.mark_completed(REPO, 999)
        assert activated == []

    @pytest.mark.asyncio
    async def test_mark_completed_already_completed(self, db):
        """Completing an already-completed issue is idempotent."""
        await _enqueue(1, blocking=True, db_conn=db)
        await bq.mark_in_review(REPO, 1)
        await bq.mark_completed(REPO, 1)

        # Second call should be idempotent
        activated = await bq.mark_completed(REPO, 1)
        assert activated == []
        assert await _status(1) == BlockingQueueStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_mark_completed_from_pending(self, db):
        """Completing a pending issue (manually closed) transitions correctly."""
        await _enqueue(1, blocking=True, db_conn=db)
        await store.insert(REPO, 2, PROJECT, is_blocking=False)  # pending

        # Manually close #2 while it's still pending
        activated = await bq.mark_completed(REPO, 2)
        assert await _status(2) == BlockingQueueStatus.COMPLETED
        # #1 is still active, so no new activations triggered
        assert activated == []

    @pytest.mark.asyncio
    async def test_mark_in_review_unknown_issue(self, db):
        """Reviewing an issue not in the queue returns empty list."""
        activated = await bq.mark_in_review(REPO, 999)
        assert activated == []

    @pytest.mark.asyncio
    async def test_mark_in_review_pending_issue(self, db):
        """Reviewing a pending issue (not yet active) returns empty list."""
        await _enqueue(1, blocking=True, db_conn=db)
        await store.insert(REPO, 2, PROJECT, is_blocking=False)  # pending

        activated = await bq.mark_in_review(REPO, 2)
        assert activated == []
        # #2 should still be pending (not transitioned)
        assert await _status(2) == BlockingQueueStatus.PENDING

    @pytest.mark.asyncio
    async def test_deleted_branch_fallback(self, db):
        """When a blocking issue's branch is None, fall back to 'main'."""
        # Create a blocking issue but don't set its branch (simulates deleted branch)
        await _enqueue(1, blocking=True, db_conn=db)
        # Note: entry is active with parent_branch='main' from activation
        # Clear the parent_branch to simulate deletion
        await store.update_status(REPO, 1, queue_status="active", parent_branch=None)

        ref = await bq.get_base_ref_for_issue(REPO, 2)
        assert ref == "main"


class TestRecovery:
    """Tests for startup recovery."""

    @pytest.mark.asyncio
    async def test_recover_activates_pending(self, db):
        """Recovery should activate pending issues that were stuck."""
        # Simulate: one issue stuck in pending (e.g., container restart
        # after in_review transition but before activation cascade)
        await store.insert(REPO, 1, PROJECT, is_blocking=False)

        await bq.recover_all_repos()

        entry = await store.get_by_issue(REPO, 1)
        assert entry is not None
        assert entry.queue_status == BlockingQueueStatus.ACTIVE
