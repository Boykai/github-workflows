from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src import main


@pytest.mark.asyncio
async def test_polling_watchdog_attempts_restart_after_detecting_stopped_loop(monkeypatch) -> None:
    sleep_calls: list[float] = []
    restart = AsyncMock(return_value=True)

    async def fake_sleep(delay: float) -> None:
        sleep_calls.append(delay)
        if len(sleep_calls) > 1:
            raise asyncio.CancelledError()

    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(main, "_auto_start_copilot_polling", restart)
    monkeypatch.setattr(
        "src.services.copilot_polling.get_polling_status",
        lambda: {"is_running": False, "errors_count": 1, "last_error": "boom"},
    )

    await main._polling_watchdog_loop()

    assert sleep_calls[0] == 30
    restart.assert_awaited_once()


@pytest.mark.asyncio
async def test_session_cleanup_loop_uses_exponential_backoff_after_failures(monkeypatch) -> None:
    sleep_calls: list[int] = []
    purge = AsyncMock(side_effect=[RuntimeError("db down"), 0])

    async def fake_sleep(delay: int) -> None:
        sleep_calls.append(delay)
        if len(sleep_calls) > 2:
            raise asyncio.CancelledError()

    monkeypatch.setattr(main.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(main, "get_settings", lambda: SimpleNamespace(session_cleanup_interval=5))
    monkeypatch.setattr("src.services.database.get_db", lambda: object())
    monkeypatch.setattr("src.services.session_store.purge_expired_sessions", purge)

    await main._session_cleanup_loop()

    assert sleep_calls[:2] == [5, 10]
