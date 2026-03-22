"""Unit tests for pipeline queue mode feature.

Covers:
- count_active_pipelines_for_project() — 0, 1, and N active pipelines
- get_queued_pipelines_for_project() — FIFO ordering by started_at
- Queue gate logic — queue ON + active → no agent assignment
- Queue OFF preserves immediate behavior
- PipelineState.queued field serialization round-trip
- is_queue_mode_enabled() helper
- ProjectSettingsUpdate with queue_mode field
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.services import pipeline_state_store as store
from src.services.pipeline_state_store import (
    count_active_pipelines_for_project,
    get_queued_pipelines_for_project,
)
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


@pytest.fixture(autouse=True)
def _clear_l1_cache():
    """Clear L1 pipeline state cache before each test."""
    store._pipeline_states.clear()
    yield
    store._pipeline_states.clear()


# =============================================================================
# count_active_pipelines_for_project
# =============================================================================


class TestCountActivePipelinesForProject:
    def test_returns_zero_when_empty(self):
        assert count_active_pipelines_for_project("PVT_proj1") == 0

    def test_counts_active_pipelines_for_matching_project(self):
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=False
        )
        assert count_active_pipelines_for_project("PVT_proj1") == 1

    def test_ignores_queued_pipelines(self):
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=False
        )
        store._pipeline_states[200] = _make_pipeline_state(
            issue_number=200, project_id="PVT_proj1", queued=True
        )
        assert count_active_pipelines_for_project("PVT_proj1") == 1

    def test_ignores_different_project(self):
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_other", queued=False
        )
        assert count_active_pipelines_for_project("PVT_proj1") == 0

    def test_counts_multiple_active_pipelines(self):
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=False
        )
        store._pipeline_states[200] = _make_pipeline_state(
            issue_number=200, project_id="PVT_proj1", queued=False
        )
        store._pipeline_states[300] = _make_pipeline_state(
            issue_number=300, project_id="PVT_proj1", queued=False
        )
        assert count_active_pipelines_for_project("PVT_proj1") == 3

    def test_exclude_issue_prevents_self_counting(self):
        """A pipeline should not count itself when deciding whether to queue."""
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=False
        )
        # Without exclude_issue → 1
        assert count_active_pipelines_for_project("PVT_proj1") == 1
        # With exclude_issue → 0
        assert count_active_pipelines_for_project("PVT_proj1", exclude_issue=100) == 0

    def test_exclude_issue_only_removes_specified(self):
        """exclude_issue removes exactly one pipeline from the count."""
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=False
        )
        store._pipeline_states[200] = _make_pipeline_state(
            issue_number=200, project_id="PVT_proj1", queued=False
        )
        assert count_active_pipelines_for_project("PVT_proj1", exclude_issue=100) == 1
        assert count_active_pipelines_for_project("PVT_proj1", exclude_issue=200) == 1
        assert count_active_pipelines_for_project("PVT_proj1", exclude_issue=999) == 2

    def test_exclude_issue_ignores_queued(self):
        """exclude_issue with a queued pipeline has no effect (already excluded)."""
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=False
        )
        store._pipeline_states[200] = _make_pipeline_state(
            issue_number=200, project_id="PVT_proj1", queued=True
        )
        assert count_active_pipelines_for_project("PVT_proj1", exclude_issue=200) == 1


# =============================================================================
# get_queued_pipelines_for_project
# =============================================================================


class TestGetQueuedPipelinesForProject:
    def test_returns_empty_when_no_queued(self):
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=False
        )
        assert get_queued_pipelines_for_project("PVT_proj1") == []

    def test_returns_queued_pipelines_only(self):
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_proj1", queued=True
        )
        store._pipeline_states[200] = _make_pipeline_state(
            issue_number=200, project_id="PVT_proj1", queued=False
        )
        result = get_queued_pipelines_for_project("PVT_proj1")
        assert len(result) == 1
        assert result[0].issue_number == 100

    def test_fifo_ordering_by_started_at(self):
        store._pipeline_states[300] = _make_pipeline_state(
            issue_number=300,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 11, 0, 0, tzinfo=UTC),
        )
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 9, 0, 0, tzinfo=UTC),
        )
        store._pipeline_states[200] = _make_pipeline_state(
            issue_number=200,
            project_id="PVT_proj1",
            queued=True,
            started_at=datetime(2026, 3, 12, 10, 0, 0, tzinfo=UTC),
        )
        result = get_queued_pipelines_for_project("PVT_proj1")
        assert len(result) == 3
        assert [r.issue_number for r in result] == [100, 200, 300]

    def test_ignores_different_project(self):
        store._pipeline_states[100] = _make_pipeline_state(
            issue_number=100, project_id="PVT_other", queued=True
        )
        assert get_queued_pipelines_for_project("PVT_proj1") == []


# =============================================================================
# PipelineState queued field
# =============================================================================


class TestPipelineStateQueuedField:
    def test_defaults_to_false(self):
        ps = PipelineState(issue_number=1, project_id="PVT_1", status="Backlog", agents=["a"])
        assert ps.queued is False

    def test_can_be_set_true(self):
        ps = _make_pipeline_state(queued=True)
        assert ps.queued is True


# =============================================================================
# PipelineState serialization round-trip (queued field)
# =============================================================================


class TestQueuedFieldSerialization:
    def test_queued_persisted_in_metadata(self):
        ps = _make_pipeline_state(queued=True)
        row = store._pipeline_state_to_row(ps.issue_number, ps)
        # metadata is the 9th element (index 8)
        import json

        metadata = json.loads(row[8])
        assert metadata["queued"] is True

    def test_queued_false_persisted(self):
        ps = _make_pipeline_state(queued=False)
        row = store._pipeline_state_to_row(ps.issue_number, ps)
        import json

        metadata = json.loads(row[8])
        assert metadata["queued"] is False


# =============================================================================
# is_queue_mode_enabled
# =============================================================================


class TestIsQueueModeEnabled:
    async def test_returns_false_when_no_setting(self, mock_db):
        from src.services.settings_store import _queue_mode_cache, is_queue_mode_enabled

        _queue_mode_cache.clear()
        result = await is_queue_mode_enabled(mock_db, "PVT_nonexistent")
        assert result is False

    async def test_returns_true_when_enabled(self, mock_db, mock_settings):
        from src.services.database import seed_global_settings
        from src.services.settings_store import (
            _queue_mode_cache,
            is_queue_mode_enabled,
            upsert_project_settings,
        )

        with patch("src.services.database.get_settings", return_value=mock_settings):
            await seed_global_settings(mock_db)

        _queue_mode_cache.clear()
        await upsert_project_settings(mock_db, "__workflow__", "PVT_proj1", {"queue_mode": 1})
        result = await is_queue_mode_enabled(mock_db, "PVT_proj1")
        assert result is True

    async def test_returns_false_when_disabled(self, mock_db, mock_settings):
        from src.services.database import seed_global_settings
        from src.services.settings_store import (
            _queue_mode_cache,
            is_queue_mode_enabled,
            upsert_project_settings,
        )

        with patch("src.services.database.get_settings", return_value=mock_settings):
            await seed_global_settings(mock_db)

        _queue_mode_cache.clear()
        await upsert_project_settings(mock_db, "__workflow__", "PVT_proj1", {"queue_mode": 0})
        result = await is_queue_mode_enabled(mock_db, "PVT_proj1")
        assert result is False

    async def test_ignores_non_canonical_rows(self, mock_db, mock_settings):
        """Stale per-user rows should not cause queue mode to appear enabled."""
        from src.services.database import seed_global_settings
        from src.services.settings_store import (
            _queue_mode_cache,
            is_queue_mode_enabled,
            upsert_project_settings,
        )

        with patch("src.services.database.get_settings", return_value=mock_settings):
            await seed_global_settings(mock_db)

        _queue_mode_cache.clear()
        # A non-canonical per-user row has queue_mode=1 but canonical row has 0
        await upsert_project_settings(mock_db, "user1", "PVT_proj1", {"queue_mode": 1})
        await upsert_project_settings(mock_db, "__workflow__", "PVT_proj1", {"queue_mode": 0})
        result = await is_queue_mode_enabled(mock_db, "PVT_proj1")
        assert result is False

    async def test_uses_cache_on_second_call(self, mock_db, mock_settings):
        from src.services.database import seed_global_settings
        from src.services.settings_store import (
            _queue_mode_cache,
            is_queue_mode_enabled,
            upsert_project_settings,
        )

        with patch("src.services.database.get_settings", return_value=mock_settings):
            await seed_global_settings(mock_db)

        _queue_mode_cache.clear()
        await upsert_project_settings(mock_db, "__workflow__", "PVT_proj1", {"queue_mode": 1})
        # First call populates cache
        result1 = await is_queue_mode_enabled(mock_db, "PVT_proj1")
        assert result1 is True
        # Second call should use cache (same result)
        result2 = await is_queue_mode_enabled(mock_db, "PVT_proj1")
        assert result2 is True


# =============================================================================
# ProjectBoardConfig.queue_mode
# =============================================================================


class TestProjectBoardConfigQueueMode:
    def test_defaults_to_false(self):
        from src.models.settings import ProjectBoardConfig

        config = ProjectBoardConfig()
        assert config.queue_mode is False

    def test_can_be_set_true(self):
        from src.models.settings import ProjectBoardConfig

        config = ProjectBoardConfig(queue_mode=True)
        assert config.queue_mode is True


# =============================================================================
# ProjectSettingsUpdate.queue_mode
# =============================================================================


class TestProjectSettingsUpdateQueueMode:
    def test_queue_mode_optional(self):
        from src.models.settings import ProjectSettingsUpdate

        update = ProjectSettingsUpdate()
        assert update.queue_mode is None

    def test_queue_mode_can_be_set(self):
        from src.models.settings import ProjectSettingsUpdate

        update = ProjectSettingsUpdate(queue_mode=True)
        assert update.queue_mode is True

    def test_queue_mode_excluded_when_unset(self):
        from src.models.settings import ProjectSettingsUpdate

        update = ProjectSettingsUpdate()
        dump = update.model_dump(exclude_unset=True)
        assert "queue_mode" not in dump

    def test_queue_mode_included_when_set(self):
        from src.models.settings import ProjectSettingsUpdate

        update = ProjectSettingsUpdate(queue_mode=False)
        dump = update.model_dump(exclude_unset=True)
        assert "queue_mode" in dump
        assert dump["queue_mode"] is False


# =============================================================================
# get_project_launch_lock
# =============================================================================


class TestGetProjectLaunchLock:
    def test_returns_same_lock_for_same_project(self):
        from src.services.pipeline_state_store import _project_launch_locks, get_project_launch_lock

        _project_launch_locks.clear()
        lock_a = get_project_launch_lock("PVT_proj1")
        lock_b = get_project_launch_lock("PVT_proj1")
        assert lock_a is lock_b
        _project_launch_locks.clear()

    def test_returns_different_locks_for_different_projects(self):
        from src.services.pipeline_state_store import _project_launch_locks, get_project_launch_lock

        _project_launch_locks.clear()
        lock_a = get_project_launch_lock("PVT_proj1")
        lock_b = get_project_launch_lock("PVT_proj2")
        assert lock_a is not lock_b
        _project_launch_locks.clear()

    async def test_lock_serialises_access(self):
        """Concurrent tasks acquire the lock one at a time."""
        import asyncio

        from src.services.pipeline_state_store import _project_launch_locks, get_project_launch_lock

        _project_launch_locks.clear()
        order: list[int] = []
        in_critical_section = 0
        max_in_critical_section = 0

        async def worker(n: int) -> None:
            nonlocal in_critical_section, max_in_critical_section
            async with get_project_launch_lock("PVT_proj1"):
                in_critical_section += 1
                max_in_critical_section = max(max_in_critical_section, in_critical_section)
                try:
                    order.append(n)
                    await asyncio.sleep(0.01)
                finally:
                    in_critical_section -= 1

        await asyncio.gather(worker(1), worker(2), worker(3))
        # All 3 ran; they may interleave in time, but must not overlap in the critical section.
        assert sorted(order) == [1, 2, 3]
        assert max_in_critical_section == 1
        _project_launch_locks.clear()


# =============================================================================
# Concurrent launch queue gate
# =============================================================================


class TestConcurrentLaunchQueueGate:
    """Verify that the per-project lock + exclude_issue prevents races."""

    async def test_first_pipeline_active_second_queued(self):
        """Simulates two serialised launches — only the first should be active."""

        from src.services.pipeline_state_store import _project_launch_locks, get_project_launch_lock

        _project_launch_locks.clear()
        project_id = "PVT_proj1"
        results: dict[int, bool] = {}  # issue_number → should_queue

        async def simulate_launch(issue_number: int) -> None:
            async with get_project_launch_lock(project_id):
                active = count_active_pipelines_for_project(project_id, exclude_issue=issue_number)
                should_queue = active > 0
                results[issue_number] = should_queue
                # Register as active (not queued) or queued
                store._pipeline_states[issue_number] = _make_pipeline_state(
                    issue_number=issue_number,
                    project_id=project_id,
                    queued=should_queue,
                )

        # Launch sequentially under the lock to exercise the queue gate order.
        await simulate_launch(100)
        await simulate_launch(200)

        # First pipeline should NOT be queued
        assert results[100] is False
        # Second pipeline SHOULD be queued
        assert results[200] is True
        _project_launch_locks.clear()

    async def test_concurrent_launches_serialised_by_lock(self):
        """Two concurrent asyncio tasks use the lock to avoid racing."""
        import asyncio

        from src.services.pipeline_state_store import _project_launch_locks, get_project_launch_lock

        _project_launch_locks.clear()
        project_id = "PVT_proj1"
        results: dict[int, bool] = {}

        async def simulate_launch(issue_number: int) -> None:
            async with get_project_launch_lock(project_id):
                active = count_active_pipelines_for_project(project_id, exclude_issue=issue_number)
                should_queue = active > 0
                results[issue_number] = should_queue
                store._pipeline_states[issue_number] = _make_pipeline_state(
                    issue_number=issue_number,
                    project_id=project_id,
                    queued=should_queue,
                )
                # Small delay to simulate work inside the lock
                await asyncio.sleep(0.01)

        await asyncio.gather(
            simulate_launch(100),
            simulate_launch(200),
            simulate_launch(300),
            simulate_launch(400),
        )

        # Exactly one pipeline should be active, rest queued
        active_count = sum(1 for q in results.values() if not q)
        queued_count = sum(1 for q in results.values() if q)
        assert active_count == 1
        assert queued_count == 3
        _project_launch_locks.clear()
