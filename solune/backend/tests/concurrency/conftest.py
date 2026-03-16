from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import ExitStack
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest

from src.services.copilot_polling import state as polling_state_module
from src.services.copilot_polling.state import PollingState
from src.utils import BoundedDict, BoundedSet


@pytest.fixture
def fresh_polling_state() -> PollingState:
    return PollingState()


@pytest.fixture
def isolated_polling_globals(fresh_polling_state: PollingState):
    with ExitStack() as stack:
        stack.enter_context(
            patch.object(polling_state_module, "_polling_state", fresh_polling_state)
        )
        stack.enter_context(patch.object(polling_state_module, "_polling_task", None))
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_processed_issue_prs",
                BoundedSet[str](maxlen=1000),
            )
        )
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_posted_agent_outputs",
                BoundedSet[str](maxlen=500),
            )
        )
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_claimed_child_prs",
                BoundedSet[str](maxlen=500),
            )
        )
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_pending_agent_assignments",
                BoundedDict[str, datetime](maxlen=500),
            )
        )
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_system_marked_ready_prs",
                BoundedSet[int](maxlen=500),
            )
        )
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_copilot_review_first_detected",
                BoundedDict[int, datetime](maxlen=200),
            )
        )
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_copilot_review_requested_at",
                BoundedDict[int, datetime](maxlen=200),
            )
        )
        stack.enter_context(
            patch.object(
                polling_state_module,
                "_recovery_last_attempt",
                BoundedDict[int, datetime](maxlen=200),
            )
        )
        stack.enter_context(patch.object(polling_state_module, "_consecutive_idle_polls", 0))
        yield fresh_polling_state


@pytest.fixture
def utc_now() -> datetime:
    return datetime.now(UTC)


async def run_concurrent(*coroutines: Awaitable[Any]) -> list[Any]:
    return list(await asyncio.gather(*coroutines))


async def force_interleave(
    first_step: Callable[[asyncio.Event, asyncio.Event], Awaitable[Any]],
    second_step: Callable[[asyncio.Event, asyncio.Event], Awaitable[Any]],
) -> tuple[Any, Any]:
    first_can_resume = asyncio.Event()
    second_can_resume = asyncio.Event()

    first_task = asyncio.create_task(first_step(first_can_resume, second_can_resume))
    second_task = asyncio.create_task(second_step(second_can_resume, first_can_resume))

    second_can_resume.set()
    await asyncio.sleep(0)
    first_can_resume.set()

    return await asyncio.gather(first_task, second_task)
