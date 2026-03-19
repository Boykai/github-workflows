"""Chaos test: concurrent pipeline state updates.

Verifies that simultaneous updates to pipeline state from multiple
coroutines do not corrupt the in-memory state or lose updates.
"""

from __future__ import annotations

import asyncio

import pytest

from src.services.workflow_orchestrator.models import PipelineState
from src.services.workflow_orchestrator.transitions import (
    get_pipeline_state,
    remove_pipeline_state,
    set_pipeline_state,
)


@pytest.fixture(autouse=True)
def _clean_state():
    """Reset pipeline state for each test."""
    from src.services.pipeline_state_store import _pipeline_states

    _pipeline_states.clear()
    yield
    _pipeline_states.clear()


class TestConcurrentStateUpdates:
    """Verify integrity under concurrent pipeline state mutations."""

    @pytest.mark.asyncio
    async def test_concurrent_set_does_not_lose_updates(self):
        """Multiple concurrent set_pipeline_state calls should all succeed."""
        num_issues = 50

        async def _set_state(issue_num: int):
            ps = PipelineState(
                issue_number=issue_num,
                project_id="PVT_chaos",
                status="In Progress",
                agents=["builder"],
            )
            set_pipeline_state(issue_num, ps)
            await asyncio.sleep(0)  # Yield to event loop

        tasks = [_set_state(i) for i in range(num_issues)]
        await asyncio.gather(*tasks)

        for i in range(num_issues):
            state = get_pipeline_state(i)
            assert state is not None, f"State for issue #{i} was lost"
            assert state.issue_number == i

    @pytest.mark.asyncio
    async def test_concurrent_set_and_remove(self):
        """Concurrent set and remove should not raise or corrupt state."""
        ps = PipelineState(
            issue_number=100,
            project_id="PVT_chaos",
            status="idle",
            agents=["planner"],
        )
        set_pipeline_state(100, ps)

        async def _updater():
            for _ in range(20):
                set_pipeline_state(
                    100,
                    PipelineState(
                        issue_number=100,
                        project_id="PVT_chaos",
                        status="running",
                        agents=["builder"],
                    ),
                )
                await asyncio.sleep(0)

        async def _remover():
            for _ in range(20):
                remove_pipeline_state(100)
                await asyncio.sleep(0)

        # Run concurrently — should not raise
        await asyncio.gather(_updater(), _remover())

    @pytest.mark.asyncio
    async def test_rapid_status_transitions(self):
        """Rapidly changing pipeline status should converge to final state."""
        statuses = ["idle", "running", "completed", "failed", "idle"]
        ps = PipelineState(
            issue_number=200,
            project_id="PVT_chaos",
            status="idle",
            agents=["agent"],
        )
        set_pipeline_state(200, ps)

        async def _transition(status: str, delay: float):
            await asyncio.sleep(delay)
            ps = PipelineState(
                issue_number=200,
                project_id="PVT_chaos",
                status=status,
                agents=["agent"],
            )
            set_pipeline_state(200, ps)

        tasks = [_transition(s, i * 0.001) for i, s in enumerate(statuses)]
        await asyncio.gather(*tasks)

        # Final state should be the last one set
        final = get_pipeline_state(200)
        assert final is not None
        assert final.status == "idle"
