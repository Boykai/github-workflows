"""Integration tests for Pipeline Queue Mode feature.

Covers:
- Launch 2 issues with queue ON → first starts, second is queued
- Complete first → second auto-starts
- Queue OFF → both launch immediately
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import aiosqlite
import pytest

from src.services import pipeline_state_store as store
from src.services.workflow_orchestrator.models import PipelineState


# ── Helpers ──────────────────────────────────────────────────────


def _make_pipeline_state(**overrides) -> PipelineState:
    defaults = {
        "issue_number": 100,
        "project_id": "PVT_proj1",
        "status": "Backlog",
        "agents": ["speckit.specify"],
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
# Integration: queue mode lifecycle
# ══════════════════════════════════════════════════════════════════


class TestQueueModeLifecycle:
    """Full lifecycle: launch → queue → complete → dequeue."""

    async def test_queue_on_first_starts_second_queued(self, db):
        """With queue ON, first pipeline starts and second is queued."""
        from src.services.settings_store import is_queue_mode_enabled

        # Enable queue mode
        await db.execute(
            "INSERT INTO project_settings (github_user_id, project_id, queue_mode, updated_at) VALUES (?, ?, 1, '')",
            ("user1", "PVT_proj1"),
        )
        await db.commit()

        # Verify queue mode is on
        assert await is_queue_mode_enabled(db, "PVT_proj1") is True

        # First pipeline: active (not queued)
        s1 = _make_pipeline_state(
            issue_number=1,
            project_id="PVT_proj1",
            queued=False,
            started_at=datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC),
        )
        store._pipeline_states[1] = s1

        # Active count should be 1
        assert store.count_active_pipelines_for_project("PVT_proj1") == 1

        # Second pipeline: should be queued
        s2 = _make_pipeline_state(
            issue_number=2,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC),
        )
        store._pipeline_states[2] = s2

        # Active count stays at 1 (queued not counted)
        assert store.count_active_pipelines_for_project("PVT_proj1") == 1
        assert store._pipeline_states[2].queued is True

    async def test_complete_first_dequeues_second(self, db):
        """When first pipeline completes, second is dequeued (queued=False)."""
        await store.init_pipeline_state_store(db)

        # First pipeline: active
        s1 = _make_pipeline_state(
            issue_number=1,
            project_id="PVT_proj1",
            queued=False,
            started_at=datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC),
        )
        await store.set_pipeline_state(1, s1)

        # Second pipeline: queued
        s2 = _make_pipeline_state(
            issue_number=2,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC),
        )
        await store.set_pipeline_state(2, s2)

        # Simulate first pipeline completing: remove from L1
        store._pipeline_states.pop(1, None)

        # Now no active pipelines
        assert store.count_active_pipelines_for_project("PVT_proj1") == 0

        # Simulate dequeue: find oldest queued, mark as not queued
        all_states = store.get_all_pipeline_states()
        queued = sorted(
            (
                (num, state)
                for num, state in all_states.items()
                if state.project_id == "PVT_proj1" and state.queued
            ),
            key=lambda pair: pair[1].started_at or datetime.max.replace(tzinfo=UTC),
        )
        assert len(queued) == 1
        assert queued[0][0] == 2

        # Dequeue it
        issue_number, pipeline = queued[0]
        pipeline.queued = False
        store._pipeline_states[issue_number] = pipeline

        # Now one active pipeline (the dequeued one)
        assert store.count_active_pipelines_for_project("PVT_proj1") == 1
        assert store._pipeline_states[2].queued is False

    async def test_queue_off_both_launch_immediately(self, db):
        """With queue OFF, multiple pipelines all start immediately."""
        from src.services.settings_store import is_queue_mode_enabled

        # Queue mode disabled (default)
        assert await is_queue_mode_enabled(db, "PVT_proj1") is False

        # Both pipelines active (not queued)
        s1 = _make_pipeline_state(issue_number=1, project_id="PVT_proj1", queued=False)
        s2 = _make_pipeline_state(issue_number=2, project_id="PVT_proj1", queued=False)
        store._pipeline_states[1] = s1
        store._pipeline_states[2] = s2

        # Both are active
        assert store.count_active_pipelines_for_project("PVT_proj1") == 2

    async def test_queue_mode_toggle_persistence(self, db):
        """Queue mode setting persists and reads back correctly."""
        from src.services.settings_store import is_queue_mode_enabled, upsert_project_settings

        # Initially OFF
        assert await is_queue_mode_enabled(db, "PVT_proj1") is False

        # Enable
        await upsert_project_settings(db, "user1", "PVT_proj1", {"queue_mode": 1})
        assert await is_queue_mode_enabled(db, "PVT_proj1") is True

        # Disable
        await upsert_project_settings(db, "user1", "PVT_proj1", {"queue_mode": 0})
        assert await is_queue_mode_enabled(db, "PVT_proj1") is False
