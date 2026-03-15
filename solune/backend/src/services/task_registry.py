"""Centralized registry for fire-and-forget ``asyncio`` tasks.

Every call to :func:`asyncio.create_task` that is *not* directly awaited by the
caller should go through :data:`task_registry` instead.  The registry:

* Tracks all pending tasks so none are silently garbage-collected.
* Logs failures at WARNING level with the task name and exception.
* Provides :meth:`drain` for graceful shutdown (await pending, cancel stragglers).
* Provides :meth:`cancel_all` for forceful shutdown.

Usage::

    from src.services.task_registry import task_registry

    task_registry.create_task(
        send_notification(user_id),
        name="signal-delivery-42",
    )
"""

from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger(__name__)


class TaskRegistry:
    """Singleton-style registry that tracks fire-and-forget tasks."""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()  # type: ignore[type-arg]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_task(
        self,
        coro: object,
        *,
        name: str | None = None,
    ) -> asyncio.Task:  # type: ignore[type-arg]
        """Create, register, and return an :class:`asyncio.Task`.

        A done-callback is automatically attached that removes the task from the
        registry and logs any exception at WARNING level.
        """
        task = asyncio.create_task(coro, name=name)  # type: ignore[arg-type]
        self._tasks.add(task)
        task.add_done_callback(self._task_done)
        return task

    async def drain(self, drain_timeout: float = 30.0) -> list[asyncio.Task]:  # type: ignore[type-arg]
        """Await all pending tasks up to *drain_timeout* seconds.

        Tasks that do not complete in time are cancelled and returned so the
        caller can inspect them.
        """
        pending = {t for t in self._tasks if not t.done()}
        if not pending:
            return []

        logger.info("TaskRegistry draining %d pending task(s) …", len(pending))
        _done, still_pending = await asyncio.wait(pending, timeout=drain_timeout)

        # Cancel tasks that exceeded the timeout.
        for t in still_pending:
            t.cancel()
        # Give cancelled tasks a chance to handle CancelledError.
        if still_pending:
            await asyncio.wait(still_pending, timeout=5.0)

        # Return all tasks that exceeded the initial timeout so callers
        # have full visibility, even if cancellation eventually succeeded.
        timed_out = list(still_pending)
        if timed_out:
            logger.warning(
                "TaskRegistry: %d task(s) exceeded drain timeout: %s",
                len(timed_out),
                [t.get_name() for t in timed_out],
            )
        return timed_out

    def cancel_all(self) -> None:
        """Cancel every non-done task in the registry."""
        for t in list(self._tasks):
            if not t.done():
                t.cancel()

    @property
    def pending_count(self) -> int:
        """Number of tasks that are still running or pending."""
        return sum(1 for t in self._tasks if not t.done())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _task_done(self, task: asyncio.Task) -> None:  # type: ignore[type-arg]
        """Done-callback: auto-remove from registry and log failures."""
        self._tasks.discard(task)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.warning(
                "TaskRegistry task %r failed: %s",
                task.get_name(),
                exc,
                exc_info=exc,
            )


# Module-level singleton used throughout the application.
task_registry = TaskRegistry()
