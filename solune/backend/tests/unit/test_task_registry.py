"""Unit tests for :mod:`src.services.task_registry`."""

from __future__ import annotations

import asyncio
import logging

import pytest

from src.services.task_registry import TaskRegistry

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _noop() -> str:
    return "ok"


async def _sleep_forever() -> None:
    await asyncio.sleep(3600)


async def _raise_error() -> None:
    raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCreateTask:
    """TaskRegistry.create_task() behaviour."""

    async def test_returns_asyncio_task(self) -> None:
        reg = TaskRegistry()
        task = reg.create_task(_noop(), name="test")
        assert isinstance(task, asyncio.Task)
        await task

    async def test_task_auto_removed_on_completion(self) -> None:
        reg = TaskRegistry()
        task = reg.create_task(_noop(), name="test")
        await task
        # Allow done-callback to fire.
        await asyncio.sleep(0)
        assert reg.pending_count == 0

    async def test_pending_count_reflects_running_tasks(self) -> None:
        reg = TaskRegistry()
        t1 = reg.create_task(_sleep_forever(), name="t1")
        t2 = reg.create_task(_sleep_forever(), name="t2")
        assert reg.pending_count == 2
        t1.cancel()
        t2.cancel()
        await asyncio.sleep(0.05)

    async def test_name_is_applied(self) -> None:
        reg = TaskRegistry()
        task = reg.create_task(_noop(), name="my-task")
        assert task.get_name() == "my-task"
        await task


class TestDrain:
    """TaskRegistry.drain() behaviour."""

    async def test_drain_empty_registry(self) -> None:
        reg = TaskRegistry()
        undrained = await reg.drain(drain_timeout=1.0)
        assert undrained == []

    async def test_drain_completes_fast_tasks(self) -> None:
        reg = TaskRegistry()
        reg.create_task(_noop(), name="fast")
        undrained = await reg.drain(drain_timeout=5.0)
        assert undrained == []
        assert reg.pending_count == 0

    async def test_drain_cancels_slow_tasks(self) -> None:
        reg = TaskRegistry()
        reg.create_task(_sleep_forever(), name="slow")
        undrained = await reg.drain(drain_timeout=0.1)
        # The slow task exceeded the drain timeout so it should be reported
        # even though cancellation eventually succeeds.
        assert len(undrained) == 1
        assert undrained[0].get_name() == "slow"
        await asyncio.sleep(0.05)
        assert reg.pending_count == 0


class TestCancelAll:
    """TaskRegistry.cancel_all() behaviour."""

    async def test_cancel_all_cancels_pending(self) -> None:
        reg = TaskRegistry()
        t1 = reg.create_task(_sleep_forever(), name="t1")
        t2 = reg.create_task(_sleep_forever(), name="t2")
        reg.cancel_all()
        await asyncio.sleep(0.05)
        assert t1.cancelled()
        assert t2.cancelled()


class TestExceptionLogging:
    """Failed tasks are logged at WARNING level."""

    async def test_exception_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        reg = TaskRegistry()
        with caplog.at_level(logging.WARNING):
            reg.create_task(_raise_error(), name="failing")
            await asyncio.sleep(0.05)
        assert any("boom" in r.message for r in caplog.records)


class TestConcurrentCreateDuringDrain:
    """Creating tasks while drain is in progress."""

    async def test_new_task_tracked_during_drain(self) -> None:
        reg = TaskRegistry()
        reg.create_task(_sleep_forever(), name="existing")

        async def _add_during_drain() -> None:
            await asyncio.sleep(0.01)
            reg.create_task(_noop(), name="new-during-drain")

        helper = TaskRegistry()
        helper.create_task(_add_during_drain(), name="helper")
        await reg.drain(drain_timeout=0.2)
        # The new task should have completed on its own.
        await asyncio.sleep(0.05)
        assert reg.pending_count == 0
