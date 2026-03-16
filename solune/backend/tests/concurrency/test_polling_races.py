from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from src.services.copilot_polling import state as polling_state_module


@pytest.mark.asyncio
async def test_bounded_polling_collections_stay_within_capacity(
    isolated_polling_globals,
    utc_now: datetime,
) -> None:
    async def populate(worker_id: int) -> None:
        for offset in range(200):
            issue_key = f"{worker_id}:{offset}"
            polling_state_module._processed_issue_prs.add(issue_key)
            polling_state_module._pending_agent_assignments[issue_key] = utc_now
            polling_state_module._claimed_child_prs.add(f"claim:{issue_key}")
            await asyncio.sleep(0)

    await asyncio.gather(*(populate(worker_id) for worker_id in range(10)))

    assert (
        len(polling_state_module._processed_issue_prs)
        <= polling_state_module._processed_issue_prs.maxlen
    )
    assert (
        len(polling_state_module._pending_agent_assignments)
        <= polling_state_module._pending_agent_assignments.maxlen
    )
    assert (
        len(polling_state_module._claimed_child_prs)
        <= polling_state_module._claimed_child_prs.maxlen
    )


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="polling task start is not synchronized")
async def test_concurrent_start_attempts_should_never_create_duplicate_polling_tasks(
    isolated_polling_globals,
) -> None:
    created_tasks: list[asyncio.Task[None]] = []
    gate = asyncio.Event()

    async def start_attempt() -> None:
        if polling_state_module._polling_task is None:
            await gate.wait()
            task = asyncio.create_task(asyncio.sleep(60))
            created_tasks.append(task)
            polling_state_module._polling_task = task
            polling_state_module._polling_state.is_running = True

    try:
        starters = [asyncio.create_task(start_attempt()) for _ in range(2)]
        await asyncio.sleep(0)
        gate.set()
        await asyncio.gather(*starters)

        assert len(created_tasks) == 1
    finally:
        for task in created_tasks:
            task.cancel()
        await asyncio.gather(*created_tasks, return_exceptions=True)
