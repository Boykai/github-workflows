"""Tests for workflow_orchestrator/transitions.py — state, branch, and sub-issue management."""

from __future__ import annotations

import warnings

import pytest

from src.services.workflow_orchestrator.models import PipelineState
from src.services.workflow_orchestrator.transitions import (
    _agent_trigger_key,
    clear_all_agent_trigger_buffers,
    clear_issue_main_branch,
    clear_issue_sub_issues,
    get_all_pipeline_states,
    get_issue_main_branch,
    get_issue_sub_issues,
    get_pipeline_state,
    release_agent_trigger,
    remove_pipeline_state,
    set_issue_main_branch,
    set_issue_sub_issues,
    set_pipeline_state,
    should_skip_agent_trigger,
    update_issue_main_branch_sha,
)


@pytest.fixture(autouse=True)
def _clean_transition_state():
    """Ensure clean state for each test."""
    from src.services.pipeline_state_store import (
        _agent_trigger_inflight,
        _issue_main_branches,
        _issue_sub_issue_map,
        _pipeline_states,
    )

    _pipeline_states.clear()
    _issue_main_branches.clear()
    _issue_sub_issue_map.clear()
    _agent_trigger_inflight.clear()
    yield
    _pipeline_states.clear()
    _issue_main_branches.clear()
    _issue_sub_issue_map.clear()
    _agent_trigger_inflight.clear()


# ── Agent Trigger Key ──


class TestAgentTriggerKey:
    def test_key_format(self):
        key = _agent_trigger_key(42, "In Progress", "builder")
        assert key == "42:in progress:builder"

    def test_lowercased_status(self):
        key = _agent_trigger_key(1, "BACKLOG", "planner")
        assert key == "1:backlog:planner"


# ── Pipeline State CRUD ──


class TestPipelineStateCRUD:
    def test_get_returns_none_initially(self):
        assert get_pipeline_state(999) is None

    def test_set_and_get(self):
        ps = PipelineState(
            issue_number=42,
            project_id="PVT_test",
            status="In Progress",
            agents=["planner", "builder"],
        )
        set_pipeline_state(42, ps)
        result = get_pipeline_state(42)
        assert result is not None
        assert result.issue_number == 42
        assert result.status == "In Progress"
        assert result.agents == ["planner", "builder"]

    def test_remove(self):
        ps = PipelineState(issue_number=10, project_id="PVT_test", status="idle", agents=[])
        set_pipeline_state(10, ps)
        assert get_pipeline_state(10) is not None
        remove_pipeline_state(10)
        assert get_pipeline_state(10) is None

    def test_remove_nonexistent_is_safe(self):
        remove_pipeline_state(9999)  # Should not raise

    def test_get_all_pipeline_states(self):
        ps1 = PipelineState(issue_number=1, project_id="P1", status="a", agents=[])
        ps2 = PipelineState(issue_number=2, project_id="P2", status="b", agents=[])
        set_pipeline_state(1, ps1)
        set_pipeline_state(2, ps2)
        all_states = get_all_pipeline_states()
        assert len(all_states) == 2
        assert 1 in all_states
        assert 2 in all_states


# ── Main Branch Tracking ──


class TestMainBranchTracking:
    def test_get_returns_none_initially(self):
        assert get_issue_main_branch(100) is None

    def test_set_and_get(self):
        set_issue_main_branch(100, "copilot/feature-branch", 50, "abc123")
        result = get_issue_main_branch(100)
        assert result is not None
        assert result["branch"] == "copilot/feature-branch"
        assert result["pr_number"] == 50
        assert result["head_sha"] == "abc123"

    def test_set_does_not_overwrite_existing(self):
        """Once set, the main branch should not be overwritten."""
        set_issue_main_branch(100, "first-branch", 1)
        set_issue_main_branch(100, "second-branch", 2)
        result = get_issue_main_branch(100)
        assert result["branch"] == "first-branch"
        assert result["pr_number"] == 1

    def test_clear(self):
        set_issue_main_branch(100, "branch", 1)
        clear_issue_main_branch(100)
        assert get_issue_main_branch(100) is None

    def test_update_head_sha(self):
        set_issue_main_branch(200, "branch", 10, "old_sha")
        update_issue_main_branch_sha(200, "new_sha_abc")
        result = get_issue_main_branch(200)
        assert result["head_sha"] == "new_sha_abc"

    def test_update_sha_when_no_branch_is_noop(self):
        """Updating SHA for a non-existent branch should be a no-op."""
        update_issue_main_branch_sha(999, "some_sha")
        assert get_issue_main_branch(999) is None


# ── Sub-Issue Mapping ──


class TestSubIssueMapping:
    def test_get_returns_empty_dict_initially(self):
        assert get_issue_sub_issues(100) == {}

    def test_set_and_get(self):
        mappings = {
            "planner": {"number": 101, "node_id": "N1", "url": "u1"},
            "builder": {"number": 102, "node_id": "N2", "url": "u2"},
        }
        set_issue_sub_issues(100, mappings)
        result = get_issue_sub_issues(100)
        assert "planner" in result
        assert result["planner"]["number"] == 101

    def test_merge_behavior(self):
        """set_issue_sub_issues should merge with existing mappings."""
        set_issue_sub_issues(100, {"planner": {"number": 101}})
        set_issue_sub_issues(100, {"builder": {"number": 102}})
        result = get_issue_sub_issues(100)
        assert "planner" in result
        assert "builder" in result

    def test_clear(self):
        set_issue_sub_issues(100, {"agent": {"number": 1}})
        clear_issue_sub_issues(100)
        assert get_issue_sub_issues(100) == {}


# ── Agent Trigger Skipping ──


class TestAgentTriggerSkipping:
    def test_first_call_does_not_skip(self):
        skip, age = should_skip_agent_trigger(42, "Ready", "planner")
        assert skip is False
        assert age == 0.0

    def test_second_call_skips(self):
        should_skip_agent_trigger(42, "Ready", "planner")
        skip, age = should_skip_agent_trigger(42, "Ready", "planner")
        assert skip is True
        assert age >= 0.0

    def test_release_allows_retrigger(self):
        should_skip_agent_trigger(42, "Ready", "planner")
        release_agent_trigger(42, "Ready", "planner")
        skip, _ = should_skip_agent_trigger(42, "Ready", "planner")
        assert skip is False

    def test_clear_all_buffers(self):
        should_skip_agent_trigger(1, "Ready", "a")
        should_skip_agent_trigger(2, "Backlog", "b")
        clear_all_agent_trigger_buffers()
        skip1, _ = should_skip_agent_trigger(1, "Ready", "a")
        skip2, _ = should_skip_agent_trigger(2, "Backlog", "b")
        assert skip1 is False
        assert skip2 is False


# ── Schedule Persist Safety ──


class TestSchedulePersistSafety:
    def test_no_runtime_warning_when_no_event_loop(self):
        """Calling clear_all_agent_trigger_buffers must not leave unawaited coroutines."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", RuntimeWarning)
            clear_all_agent_trigger_buffers()

        unawaited = [
            w
            for w in caught
            if issubclass(w.category, RuntimeWarning) and "never awaited" in str(w.message)
        ]
        assert unawaited == [], (
            f"Unawaited coroutine warnings: {[str(w.message) for w in unawaited]}"
        )
