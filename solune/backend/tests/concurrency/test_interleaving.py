from __future__ import annotations

import asyncio

import pytest

from src.services.copilot_polling import state as polling_state_module


@pytest.mark.asyncio
@pytest.mark.xfail(strict=True, reason="module-level polling state allows stale writes")
async def test_forced_interleaving_should_preserve_latest_error(
    isolated_polling_globals,
    fresh_polling_state,
) -> None:
    fresh_polling_state.last_error = "initial"

    async def first_writer(resume: asyncio.Event, other_resumed: asyncio.Event) -> None:
        observed = fresh_polling_state.last_error
        other_resumed.set()
        await resume.wait()
        polling_state_module._polling_state.last_error = f"{observed}-stale"

    async def second_writer(resume: asyncio.Event, other_resumed: asyncio.Event) -> None:
        await resume.wait()
        polling_state_module._polling_state.last_error = "newest"
        other_resumed.set()

    first_can_resume = asyncio.Event()
    second_can_resume = asyncio.Event()

    first_task = asyncio.create_task(first_writer(first_can_resume, second_can_resume))
    second_task = asyncio.create_task(second_writer(second_can_resume, first_can_resume))

    await asyncio.sleep(0)
    second_can_resume.set()
    await asyncio.sleep(0)
    first_can_resume.set()

    await asyncio.gather(first_task, second_task)

    assert polling_state_module._polling_state.last_error == "newest"
