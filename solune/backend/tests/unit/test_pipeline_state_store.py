"""Tests for pipeline_state_store — SQLite write-through cache for pipeline orchestration state.

Covers:
- init_pipeline_state_store (L1 warm-up from SQLite)
- Pipeline state CRUD (get / set / delete / get_all / async fallback)
- Main branch CRUD (get / set / delete / async fallback)
- Sub-issue map CRUD (get / set with merge / delete)
- Trigger inflight guard (get / set / delete / clear_all)
- L1-miss → SQLite fallback behaviour
- Graceful handling when tables don't exist
- Write-through atomicity (L1 only updated on successful SQLite write)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import aiosqlite
import pytest

# Module under test — imported after env vars set in conftest.py
from src.services import pipeline_state_store as store
from src.services.workflow_orchestrator.models import MainBranchInfo, PipelineState

# ── Helpers ──────────────────────────────────────────────────────


def _make_pipeline_state(**overrides) -> PipelineState:
    """Create a PipelineState with sensible defaults; override via kwargs."""
    defaults = {
        "issue_number": 100,
        "project_id": "PVT_proj1",
        "status": "In Progress",
        "agents": ["speckit.specify", "tester"],
        "current_agent_index": 0,
        "completed_agents": [],
        "started_at": datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC),
        "error": None,
        "agent_assigned_sha": "abc123",
        "agent_sub_issues": {},
        "original_status": None,
        "target_status": None,
        "execution_mode": "sequential",
        "parallel_agent_statuses": {},
        "failed_agents": [],
    }
    defaults.update(overrides)
    return PipelineState(**defaults)


def _make_main_branch_info(**overrides) -> MainBranchInfo:
    defaults: MainBranchInfo = {
        "branch": "copilot/issue-100",
        "pr_number": 42,
        "head_sha": "deadbeef",
    }
    defaults.update(overrides)  # type: ignore[typeddict-item]
    return defaults


# ── Schema helper ────────────────────────────────────────────────

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

_MAIN_BRANCHES_DDL = """
CREATE TABLE IF NOT EXISTS issue_main_branches (
    issue_number INTEGER PRIMARY KEY,
    branch       TEXT NOT NULL,
    pr_number    INTEGER NOT NULL,
    head_sha     TEXT NOT NULL DEFAULT ''
);
"""

_SUB_ISSUE_MAP_DDL = """
CREATE TABLE IF NOT EXISTS issue_sub_issue_map (
    issue_number      INTEGER NOT NULL,
    agent_name        TEXT NOT NULL,
    sub_issue_number  INTEGER NOT NULL,
    sub_issue_node_id TEXT NOT NULL DEFAULT '',
    sub_issue_url     TEXT DEFAULT '',
    PRIMARY KEY (issue_number, agent_name)
);
"""

_TRIGGER_INFLIGHT_DDL = """
CREATE TABLE IF NOT EXISTS agent_trigger_inflight (
    trigger_key TEXT PRIMARY KEY,
    started_at  TEXT NOT NULL
);
"""


async def _create_tables(db: aiosqlite.Connection) -> None:
    """Create all pipeline state store tables."""
    for ddl in (
        _PIPELINE_STATES_DDL,
        _MAIN_BRANCHES_DDL,
        _SUB_ISSUE_MAP_DDL,
        _TRIGGER_INFLIGHT_DDL,
    ):
        await db.executescript(ddl)
    await db.commit()


# ── Fixtures ─────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_caches():
    """Reset module-level L1 caches between tests."""
    store._pipeline_states.clear()
    store._issue_main_branches.clear()
    store._issue_sub_issue_map.clear()
    store._agent_trigger_inflight.clear()
    old_db = store._db
    store._db = None
    yield
    store._pipeline_states.clear()
    store._issue_main_branches.clear()
    store._issue_sub_issue_map.clear()
    store._agent_trigger_inflight.clear()
    store._db = old_db


@pytest.fixture
async def db():
    """In-memory SQLite database with pipeline state store tables."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await _create_tables(conn)
    yield conn
    await conn.close()


# ══════════════════════════════════════════════════════════════════
# init_pipeline_state_store
# ══════════════════════════════════════════════════════════════════


class TestInitPipelineStateStore:
    """Verify L1 caches are warmed from SQLite on startup."""

    async def test_init_loads_pipeline_states(self, db):
        """Pipeline states pre-seeded in SQLite are loaded into L1."""
        now = datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC).isoformat()
        metadata = json.dumps(
            {
                "agents": ["speckit.specify"],
                "current_agent_index": 0,
                "completed_agents": [],
                "started_at": now,
                "error": None,
                "agent_assigned_sha": "sha1",
                "original_status": None,
                "target_status": None,
                "execution_mode": "sequential",
                "parallel_agent_statuses": {},
                "failed_agents": [],
            }
        )
        await db.execute(
            """INSERT INTO pipeline_states
               (issue_number, project_id, status, agent_name, agent_instance_id,
                pr_number, pr_url, sub_issues, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                100,
                "PVT_proj1",
                "In Progress",
                "speckit.specify",
                None,
                None,
                None,
                None,
                metadata,
                now,
                now,
            ),
        )
        await db.commit()

        await store.init_pipeline_state_store(db)

        state = store.get_pipeline_state(100)
        assert state is not None
        assert state.issue_number == 100
        assert state.project_id == "PVT_proj1"
        assert state.agents == ["speckit.specify"]

    async def test_init_loads_main_branches(self, db):
        """Main branch entries seeded in SQLite are loaded into L1."""
        await db.execute(
            "INSERT INTO issue_main_branches (issue_number, branch, pr_number, head_sha) VALUES (?, ?, ?, ?)",
            (200, "copilot/issue-200", 55, "beef1234"),
        )
        await db.commit()

        await store.init_pipeline_state_store(db)

        info = store.get_main_branch(200)
        assert info is not None
        assert info["branch"] == "copilot/issue-200"
        assert info["pr_number"] == 55
        assert info["head_sha"] == "beef1234"

    async def test_init_loads_sub_issue_map(self, db):
        """Sub-issue mappings seeded in SQLite are loaded into L1."""
        await db.execute(
            "INSERT INTO issue_sub_issue_map VALUES (?, ?, ?, ?, ?)",
            (300, "tester", 301, "SI_abc", "https://github.com/repo/issues/301"),
        )
        await db.commit()

        await store.init_pipeline_state_store(db)

        mapping = store.get_sub_issue_map(300)
        assert "tester" in mapping
        assert mapping["tester"]["number"] == 301
        assert mapping["tester"]["node_id"] == "SI_abc"

    async def test_init_loads_trigger_inflights(self, db):
        """Trigger inflight markers seeded in SQLite are loaded into L1."""
        ts = datetime(2026, 3, 12, 8, 0, 0, tzinfo=UTC)
        await db.execute(
            "INSERT INTO agent_trigger_inflight VALUES (?, ?)",
            ("100:tester", ts.isoformat()),
        )
        await db.commit()

        await store.init_pipeline_state_store(db)

        loaded = store.get_trigger_inflight("100:tester")
        assert loaded is not None
        assert loaded == ts

    async def test_init_handles_missing_tables_gracefully(self):
        """When tables don't exist, init succeeds with empty caches."""
        conn = await aiosqlite.connect(":memory:")
        conn.row_factory = aiosqlite.Row
        try:
            await store.init_pipeline_state_store(conn)
            assert len(store._pipeline_states) == 0
            assert len(store._issue_main_branches) == 0
        finally:
            await conn.close()


# ══════════════════════════════════════════════════════════════════
# Pipeline State CRUD
# ══════════════════════════════════════════════════════════════════


class TestPipelineStateCRUD:
    """get / set / delete / get_all / async fallback for pipeline states."""

    async def test_set_and_get(self, db):
        """set_pipeline_state writes through to SQLite and populates L1."""
        await store.init_pipeline_state_store(db)
        state = _make_pipeline_state(issue_number=100)

        await store.set_pipeline_state(100, state)

        # L1 hit
        cached = store.get_pipeline_state(100)
        assert cached is not None
        assert cached.issue_number == 100
        assert cached.project_id == "PVT_proj1"

        # SQLite persisted
        cursor = await db.execute("SELECT * FROM pipeline_states WHERE issue_number = ?", (100,))
        row = await cursor.fetchone()
        assert row is not None
        assert row["project_id"] == "PVT_proj1"

    async def test_get_returns_none_for_missing(self, db):
        """get_pipeline_state returns None when issue not tracked."""
        await store.init_pipeline_state_store(db)
        assert store.get_pipeline_state(999) is None

    async def test_get_all_returns_all_cached(self, db):
        """get_all_pipeline_states returns a snapshot of all L1 entries."""
        await store.init_pipeline_state_store(db)
        s1 = _make_pipeline_state(issue_number=100)
        s2 = _make_pipeline_state(issue_number=200, project_id="PVT_proj2")

        await store.set_pipeline_state(100, s1)
        await store.set_pipeline_state(200, s2)

        all_states = store.get_all_pipeline_states()
        assert len(all_states) == 2
        assert 100 in all_states
        assert 200 in all_states

    async def test_delete_removes_from_both_layers(self, db):
        """delete_pipeline_state clears from L1 and SQLite."""
        await store.init_pipeline_state_store(db)
        state = _make_pipeline_state(issue_number=100)
        await store.set_pipeline_state(100, state)

        await store.delete_pipeline_state(100)

        assert store.get_pipeline_state(100) is None
        cursor = await db.execute("SELECT * FROM pipeline_states WHERE issue_number = ?", (100,))
        assert await cursor.fetchone() is None

    async def test_async_get_falls_back_to_sqlite_on_l1_miss(self, db):
        """get_pipeline_state_async repopulates L1 from SQLite on miss."""
        await store.init_pipeline_state_store(db)
        state = _make_pipeline_state(issue_number=100)
        await store.set_pipeline_state(100, state)

        # Clear L1 to simulate eviction
        store._pipeline_states.clear()
        assert store.get_pipeline_state(100) is None  # L1 miss

        # Async fallback should hit SQLite
        recovered = await store.get_pipeline_state_async(100)
        assert recovered is not None
        assert recovered.issue_number == 100

        # L1 should be repopulated
        assert store.get_pipeline_state(100) is not None

    async def test_async_get_returns_none_when_not_in_sqlite(self, db):
        """get_pipeline_state_async returns None when not in any layer."""
        await store.init_pipeline_state_store(db)
        result = await store.get_pipeline_state_async(999)
        assert result is None

    async def test_set_upserts_on_conflict(self, db):
        """Second set_pipeline_state for same issue updates the row."""
        await store.init_pipeline_state_store(db)
        s1 = _make_pipeline_state(issue_number=100, status="In Progress")
        await store.set_pipeline_state(100, s1)

        s2 = _make_pipeline_state(issue_number=100, status="In Review")
        await store.set_pipeline_state(100, s2)

        cached = store.get_pipeline_state(100)
        assert cached.status == "In Review"

        cursor = await db.execute(
            "SELECT COUNT(*) FROM pipeline_states WHERE issue_number = ?", (100,)
        )
        row = await cursor.fetchone()
        assert row[0] == 1  # Only one row — upsert, not insert

    async def test_set_without_db_only_writes_l1(self):
        """When no DB is configured, set_pipeline_state still caches to L1."""
        store._db = None
        state = _make_pipeline_state(issue_number=100)

        await store.set_pipeline_state(100, state)

        assert store.get_pipeline_state(100) is not None

    async def test_set_preserves_sub_issues_json(self, db):
        """agent_sub_issues are round-tripped via JSON correctly."""
        await store.init_pipeline_state_store(db)
        state = _make_pipeline_state(
            issue_number=100,
            agent_sub_issues={
                "tester": {"number": 101, "node_id": "SI_abc", "url": "https://example.com"}
            },
        )
        await store.set_pipeline_state(100, state)

        # Clear L1 and recover from SQLite
        store._pipeline_states.clear()
        recovered = await store.get_pipeline_state_async(100)
        assert recovered is not None
        assert recovered.agent_sub_issues["tester"]["number"] == 101

    async def test_set_preserves_metadata_fields(self, db):
        """Metadata fields (execution_mode, parallel_agent_statuses, etc.) round-trip correctly."""
        await store.init_pipeline_state_store(db)
        state = _make_pipeline_state(
            issue_number=100,
            execution_mode="parallel",
            parallel_agent_statuses={"tester": "completed", "linter": "running"},
            failed_agents=["designer"],
            original_status="Todo",
            target_status="In Review",
        )
        await store.set_pipeline_state(100, state)

        store._pipeline_states.clear()
        recovered = await store.get_pipeline_state_async(100)
        assert recovered is not None
        assert recovered.execution_mode == "parallel"
        assert recovered.parallel_agent_statuses == {"tester": "completed", "linter": "running"}
        assert recovered.failed_agents == ["designer"]
        assert recovered.original_status == "Todo"
        assert recovered.target_status == "In Review"


# ══════════════════════════════════════════════════════════════════
# Main Branch CRUD
# ══════════════════════════════════════════════════════════════════


class TestMainBranchCRUD:
    """get / set / delete / async fallback for issue main branches."""

    async def test_set_and_get(self, db):
        await store.init_pipeline_state_store(db)
        info = _make_main_branch_info()

        await store.set_main_branch(100, info)

        cached = store.get_main_branch(100)
        assert cached is not None
        assert cached["branch"] == "copilot/issue-100"
        assert cached["pr_number"] == 42

    async def test_get_returns_none_for_missing(self, db):
        await store.init_pipeline_state_store(db)
        assert store.get_main_branch(999) is None

    async def test_delete_removes_from_both_layers(self, db):
        await store.init_pipeline_state_store(db)
        await store.set_main_branch(100, _make_main_branch_info())

        await store.delete_main_branch(100)

        assert store.get_main_branch(100) is None
        cursor = await db.execute(
            "SELECT * FROM issue_main_branches WHERE issue_number = ?", (100,)
        )
        assert await cursor.fetchone() is None

    async def test_async_get_falls_back_to_sqlite(self, db):
        """Async getter recovers from SQLite after L1 eviction."""
        await store.init_pipeline_state_store(db)
        await store.set_main_branch(100, _make_main_branch_info())
        store._issue_main_branches.clear()

        recovered = await store.get_main_branch_async(100)
        assert recovered is not None
        assert recovered["branch"] == "copilot/issue-100"

    async def test_async_get_returns_none_when_absent(self, db):
        await store.init_pipeline_state_store(db)
        assert await store.get_main_branch_async(999) is None

    async def test_set_replaces_existing(self, db):
        """Setting main branch for same issue replaces the entry."""
        await store.init_pipeline_state_store(db)
        await store.set_main_branch(100, _make_main_branch_info(branch="branch-v1"))
        await store.set_main_branch(100, _make_main_branch_info(branch="branch-v2"))

        cached = store.get_main_branch(100)
        assert cached["branch"] == "branch-v2"


# ══════════════════════════════════════════════════════════════════
# Sub-Issue Map CRUD
# ══════════════════════════════════════════════════════════════════


class TestSubIssueMapCRUD:
    """get / set (with merge) / delete for sub-issue mappings."""

    async def test_set_and_get(self, db):
        await store.init_pipeline_state_store(db)
        mapping = {"tester": {"number": 101, "node_id": "SI_a", "url": "https://example.com/101"}}

        await store.set_sub_issue_map(100, mapping)

        result = store.get_sub_issue_map(100)
        assert "tester" in result
        assert result["tester"]["number"] == 101

    async def test_get_returns_empty_for_missing(self, db):
        await store.init_pipeline_state_store(db)
        result = store.get_sub_issue_map(999)
        assert result == {}

    async def test_set_merges_new_agents(self, db):
        """Second call to set_sub_issue_map merges into existing mappings."""
        await store.init_pipeline_state_store(db)
        await store.set_sub_issue_map(
            100, {"tester": {"number": 101, "node_id": "SI_a", "url": ""}}
        )
        await store.set_sub_issue_map(
            100, {"linter": {"number": 102, "node_id": "SI_b", "url": ""}}
        )

        result = store.get_sub_issue_map(100)
        assert "tester" in result
        assert "linter" in result

    async def test_delete_clears_both_layers(self, db):
        await store.init_pipeline_state_store(db)
        await store.set_sub_issue_map(
            100, {"tester": {"number": 101, "node_id": "SI_a", "url": ""}}
        )

        await store.delete_sub_issue_map(100)

        assert store.get_sub_issue_map(100) == {}
        cursor = await db.execute(
            "SELECT * FROM issue_sub_issue_map WHERE issue_number = ?", (100,)
        )
        assert await cursor.fetchone() is None

    async def test_sqlite_persistence(self, db):
        """Sub-issue mappings are persisted to SQLite."""
        await store.init_pipeline_state_store(db)
        await store.set_sub_issue_map(
            100, {"tester": {"number": 101, "node_id": "SI_a", "url": "http://ex.com"}}
        )

        cursor = await db.execute(
            "SELECT * FROM issue_sub_issue_map WHERE issue_number = ?", (100,)
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["agent_name"] == "tester"
        assert row["sub_issue_number"] == 101


# ══════════════════════════════════════════════════════════════════
# Trigger Inflight Guard
# ══════════════════════════════════════════════════════════════════


class TestTriggerInflight:
    """get / set / delete / clear_all for agent trigger inflight markers."""

    async def test_set_and_get(self, db):
        await store.init_pipeline_state_store(db)
        ts = datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC)

        await store.set_trigger_inflight("100:tester", ts)

        assert store.get_trigger_inflight("100:tester") == ts

    async def test_get_returns_none_for_missing(self, db):
        await store.init_pipeline_state_store(db)
        assert store.get_trigger_inflight("unknown") is None

    async def test_delete_clears_both_layers(self, db):
        await store.init_pipeline_state_store(db)
        ts = datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC)
        await store.set_trigger_inflight("100:tester", ts)

        await store.delete_trigger_inflight("100:tester")

        assert store.get_trigger_inflight("100:tester") is None
        cursor = await db.execute(
            "SELECT * FROM agent_trigger_inflight WHERE trigger_key = ?", ("100:tester",)
        )
        assert await cursor.fetchone() is None

    async def test_clear_all_removes_everything(self, db):
        await store.init_pipeline_state_store(db)
        ts = datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC)
        await store.set_trigger_inflight("100:tester", ts)
        await store.set_trigger_inflight("200:linter", ts)

        await store.clear_all_trigger_inflights()

        assert store.get_trigger_inflight("100:tester") is None
        assert store.get_trigger_inflight("200:linter") is None

    async def test_sqlite_persistence(self, db):
        """Trigger markers are persisted to SQLite."""
        await store.init_pipeline_state_store(db)
        ts = datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC)
        await store.set_trigger_inflight("100:tester", ts)

        cursor = await db.execute(
            "SELECT * FROM agent_trigger_inflight WHERE trigger_key = ?", ("100:tester",)
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row["started_at"] == ts.isoformat()


# ══════════════════════════════════════════════════════════════════
# Error Handling & Edge Cases
# ══════════════════════════════════════════════════════════════════


class TestErrorHandling:
    """Verify graceful degradation on SQLite errors."""

    async def test_set_pipeline_state_skips_l1_on_db_error(self, db):
        """If SQLite write fails, L1 is NOT updated (consistency guard)."""
        await store.init_pipeline_state_store(db)
        state = _make_pipeline_state(issue_number=100)

        # Simulate SQLite write failure
        with patch.object(
            store._db, "execute", new_callable=AsyncMock, side_effect=aiosqlite.Error("disk full")
        ):
            await store.set_pipeline_state(100, state)

        # L1 should NOT be populated due to write failure
        assert store.get_pipeline_state(100) is None

    async def test_async_get_returns_none_on_db_read_error(self, db):
        """If SQLite read fails during async fallback, returns None gracefully."""
        await store.init_pipeline_state_store(db)

        with patch.object(
            store._db, "execute", new_callable=AsyncMock, side_effect=aiosqlite.Error("read error")
        ):
            result = await store.get_pipeline_state_async(100)

        assert result is None

    async def test_delete_pipeline_state_handles_db_error(self, db):
        """Delete clears L1 even if SQLite delete fails."""
        await store.init_pipeline_state_store(db)
        state = _make_pipeline_state(issue_number=100)
        await store.set_pipeline_state(100, state)

        with patch.object(
            store._db, "execute", new_callable=AsyncMock, side_effect=aiosqlite.Error("write error")
        ):
            await store.delete_pipeline_state(100)

        # L1 is cleared regardless
        assert store.get_pipeline_state(100) is None

    async def test_async_get_pipeline_state_without_db(self):
        """With no DB configured, async get still returns from L1 or None."""
        store._db = None
        state = _make_pipeline_state(issue_number=100)
        store._pipeline_states[100] = state

        result = await store.get_pipeline_state_async(100)
        assert result is not None

        result = await store.get_pipeline_state_async(999)
        assert result is None

    async def test_async_get_main_branch_without_db(self):
        """With no DB configured, async main branch getter returns from L1 or None."""
        store._db = None
        store._issue_main_branches[100] = _make_main_branch_info()

        result = await store.get_main_branch_async(100)
        assert result is not None

        result = await store.get_main_branch_async(999)
        assert result is None


class TestRowConversionCorruptTimestamp:
    """Bug-bash regression: _row_to_pipeline_state must not crash on a
    malformed ``started_at`` timestamp in persisted metadata JSON.

    Previously, ``datetime.fromisoformat()`` was called without a
    try/except, so a corrupt value would raise ``ValueError`` and
    prevent the entire state reload from completing.
    """

    async def test_corrupt_started_at_returns_none(self, mock_db: aiosqlite.Connection):
        """A pipeline with a malformed started_at should load with started_at=None."""
        metadata = {
            "agents": ["tester"],
            "current_agent_index": 0,
            "completed_agents": [],
            "started_at": "not-a-valid-date",
            "error": None,
            "agent_assigned_sha": "",
        }
        await mock_db.execute(
            """INSERT INTO pipeline_states
               (issue_number, project_id, status, agent_name, agent_instance_id,
                pr_number, pr_url, sub_issues, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (
                999,
                "PVT_test",
                "In Progress",
                "tester",
                None,
                None,
                None,
                "{}",
                json.dumps(metadata),
            ),
        )
        await mock_db.commit()

        cursor = await mock_db.execute(
            "SELECT * FROM pipeline_states WHERE issue_number = ?", (999,)
        )
        row = await cursor.fetchone()
        assert row is not None

        state = store._row_to_pipeline_state(row)
        # Must not crash; started_at should gracefully fall back to None
        assert state.started_at is None
        assert state.issue_number == 999
