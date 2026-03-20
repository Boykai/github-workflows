from __future__ import annotations

from datetime import UTC, datetime

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule

from src.services.workflow_orchestrator.models import PipelineGroupInfo, PipelineState


@settings(max_examples=200, stateful_step_count=50)
class PipelineStateMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self._agents = ["planner", "builder", "reviewer"]
        self._reset_state()

    def _reset_state(self) -> None:
        self.state = PipelineState(
            issue_number=101,
            project_id="PVT_test",
            status="idle",
            agents=list(self._agents),
        )

    @rule()
    @precondition(lambda self: self.state.status == "idle")
    def start_pipeline(self) -> None:
        self.state.status = "running"
        self.state.started_at = datetime.now(UTC)

    @rule()
    @precondition(
        lambda self: (
            self.state.status == "running"
            and self.state.execution_mode == "sequential"
            and self.state.current_agent_index < len(self.state.agents)
        )
    )
    def advance_agent(self) -> None:
        current_agent = self.state.agents[self.state.current_agent_index]
        if current_agent not in self.state.completed_agents:
            self.state.completed_agents.append(current_agent)
        self.state.current_agent_index += 1
        if self.state.current_agent_index >= len(self.state.agents):
            self.state.status = "completed"

    @rule()
    @precondition(lambda self: self.state.status == "running")
    def fail_pipeline(self) -> None:
        self.state.status = "failed"
        self.state.error = "simulated failure"

    @rule()
    @precondition(lambda self: self.state.status in {"idle", "running"})
    def cancel_pipeline(self) -> None:
        self.state.status = "cancelled"

    @rule()
    @precondition(lambda self: self.state.status in {"completed", "failed", "cancelled"})
    def reset_model(self) -> None:
        self._reset_state()

    @rule()
    @precondition(lambda self: self.state.status == "idle")
    def enable_parallel_mode(self) -> None:
        self.state.execution_mode = "parallel"
        self.state.status = "running"
        self.state.parallel_agent_statuses = dict.fromkeys(self.state.agents, "pending")
        self.state.started_at = datetime.now(UTC)

    @rule()
    @precondition(
        lambda self: (
            self.state.status == "running"
            and self.state.execution_mode == "parallel"
            and any(status == "pending" for status in self.state.parallel_agent_statuses.values())
        )
    )
    def complete_parallel_agent(self) -> None:
        for agent in self.state.agents:
            if self.state.parallel_agent_statuses.get(agent) == "pending":
                self.state.parallel_agent_statuses[agent] = "completed"
                if agent not in self.state.completed_agents:
                    self.state.completed_agents.append(agent)
                break
        if all(
            status in {"completed", "failed"}
            for status in self.state.parallel_agent_statuses.values()
        ):
            self.state.status = "completed"

    @invariant()
    def current_agent_index_in_bounds(self) -> None:
        assert 0 <= self.state.current_agent_index <= len(self.state.agents)

    @invariant()
    def completed_agents_are_subset(self) -> None:
        assert set(self.state.completed_agents).issubset(set(self.state.agents))

    @invariant()
    def terminal_states_do_not_have_current_agent(self) -> None:
        if self.state.status == "completed":
            assert self.state.is_complete
        if self.state.status in {"failed", "cancelled"}:
            assert self.state.status != "running"

    @invariant()
    def parallel_completion_requires_all_agents_accounted_for(self) -> None:
        if self.state.execution_mode == "parallel" and self.state.status == "completed":
            assert self.state.parallel_agent_statuses
            assert all(
                status in {"completed", "failed"}
                for status in self.state.parallel_agent_statuses.values()
            )


TestPipelineStateMachine = PipelineStateMachine.TestCase


_agent_names = st.lists(
    st.text(
        alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="\x00"),
        min_size=1,
        max_size=12,
    ),
    min_size=1,
    max_size=4,
    unique=True,
)


@settings(max_examples=150)
@given(_agent_names)
def test_parallel_state_completion_accepts_completed_and_failed_agents(agents: list[str]) -> None:
    statuses = {
        agent: ("completed" if index % 2 == 0 else "failed") for index, agent in enumerate(agents)
    }
    state = PipelineState(
        issue_number=101,
        project_id="PVT_test",
        status="running",
        agents=agents,
        execution_mode="parallel",
        parallel_agent_statuses=statuses,
        failed_agents=[agent for agent, value in statuses.items() if value == "failed"],
    )

    assert state.is_complete is True
    assert state.is_parallel_stage_failed is (len(state.failed_agents) > 0)


@settings(max_examples=120)
@given(_agent_names)
def test_grouped_pipeline_skips_empty_groups_for_current_agent(agents: list[str]) -> None:
    state = PipelineState(
        issue_number=101,
        project_id="PVT_test",
        status="running",
        agents=agents,
        groups=[
            PipelineGroupInfo(group_id="empty", execution_mode="sequential", agents=[]),
            PipelineGroupInfo(group_id="active", execution_mode="sequential", agents=agents),
        ],
    )

    assert state.current_agent == agents[0]


@settings(max_examples=120)
@given(_agent_names)
def test_grouped_parallel_pipeline_requires_status_for_every_agent(agents: list[str]) -> None:
    partial_statuses = dict.fromkeys(agents[:-1], "completed")
    state = PipelineState(
        issue_number=101,
        project_id="PVT_test",
        status="running",
        agents=agents,
        groups=[
            PipelineGroupInfo(
                group_id="parallel",
                execution_mode="parallel",
                agents=agents,
                agent_statuses=partial_statuses,
            )
        ],
    )

    assert state.is_complete is False
