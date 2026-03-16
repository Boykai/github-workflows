"""Property tests: Pipeline state transition sequences.

Verifies invariants of the linear pipeline state machine (backlog → ready → in_progress → in_review).
"""

from hypothesis import given
from hypothesis import strategies as st

from src.models.agent import AgentAssignment
from src.models.workflow import WorkflowConfiguration
from src.services.workflow_orchestrator.models import (
    WorkflowState,
    find_next_actionable_status,
    get_next_status,
    get_status_order,
)


def _make_config(
    agent_mappings: dict | None = None,
    backlog: str = "Backlog",
    ready: str = "Ready",
    in_progress: str = "In Progress",
    in_review: str = "In Review",
) -> WorkflowConfiguration:
    return WorkflowConfiguration(
        project_id="PVT_test",
        repository_owner="test-owner",
        repository_name="test-repo",
        status_backlog=backlog,
        status_ready=ready,
        status_in_progress=in_progress,
        status_in_review=in_review,
        agent_mappings=agent_mappings or {},
    )


class TestGetStatusOrder:
    """Property: status order always has exactly 4 elements matching config."""

    @given(
        backlog=st.text(min_size=1, max_size=30, alphabet=st.characters(categories=("L",))),
        ready=st.text(min_size=1, max_size=30, alphabet=st.characters(categories=("L",))),
        in_progress=st.text(min_size=1, max_size=30, alphabet=st.characters(categories=("L",))),
        in_review=st.text(min_size=1, max_size=30, alphabet=st.characters(categories=("L",))),
    )
    def test_order_always_four_elements(
        self,
        backlog: str,
        ready: str,
        in_progress: str,
        in_review: str,
    ) -> None:
        config = _make_config(
            backlog=backlog,
            ready=ready,
            in_progress=in_progress,
            in_review=in_review,
        )
        order = get_status_order(config)
        assert len(order) == 4
        assert order == [backlog, ready, in_progress, in_review]


class TestGetNextStatus:
    """Property: get_next_status advances through the 4-column pipeline linearly."""

    def test_last_status_returns_none(self) -> None:
        config = _make_config()
        assert get_next_status(config, "In Review") is None

    def test_invalid_status_returns_none(self) -> None:
        config = _make_config()
        assert get_next_status(config, "NonExistent") is None

    @given(idx=st.integers(min_value=0, max_value=2))
    def test_non_terminal_status_advances(self, idx: int) -> None:
        config = _make_config()
        order = get_status_order(config)
        result = get_next_status(config, order[idx])
        assert result == order[idx + 1]

    def test_full_traversal(self) -> None:
        """Walking the entire pipeline produces all statuses then None."""
        config = _make_config()
        order = get_status_order(config)
        current = order[0]
        visited = [current]
        while True:
            nxt = get_next_status(config, current)
            if nxt is None:
                break
            visited.append(nxt)
            current = nxt
        assert visited == order


class TestFindNextActionableStatus:
    """Property: find_next_actionable_status skips statuses without agents."""

    def test_skips_to_status_with_agents(self) -> None:
        config = _make_config(
            agent_mappings={
                "Backlog": [],
                "Ready": [],
                "In Progress": [AgentAssignment(slug="reviewer")],
                "In Review": [],
            },
        )
        result = find_next_actionable_status(config, "Backlog")
        assert result == "In Progress"

    def test_returns_last_status_even_without_agents(self) -> None:
        config = _make_config(agent_mappings={})
        result = find_next_actionable_status(config, "Backlog")
        # Should return "In Review" as the final status
        assert result == "In Review"

    def test_returns_none_when_already_last(self) -> None:
        config = _make_config()
        result = find_next_actionable_status(config, "In Review")
        assert result is None


class TestWorkflowStateEnumCoverage:
    """Property: all WorkflowState values round-trip through .value."""

    @given(state=st.sampled_from(list(WorkflowState)))
    def test_value_roundtrip(self, state: WorkflowState) -> None:
        assert WorkflowState(state.value) is state
