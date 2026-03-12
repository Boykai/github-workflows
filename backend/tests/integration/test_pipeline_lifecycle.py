"""Integration test: pipeline state persistence across restarts.

Verifies that pipeline state stored via the pipeline_state_store module
survives a simulated container restart (store teardown → re-init from SQLite).
"""

from __future__ import annotations

from datetime import UTC, datetime

import aiosqlite
import pytest

from src.services.pipeline_state_store import (
    _agent_trigger_inflight,
    _issue_main_branches,
    _issue_sub_issue_map,
    _pipeline_states,
    delete_pipeline_state,
    get_all_pipeline_states,
    get_main_branch,
    get_pipeline_state,
    get_pipeline_state_async,
    get_sub_issue_map,
    get_trigger_inflight,
    init_pipeline_state_store,
    set_main_branch,
    set_pipeline_state,
    set_sub_issue_map,
    set_trigger_inflight,
)
from src.services.workflow_orchestrator.models import MainBranchInfo, PipelineState

PROJECT_ID = "PVT_test_project"


@pytest.fixture
async def db():
    """In-memory SQLite with pipeline state tables for testing."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    await conn.executescript("""
        CREATE TABLE IF NOT EXISTS pipeline_states (
            issue_number INTEGER PRIMARY KEY,
            project_id TEXT NOT NULL,
            status TEXT NOT NULL,
            agent_name TEXT,
            agent_instance_id TEXT,
            pr_number INTEGER,
            pr_url TEXT,
            sub_issues TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS issue_main_branches (
            issue_number INTEGER PRIMARY KEY,
            branch TEXT NOT NULL,
            pr_number INTEGER NOT NULL,
            head_sha TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );

        CREATE TABLE IF NOT EXISTS issue_sub_issue_map (
            issue_number INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            sub_issue_number INTEGER NOT NULL,
            sub_issue_node_id TEXT NOT NULL,
            sub_issue_url TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            PRIMARY KEY (issue_number, agent_name)
        );

        CREATE TABLE IF NOT EXISTS agent_trigger_inflight (
            trigger_key TEXT PRIMARY KEY,
            started_at TEXT NOT NULL
        );
    """)
    yield conn
    await conn.close()


@pytest.fixture(autouse=True)
def _clear_caches():
    """Clear L1 caches between tests."""
    _pipeline_states.clear()
    _issue_main_branches.clear()
    _issue_sub_issue_map.clear()
    _agent_trigger_inflight.clear()
    yield
    _pipeline_states.clear()
    _issue_main_branches.clear()
    _issue_sub_issue_map.clear()
    _agent_trigger_inflight.clear()


class TestPipelineStateLifecycle:
    """Test pipeline state persistence across simulated restarts."""

    async def test_pipeline_state_survives_restart(self, db: aiosqlite.Connection):
        """Pipeline state written via set_pipeline_state is recovered after init."""
        state = PipelineState(
            issue_number=42,
            project_id=PROJECT_ID,
            status="In Progress",
            agents=["copilot-swe-agent", "review-agent"],
            current_agent_index=0,
        )

        # Write state
        await init_pipeline_state_store(db)
        await set_pipeline_state(42, state)

        # Simulate restart: clear L1 caches
        _pipeline_states.clear()
        assert get_pipeline_state(42) is None

        # Re-init from SQLite
        await init_pipeline_state_store(db)

        # Verify recovery
        recovered = get_pipeline_state(42)
        assert recovered is not None
        assert recovered.issue_number == 42
        assert recovered.project_id == PROJECT_ID
        assert recovered.status == "In Progress"
        assert recovered.agents == ["copilot-swe-agent", "review-agent"]
        assert recovered.current_agent_index == 0

    async def test_pipeline_state_delete_persists(self, db: aiosqlite.Connection):
        """Deleted pipeline state is not recovered after restart."""
        state = PipelineState(
            issue_number=99,
            project_id=PROJECT_ID,
            status="Ready",
            agents=["agent-1"],
        )

        await init_pipeline_state_store(db)
        await set_pipeline_state(99, state)
        await delete_pipeline_state(99)

        # Simulate restart
        _pipeline_states.clear()
        await init_pipeline_state_store(db)

        assert get_pipeline_state(99) is None

    async def test_get_all_pipeline_states(self, db: aiosqlite.Connection):
        """get_all_pipeline_states returns all stored states."""
        await init_pipeline_state_store(db)

        for i in [10, 20, 30]:
            state = PipelineState(
                issue_number=i,
                project_id=PROJECT_ID,
                status="Ready",
                agents=["agent"],
            )
            await set_pipeline_state(i, state)

        all_states = get_all_pipeline_states()
        assert len(all_states) == 3
        assert set(all_states.keys()) == {10, 20, 30}

    async def test_evicted_state_recovered_from_sqlite(self, db: aiosqlite.Connection):
        """States evicted from L1 (BoundedDict) are recoverable via async fallback."""
        await init_pipeline_state_store(db)

        state = PipelineState(
            issue_number=1,
            project_id=PROJECT_ID,
            status="In Progress",
            agents=["agent-1"],
            current_agent_index=0,
        )
        await set_pipeline_state(1, state)

        # Manually evict from L1 to simulate BoundedDict eviction
        _pipeline_states.pop(1, None)
        assert get_pipeline_state(1) is None  # L1 miss

        # Async fallback should recover from SQLite
        recovered = await get_pipeline_state_async(1)
        assert recovered is not None
        assert recovered.issue_number == 1
        assert recovered.status == "In Progress"
        assert recovered.agents == ["agent-1"]

        # L1 should now be repopulated
        assert get_pipeline_state(1) is not None


class TestMainBranchLifecycle:
    """Test main branch persistence across simulated restarts."""

    async def test_main_branch_survives_restart(self, db: aiosqlite.Connection):
        """Main branch info is recovered after restart."""
        info = MainBranchInfo(branch="copilot/fix-bug-42", pr_number=100, head_sha="abc123")

        await init_pipeline_state_store(db)
        await set_main_branch(42, info)

        # Simulate restart
        _issue_main_branches.clear()
        await init_pipeline_state_store(db)

        recovered = get_main_branch(42)
        assert recovered is not None
        assert recovered["branch"] == "copilot/fix-bug-42"
        assert recovered["pr_number"] == 100
        assert recovered["head_sha"] == "abc123"


class TestSubIssueMapLifecycle:
    """Test sub-issue map persistence across simulated restarts."""

    async def test_sub_issue_map_survives_restart(self, db: aiosqlite.Connection):
        """Sub-issue mappings are recovered after restart."""
        mappings = {
            "copilot-swe-agent": {
                "number": 43,
                "node_id": "I_kwDOtest",
                "url": "https://github.com/test/test/issues/43",
            }
        }

        await init_pipeline_state_store(db)
        await set_sub_issue_map(42, mappings)

        # Simulate restart
        _issue_sub_issue_map.clear()
        await init_pipeline_state_store(db)

        recovered = get_sub_issue_map(42)
        assert recovered is not None
        assert "copilot-swe-agent" in recovered
        assert recovered["copilot-swe-agent"]["number"] == 43


class TestTriggerInflightLifecycle:
    """Test trigger inflight persistence across simulated restarts."""

    async def test_trigger_inflight_survives_restart(self, db: aiosqlite.Connection):
        """Trigger inflight markers are recovered after restart."""
        now = datetime.now(UTC)

        await init_pipeline_state_store(db)
        await set_trigger_inflight("42:in progress:agent", now)

        # Simulate restart
        _agent_trigger_inflight.clear()
        await init_pipeline_state_store(db)

        recovered = get_trigger_inflight("42:in progress:agent")
        assert recovered is not None
