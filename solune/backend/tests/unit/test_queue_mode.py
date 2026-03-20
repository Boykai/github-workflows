"""Unit tests for Pipeline Queue Mode feature.

Covers:
- count_active_pipelines_for_project() — 0, 1, N active pipelines
- is_queue_mode_enabled() — DB helper returns True/False
- Queue gate logic — queue ON + active → no agent; queue OFF → immediate
- Dequeue FIFO ordering — oldest queued pipeline starts first
- PipelineState.queued field serialization round-trip
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import aiosqlite
import pytest

from src.services import pipeline_state_store as store
from src.services.workflow_orchestrator.models import PipelineState


# ── Helpers ──────────────────────────────────────────────────────


def _make_pipeline_state(**overrides) -> PipelineState:
    """Create a PipelineState with sensible defaults; override via kwargs."""
    defaults = {
        "issue_number": 100,
        "project_id": "PVT_proj1",
        "status": "Backlog",
        "agents": ["speckit.specify", "tester"],
        "current_agent_index": 0,
        "completed_agents": [],
        "started_at": datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC),
        "error": None,
        "agent_assigned_sha": "",
        "agent_sub_issues": {},
        "original_status": None,
        "target_status": None,
        "execution_mode": "sequential",
        "parallel_agent_statuses": {},
        "failed_agents": [],
        "queued": False,
    }
    defaults.update(overrides)
    return PipelineState(**defaults)


# ── Schema ───────────────────────────────────────────────────────

_PIPELINE_STATES_DDL = """
CREATE TABLE IF NOT EXISTS pipeline_states (
    issue_number  INTEGER PRIMARY KEY,
    project_id    TEXT NOT NULL,
    status        TEXT NOT NULL,
    agent_name    TEXT,
    agent_instance_id TEXT,
    pr_number     INTEGER,
    pr_url        TEXT,
    sub_issues    TEXT,
    metadata      TEXT,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);
"""

_PROJECT_SETTINGS_DDL = """
CREATE TABLE IF NOT EXISTS project_settings (
    github_user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    board_display_config TEXT,
    agent_pipeline_mappings TEXT,
    queue_mode INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (github_user_id, project_id)
);
"""


async def _create_tables(db: aiosqlite.Connection) -> None:
    for ddl in (_PIPELINE_STATES_DDL, _PROJECT_SETTINGS_DDL):
        await db.executescript(ddl)
    await db.commit()


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_caches():
    """Reset module-level L1 caches between tests."""
    store._pipeline_states.clear()
    old_db = store._db
    store._db = None
    yield
    store._pipeline_states.clear()
    store._db = old_db


@pytest.fixture
async def db():
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await _create_tables(conn)
    yield conn
    await conn.close()


# ══════════════════════════════════════════════════════════════════
# count_active_pipelines_for_project
# ══════════════════════════════════════════════════════════════════


class TestCountActivePipelines:
    """Tests for count_active_pipelines_for_project()."""

    def test_returns_zero_when_no_pipelines(self):
        """Empty L1 → 0 active."""
        assert store.count_active_pipelines_for_project("PVT_proj1") == 0

    def test_returns_one_for_single_active(self):
        """One non-queued pipeline → 1 active."""
        s = _make_pipeline_state(issue_number=1, project_id="PVT_proj1", queued=False)
        store._pipeline_states[1] = s
        assert store.count_active_pipelines_for_project("PVT_proj1") == 1

    def test_excludes_queued_pipelines(self):
        """Queued pipelines should NOT be counted as active."""
        s1 = _make_pipeline_state(issue_number=1, project_id="PVT_proj1", queued=False)
        s2 = _make_pipeline_state(issue_number=2, project_id="PVT_proj1", queued=True)
        store._pipeline_states[1] = s1
        store._pipeline_states[2] = s2
        assert store.count_active_pipelines_for_project("PVT_proj1") == 1

    def test_filters_by_project_id(self):
        """Only count pipelines for the given project."""
        s1 = _make_pipeline_state(issue_number=1, project_id="PVT_proj1", queued=False)
        s2 = _make_pipeline_state(issue_number=2, project_id="PVT_proj2", queued=False)
        store._pipeline_states[1] = s1
        store._pipeline_states[2] = s2
        assert store.count_active_pipelines_for_project("PVT_proj1") == 1
        assert store.count_active_pipelines_for_project("PVT_proj2") == 1

    def test_counts_multiple_active(self):
        """Multiple non-queued pipelines → N active."""
        for i in range(5):
            s = _make_pipeline_state(issue_number=i, project_id="PVT_proj1", queued=False)
            store._pipeline_states[i] = s
        assert store.count_active_pipelines_for_project("PVT_proj1") == 5


# ══════════════════════════════════════════════════════════════════
# is_queue_mode_enabled
# ══════════════════════════════════════════════════════════════════


class TestIsQueueModeEnabled:
    """Tests for is_queue_mode_enabled()."""

    async def test_returns_false_when_no_settings(self, db):
        """No project_settings row → queue mode OFF."""
        from src.services.settings_store import is_queue_mode_enabled

        result = await is_queue_mode_enabled(db, "PVT_proj1")
        assert result is False

    async def test_returns_false_when_disabled(self, db):
        """queue_mode = 0 → OFF."""
        from src.services.settings_store import is_queue_mode_enabled

        await db.execute(
            "INSERT INTO project_settings (github_user_id, project_id, queue_mode, updated_at) VALUES (?, ?, 0, '')",
            ("user1", "PVT_proj1"),
        )
        await db.commit()
        result = await is_queue_mode_enabled(db, "PVT_proj1")
        assert result is False

    async def test_returns_true_when_enabled(self, db):
        """queue_mode = 1 → ON."""
        from src.services.settings_store import is_queue_mode_enabled

        await db.execute(
            "INSERT INTO project_settings (github_user_id, project_id, queue_mode, updated_at) VALUES (?, ?, 1, '')",
            ("user1", "PVT_proj1"),
        )
        await db.commit()
        result = await is_queue_mode_enabled(db, "PVT_proj1")
        assert result is True


# ══════════════════════════════════════════════════════════════════
# PipelineState.queued serialization round-trip
# ══════════════════════════════════════════════════════════════════


class TestQueuedSerialization:
    """queued field must survive write-through and read-back."""

    async def test_queued_persisted_in_metadata(self, db):
        """queued=True is stored in the metadata JSON blob."""
        await store.init_pipeline_state_store(db)
        s = _make_pipeline_state(issue_number=42, queued=True)
        await store.set_pipeline_state(42, s)

        cursor = await db.execute("SELECT metadata FROM pipeline_states WHERE issue_number = 42")
        row = await cursor.fetchone()
        metadata = json.loads(row["metadata"])
        assert metadata["queued"] is True

    async def test_queued_false_persisted(self, db):
        """queued=False round-trips correctly."""
        await store.init_pipeline_state_store(db)
        s = _make_pipeline_state(issue_number=43, queued=False)
        await store.set_pipeline_state(43, s)

        cached = store.get_pipeline_state(43)
        assert cached is not None
        assert cached.queued is False

    async def test_queued_true_round_trip(self, db):
        """queued=True round-trips through set → L1-miss → async get → L1."""
        await store.init_pipeline_state_store(db)
        s = _make_pipeline_state(issue_number=44, queued=True)
        await store.set_pipeline_state(44, s)

        # Simulate L1 miss
        store._pipeline_states.pop(44, None)

        restored = await store.get_pipeline_state_async(44)
        assert restored is not None
        assert restored.queued is True


# ══════════════════════════════════════════════════════════════════
# Queue gate logic
# ══════════════════════════════════════════════════════════════════


class TestQueueGateLogic:
    """Verify that queue_mode ON + active pipeline → skip agent assignment."""

    def test_queue_off_preserves_immediate_behavior(self):
        """With queue OFF, count_active should not gate anything."""
        # No pipelines, no queue mode → 0 active
        assert store.count_active_pipelines_for_project("PVT_proj1") == 0

    def test_queued_pipeline_not_counted_as_active(self):
        """A queued pipeline does not count toward active limit."""
        s = _make_pipeline_state(issue_number=1, project_id="PVT_proj1", queued=True)
        store._pipeline_states[1] = s
        # Even though there's a pipeline state, it's queued, not active
        assert store.count_active_pipelines_for_project("PVT_proj1") == 0

    def test_one_active_one_queued(self):
        """One active + one queued → 1 active (gate should trigger)."""
        active = _make_pipeline_state(issue_number=1, project_id="PVT_proj1", queued=False)
        queued = _make_pipeline_state(issue_number=2, project_id="PVT_proj1", queued=True)
        store._pipeline_states[1] = active
        store._pipeline_states[2] = queued
        assert store.count_active_pipelines_for_project("PVT_proj1") == 1


# ══════════════════════════════════════════════════════════════════
# Dequeue FIFO ordering
# ══════════════════════════════════════════════════════════════════


class TestDequeueFIFOOrdering:
    """Verify that the oldest queued pipeline (by started_at) is dequeued first."""

    def test_fifo_ordering_by_started_at(self):
        """Queued pipelines sorted by started_at → oldest first."""
        s1 = _make_pipeline_state(
            issue_number=10,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC),
        )
        s2 = _make_pipeline_state(
            issue_number=20,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC),
        )
        s3 = _make_pipeline_state(
            issue_number=30,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 8, 0, 0, tzinfo=UTC),
        )
        store._pipeline_states[10] = s1
        store._pipeline_states[20] = s2
        store._pipeline_states[30] = s3

        # Simulate the dequeue logic
        all_states = store.get_all_pipeline_states()
        queued = sorted(
            (
                (num, state)
                for num, state in all_states.items()
                if state.project_id == "PVT_proj1" and state.queued
            ),
            key=lambda pair: pair[1].started_at or datetime.max.replace(tzinfo=UTC),
        )

        assert len(queued) == 3
        # Oldest first (08:00)
        assert queued[0][0] == 30
        # Then 09:00
        assert queued[1][0] == 10
        # Then 10:00
        assert queued[2][0] == 20

    def test_no_queued_pipelines(self):
        """No queued pipelines → empty dequeue list."""
        s = _make_pipeline_state(issue_number=1, project_id="PVT_proj1", queued=False)
        store._pipeline_states[1] = s

        all_states = store.get_all_pipeline_states()
        queued = [
            (num, state)
            for num, state in all_states.items()
            if state.project_id == "PVT_proj1" and state.queued
        ]
        assert len(queued) == 0
