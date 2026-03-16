from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import aiosqlite
import pytest

from src.services import pipeline_state_store
from src.services.workflow_orchestrator.models import PipelineState


@pytest.mark.asyncio
async def test_set_pipeline_state_skips_l1_update_when_sqlite_execute_fails(mock_db) -> None:
    issue_number = 901
    await pipeline_state_store.init_pipeline_state_store(mock_db)
    pipeline_state_store._pipeline_states.clear()

    state = PipelineState(
        issue_number=issue_number,
        project_id="PVT_test",
        status="running",
        agents=["copilot-plan"],
        started_at=datetime.now(UTC),
    )

    original_execute = mock_db.execute

    async def failing_execute(*args, **kwargs):
        if "INSERT INTO pipeline_states" in args[0]:
            raise aiosqlite.OperationalError("simulated write failure")
        return await original_execute(*args, **kwargs)

    mock_db.execute = failing_execute  # type: ignore[method-assign]

    await pipeline_state_store.set_pipeline_state(issue_number, state)

    assert pipeline_state_store.get_pipeline_state(issue_number) is None


@pytest.mark.asyncio
async def test_set_pipeline_state_skips_l1_update_when_commit_is_cancelled(mock_db) -> None:
    issue_number = 902
    await pipeline_state_store.init_pipeline_state_store(mock_db)
    pipeline_state_store._pipeline_states.clear()

    state = PipelineState(
        issue_number=issue_number,
        project_id="PVT_test",
        status="running",
        agents=["copilot-plan"],
        started_at=datetime.now(UTC),
    )

    mock_db.commit = AsyncMock(side_effect=asyncio.CancelledError())  # type: ignore[method-assign]

    with pytest.raises(asyncio.CancelledError):
        await pipeline_state_store.set_pipeline_state(issue_number, state)

    assert pipeline_state_store.get_pipeline_state(issue_number) is None
