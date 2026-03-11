"""Unit tests for the blocking queue state machine.

Tests the 8-issue mixed scenario: creation order, activation order, batch rules,
and completion cascades — verifying serial activation, concurrent non-blocking
activation, and branch ancestry resolution.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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

    @pytest.mark.asyncio
    async def test_enqueue_concurrent_non_blocking(self, db):
        """Non-blocking issues activate concurrently when no blocking issues exist."""
        entry1, act1 = await _enqueue(1, blocking=False, db_conn=db)
        assert act1 is True
        assert entry1.queue_status == BlockingQueueStatus.ACTIVE

        # Second non-blocking should also activate (concurrent mode)
        entry2, act2 = await _enqueue(2, blocking=False, db_conn=db)
        assert act2 is True
        assert entry2.queue_status == BlockingQueueStatus.ACTIVE

        # Third non-blocking should also activate
        entry3, act3 = await _enqueue(3, blocking=False, db_conn=db)
        assert act3 is True
        assert entry3.queue_status == BlockingQueueStatus.ACTIVE


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
        """Non-blocking issues activate together up to and including the next blocking entry."""
        await store.insert(REPO, 1, PROJECT, is_blocking=False)
        await store.insert(REPO, 2, PROJECT, is_blocking=False)
        await store.insert(REPO, 3, PROJECT, is_blocking=True)
        await store.insert(REPO, 4, PROJECT, is_blocking=False)

        activated = await bq.try_activate_next(REPO)
        assert len(activated) == 3
        assert [e.issue_number for e in activated] == [1, 2, 3]


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
        _entry, _ = await _enqueue(1, blocking=True, db_conn=db)
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
            (2, False),
            (3, False),
            (4, True),
            (5, False),
            (6, True),
            (7, False),
            (8, False),
        ]:
            entry, activated = await _enqueue(issue_num, blocking, db_conn=db)
            assert activated is False, f"Issue #{issue_num} should be pending"
            assert entry.queue_status == BlockingQueueStatus.PENDING

        # Step 3: Issue #1 → "in review"
        # Should activate #2, #3, and #4 (consecutive non-blocking + first blocking)
        activated = await bq.mark_in_review(REPO, 1)
        assert len(activated) == 3
        assert [e.issue_number for e in activated] == [2, 3, 4]
        # #2, #3, #4 branch from #1's branch
        assert activated[0].parent_branch == "copilot/issue-1"
        assert activated[1].parent_branch == "copilot/issue-1"
        assert activated[2].parent_branch == "copilot/issue-1"

        assert await _status(1) == BlockingQueueStatus.IN_REVIEW
        assert await _status(2) == BlockingQueueStatus.ACTIVE
        assert await _status(3) == BlockingQueueStatus.ACTIVE
        assert await _status(4) == BlockingQueueStatus.ACTIVE
        assert await _status(5) == BlockingQueueStatus.PENDING

        # Step 4: Issues #2 and #3 → "in review"
        # #4 is active blocking → no new activations
        activated_2 = await bq.mark_in_review(REPO, 2)
        assert activated_2 == []

        activated_3 = await bq.mark_in_review(REPO, 3)
        assert activated_3 == []

        # Simulate orchestrator setting #4's branch
        await store.update_status(REPO, 4, queue_status="active", parent_branch="copilot/issue-4")

        # Step 5: Issue #1 → "completed"
        # #4 is active (blocking) → can't activate more
        activated_1c = await bq.mark_completed(REPO, 1)
        assert activated_1c == []
        assert await _status(1) == BlockingQueueStatus.COMPLETED

        # Step 6: Issues #2, #3 → "completed", #4 → "in review"
        await bq.mark_completed(REPO, 2)
        await bq.mark_completed(REPO, 3)

        # #4 → in_review: next is #5 (non-blocking), then #6 (blocking) → activate [5, 6]
        activated_4r = await bq.mark_in_review(REPO, 4)
        assert len(activated_4r) == 2
        assert [e.issue_number for e in activated_4r] == [5, 6]
        assert activated_4r[0].parent_branch == "copilot/issue-4"  # #4 is oldest open blocking
        assert activated_4r[1].parent_branch == "copilot/issue-4"

        # Simulate orchestrator setting #6's branch
        await store.update_status(REPO, 6, queue_status="active", parent_branch="copilot/issue-6")

        # Step 7: #5 → "in review"
        # #6 is active blocking → no new activations
        activated_5r = await bq.mark_in_review(REPO, 5)
        assert activated_5r == []

        # Step 8: #4 → "completed"
        # #6 is active (blocking) → can't activate more
        activated_4c = await bq.mark_completed(REPO, 4)
        assert activated_4c == []

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
        # Clear the parent_branch directly via SQL to simulate branch deletion
        await db.execute(
            "UPDATE blocking_queue SET parent_branch = NULL WHERE repo_key = ? AND issue_number = ?",
            (REPO, 1),
        )
        await db.commit()

        ref = await bq.get_base_ref_for_issue(REPO, 2)
        assert ref == "main"


class TestSweepStaleEntries:
    """Tests for sweep_stale_entries — detect closed/deleted blocking issues."""

    @pytest.mark.asyncio
    async def test_sweep_clears_closed_issue(self, db):
        """A closed/deleted blocking issue is marked completed and queue advances."""
        # Enqueue blocking #1 (activates), then non-blocking #2 (pending)
        await _enqueue(1, blocking=True, db_conn=db)
        await _enqueue(2, blocking=False, db_conn=db)
        assert await _status(1) == BlockingQueueStatus.ACTIVE
        assert await _status(2) == BlockingQueueStatus.PENDING

        # Mock check_issue_closed to report #1 as closed
        mock_svc = AsyncMock()
        mock_svc.check_issue_closed = AsyncMock(return_value=True)
        with patch("src.services.github_projects.github_projects_service", mock_svc):
            swept, activated = await bq.sweep_stale_entries("tok", "owner", "repo")

        assert swept == [1]
        assert len(activated) == 1
        assert activated[0].issue_number == 2
        assert await _status(1) == BlockingQueueStatus.COMPLETED
        # Queue should have advanced: #2 is now active
        assert await _status(2) == BlockingQueueStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_sweep_skips_open_issues(self, db):
        """Open issues are not swept."""
        await _enqueue(1, blocking=True, db_conn=db)
        assert await _status(1) == BlockingQueueStatus.ACTIVE

        mock_svc = AsyncMock()
        mock_svc.check_issue_closed = AsyncMock(return_value=False)
        with patch("src.services.github_projects.github_projects_service", mock_svc):
            swept, activated = await bq.sweep_stale_entries("tok", "owner", "repo")

        assert swept == []
        assert activated == []
        assert await _status(1) == BlockingQueueStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_sweep_no_active_entries(self, db):
        """No-op when there are no active/in_review entries."""
        swept, activated = await bq.sweep_stale_entries("tok", "owner", "repo")
        assert swept == []
        assert activated == []

    @pytest.mark.asyncio
    async def test_sweep_handles_api_error(self, db):
        """API errors for individual issues don't crash the sweep."""
        await _enqueue(1, blocking=True, db_conn=db)

        mock_svc = AsyncMock()
        mock_svc.check_issue_closed = AsyncMock(side_effect=Exception("API error"))
        with patch("src.services.github_projects.github_projects_service", mock_svc):
            swept, activated = await bq.sweep_stale_entries("tok", "owner", "repo")

        assert swept == []
        assert activated == []
        # Entry should still be active (not corrupted)
        assert await _status(1) == BlockingQueueStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_sweep_clears_in_review_entry(self, db):
        """Issues in in_review state are also swept if closed."""
        await _enqueue(1, blocking=True, db_conn=db)
        await bq.mark_in_review(REPO, 1)
        assert await _status(1) == BlockingQueueStatus.IN_REVIEW

        mock_svc = AsyncMock()
        mock_svc.check_issue_closed = AsyncMock(return_value=True)
        with patch("src.services.github_projects.github_projects_service", mock_svc):
            swept, activated = await bq.sweep_stale_entries("tok", "owner", "repo")

        assert swept == [1]
        assert await _status(1) == BlockingQueueStatus.COMPLETED


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


# ─── Skip / Delete Workflow Tests ────────────────────────────────────


class TestSkipWorkflow:
    """Tests for skip (mark_completed) used by the board API delete endpoint."""

    @pytest.mark.asyncio
    async def test_skip_active_blocking_advances_queue(self, db):
        """Skipping the active blocking issue should complete it and activate the next."""
        await _enqueue(10, blocking=True, db_conn=db)
        await _enqueue(20, blocking=False, db_conn=db)
        assert await _status(10) == BlockingQueueStatus.ACTIVE
        assert await _status(20) == BlockingQueueStatus.PENDING

        # Skip issue #10 (what the /delete endpoint does via mark_completed)
        activated = await bq.mark_completed(REPO, 10)

        assert await _status(10) == BlockingQueueStatus.COMPLETED
        assert await _status(20) == BlockingQueueStatus.ACTIVE
        assert len(activated) == 1
        assert activated[0].issue_number == 20

    @pytest.mark.asyncio
    async def test_skip_nonexistent_issue_is_noop(self, db):
        """Skipping an issue not in the queue should return empty list."""
        activated = await bq.mark_completed(REPO, 999)
        assert activated == []

    @pytest.mark.asyncio
    async def test_resolve_entry_by_project(self, db):
        """get_by_project returns entries that can be looked up by issue number."""
        await _enqueue(10, blocking=True, db_conn=db)
        await _enqueue(20, blocking=False, db_conn=db)

        entries = await store.get_by_project(PROJECT)
        assert len(entries) == 2
        match = next((e for e in entries if e.issue_number == 10), None)
        assert match is not None
        assert match.repo_key == REPO

    @pytest.mark.asyncio
    async def test_resolve_entry_missing_issue_not_found(self, db):
        """Looking up a missing issue by project should return no match."""
        await _enqueue(10, blocking=True, db_conn=db)

        entries = await store.get_by_project(PROJECT)
        match = next((e for e in entries if e.issue_number == 999), None)
        assert match is None


# ─── Skip to Non-Blocking Tests ─────────────────────────────────────


class TestSkipToNonBlocking:
    """Tests for skip_to_non_blocking — marks a blocking issue as non-blocking."""

    @pytest.mark.asyncio
    async def test_skip_active_blocking_activates_pending(self, db):
        """Skipping an active blocking issue makes it non-blocking and activates pending."""
        await _enqueue(10, blocking=True, db_conn=db)
        await _enqueue(20, blocking=False, db_conn=db)
        assert await _status(10) == BlockingQueueStatus.ACTIVE
        assert await _status(20) == BlockingQueueStatus.PENDING

        activated = await bq.skip_to_non_blocking(REPO, 10)

        # #10 stays active but is now non-blocking
        entry10 = await store.get_by_issue(REPO, 10)
        assert entry10 is not None
        assert entry10.queue_status == BlockingQueueStatus.ACTIVE
        assert entry10.is_blocking is False

        # #20 is activated
        assert len(activated) == 1
        assert activated[0].issue_number == 20
        assert await _status(20) == BlockingQueueStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_skip_activates_batch_with_next_blocking(self, db):
        """Skipping activates non-blocking entries plus the next blocking entry."""
        await _enqueue(10, blocking=True, db_conn=db)
        await _enqueue(20, blocking=False, db_conn=db)
        await _enqueue(30, blocking=True, db_conn=db)
        await _enqueue(40, blocking=False, db_conn=db)
        assert await _status(10) == BlockingQueueStatus.ACTIVE

        activated = await bq.skip_to_non_blocking(REPO, 10)

        # #10 is non-blocking but still active
        entry10 = await store.get_by_issue(REPO, 10)
        assert entry10 is not None
        assert entry10.is_blocking is False
        assert entry10.queue_status == BlockingQueueStatus.ACTIVE

        # #20 and #30 activate; #40 waits behind #30 (the new blocking gate)
        assert len(activated) == 2
        assert [e.issue_number for e in activated] == [20, 30]
        assert await _status(40) == BlockingQueueStatus.PENDING

    @pytest.mark.asyncio
    async def test_skip_already_non_blocking_returns_empty(self, db):
        """Skipping a non-blocking issue is idempotent and returns empty list."""
        await _enqueue(10, blocking=False, db_conn=db)

        activated = await bq.skip_to_non_blocking(REPO, 10)
        assert activated == []

    @pytest.mark.asyncio
    async def test_skip_unknown_issue_returns_empty(self, db):
        """Skipping an issue not in the queue returns empty list."""
        activated = await bq.skip_to_non_blocking(REPO, 999)
        assert activated == []

    @pytest.mark.asyncio
    async def test_skip_pending_blocking_behind_active_blocking(self, db):
        """Skipping a pending blocking issue behind an active blocking issue.

        The pending issue becomes non-blocking but stays pending because the
        active blocking issue still gates activation.
        """
        await _enqueue(10, blocking=True, db_conn=db)
        await _enqueue(20, blocking=True, db_conn=db)
        assert await _status(10) == BlockingQueueStatus.ACTIVE
        assert await _status(20) == BlockingQueueStatus.PENDING

        activated = await bq.skip_to_non_blocking(REPO, 20)

        # #20 is now non-blocking but still pending (#10 gates it)
        entry20 = await store.get_by_issue(REPO, 20)
        assert entry20 is not None
        assert entry20.is_blocking is False
        assert entry20.queue_status == BlockingQueueStatus.PENDING
        assert activated == []
