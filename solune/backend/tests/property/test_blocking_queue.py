"""Property-based tests for pipeline blocking queue operations.

Exercises:
- count_active_pipelines_for_project() with random pipeline state combinations
- get_queued_pipelines_for_project() FIFO ordering invariant
- should_skip_agent_trigger() exclusivity within grace period and stale reclaim

Uses Hypothesis with ≥200 examples per test to catch edge cases.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st

from src.services import pipeline_state_store as store
from src.services.pipeline_state_store import (
    count_active_pipelines_for_project,
    get_queued_pipelines_for_project,
)
from src.services.workflow_orchestrator.models import PipelineState
from src.services.workflow_orchestrator.transitions import (
    release_agent_trigger,
    should_skip_agent_trigger,
)

# ── Strategies ──────────────────────────────────────────────────────

_project_ids = st.sampled_from(["PVT_proj1", "PVT_proj2", "PVT_proj3"])
_issue_numbers = st.integers(min_value=1, max_value=9999)
_queued_flags = st.booleans()
_timestamps = st.datetimes(
    min_value=datetime(2026, 1, 1),
    max_value=datetime(2026, 12, 31),
    timezones=st.just(UTC),
)

_pipeline_entry = st.fixed_dictionaries(
    {
        "issue_number": _issue_numbers,
        "project_id": _project_ids,
        "queued": _queued_flags,
        "started_at": _timestamps,
    }
)

_pipeline_lists = st.lists(_pipeline_entry, min_size=0, max_size=20)


def _make_pipeline_state(**overrides) -> PipelineState:
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


# ── count_active_pipelines_for_project (T048) ──────────────────────


@settings(max_examples=200)
@given(pipelines=_pipeline_lists, target_project=_project_ids)
def test_count_active_matches_manual_count(pipelines: list[dict], target_project: str) -> None:
    """count_active_pipelines_for_project returns the exact number of
    non-queued pipelines matching the given project_id."""
    store._pipeline_states.clear()

    # Deduplicate by issue_number (last write wins)
    deduped: dict[int, dict] = {}
    for p in pipelines:
        deduped[p["issue_number"]] = p

    for p in deduped.values():
        store._pipeline_states[p["issue_number"]] = _make_pipeline_state(**p)

    expected = sum(
        1 for p in deduped.values() if p["project_id"] == target_project and not p["queued"]
    )

    assert count_active_pipelines_for_project(target_project) == expected
    store._pipeline_states.clear()


@settings(max_examples=200)
@given(pipelines=_pipeline_lists, target_project=_project_ids)
def test_count_active_never_negative(pipelines: list[dict], target_project: str) -> None:
    """Active pipeline count is always ≥ 0."""
    store._pipeline_states.clear()

    deduped: dict[int, dict] = {}
    for p in pipelines:
        deduped[p["issue_number"]] = p

    for p in deduped.values():
        store._pipeline_states[p["issue_number"]] = _make_pipeline_state(**p)

    assert count_active_pipelines_for_project(target_project) >= 0
    store._pipeline_states.clear()


# ── get_queued_pipelines_for_project FIFO ordering (T049) ──────────


@settings(max_examples=200)
@given(pipelines=_pipeline_lists, target_project=_project_ids)
def test_queued_pipelines_sorted_by_started_at(pipelines: list[dict], target_project: str) -> None:
    """Queued pipelines are always returned sorted by started_at (FIFO)."""
    store._pipeline_states.clear()

    deduped: dict[int, dict] = {}
    for p in pipelines:
        deduped[p["issue_number"]] = p

    for p in deduped.values():
        store._pipeline_states[p["issue_number"]] = _make_pipeline_state(**p)

    queued = get_queued_pipelines_for_project(target_project)

    # Verify FIFO ordering: started_at is non-decreasing
    for i in range(len(queued) - 1):
        t1 = queued[i].started_at or datetime.min.replace(tzinfo=UTC)
        t2 = queued[i + 1].started_at or datetime.min.replace(tzinfo=UTC)
        assert t1 <= t2, f"FIFO violated: {t1} > {t2}"

    store._pipeline_states.clear()


@settings(max_examples=200)
@given(pipelines=_pipeline_lists, target_project=_project_ids)
def test_queued_pipelines_only_contains_queued(pipelines: list[dict], target_project: str) -> None:
    """All returned pipelines must have queued=True and matching project_id."""
    store._pipeline_states.clear()

    deduped: dict[int, dict] = {}
    for p in pipelines:
        deduped[p["issue_number"]] = p

    for p in deduped.values():
        store._pipeline_states[p["issue_number"]] = _make_pipeline_state(**p)

    queued = get_queued_pipelines_for_project(target_project)

    for p in queued:
        assert p.queued is True
        assert p.project_id == target_project

    store._pipeline_states.clear()


# ── should_skip_agent_trigger grace period (T050) ──────────────────


def test_first_trigger_not_skipped() -> None:
    """First call for a given issue/status/agent should NOT skip."""
    store._agent_trigger_inflight.clear()
    skip, age = should_skip_agent_trigger(9999, "Ready", "test-agent")
    assert skip is False
    assert age == 0.0
    # Clean up
    release_agent_trigger(9999, "Ready", "test-agent")
    store._agent_trigger_inflight.clear()


def test_duplicate_trigger_within_grace_period_is_skipped() -> None:
    """Second call within grace period should skip (exclusivity)."""
    store._agent_trigger_inflight.clear()
    skip1, _ = should_skip_agent_trigger(8888, "Ready", "test-agent")
    assert skip1 is False

    # Immediate second call — should be skipped
    skip2, age2 = should_skip_agent_trigger(8888, "Ready", "test-agent")
    assert skip2 is True
    assert age2 >= 0.0

    release_agent_trigger(8888, "Ready", "test-agent")
    store._agent_trigger_inflight.clear()


def test_stale_trigger_reclaimed_after_timeout() -> None:
    """After stale_seconds, a trigger is reclaimed (not skipped)."""
    store._agent_trigger_inflight.clear()
    # First claim
    skip1, _ = should_skip_agent_trigger(7777, "Ready", "test-agent", stale_seconds=0)
    assert skip1 is False

    # With stale_seconds=0, next call should reclaim immediately
    time.sleep(0.01)
    skip2, age2 = should_skip_agent_trigger(7777, "Ready", "test-agent", stale_seconds=0)
    assert skip2 is False
    assert age2 == 0.0

    release_agent_trigger(7777, "Ready", "test-agent")
    store._agent_trigger_inflight.clear()


def test_release_allows_new_trigger() -> None:
    """After release, a new trigger should not be skipped."""
    store._agent_trigger_inflight.clear()
    skip1, _ = should_skip_agent_trigger(6666, "Ready", "test-agent")
    assert skip1 is False

    release_agent_trigger(6666, "Ready", "test-agent")

    skip2, _ = should_skip_agent_trigger(6666, "Ready", "test-agent")
    assert skip2 is False

    release_agent_trigger(6666, "Ready", "test-agent")
    store._agent_trigger_inflight.clear()
