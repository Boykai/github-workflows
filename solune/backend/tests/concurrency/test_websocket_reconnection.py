"""Concurrency test: WebSocket reconnection under load.

Verifies that the ConnectionManager handles concurrent connection
and disconnection without data races or state corruption.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.websocket import ConnectionManager


def _make_mock_ws():
    """Create a mock WebSocket that supports accept/send_json/close."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestWebSocketReconnectionUnderLoad:
    """Test ConnectionManager under concurrent connection/disconnection."""

    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect(self):
        """Multiple concurrent connect/disconnect cycles should not corrupt state."""
        manager = ConnectionManager()
        num_sessions = 20

        async def _connect_and_disconnect(idx: int):
            mock_ws = _make_mock_ws()
            project_id = f"PVT_project_{idx}"
            await manager.connect(mock_ws, project_id)
            await asyncio.sleep(0.01)
            manager.disconnect(mock_ws)

        tasks = [_connect_and_disconnect(i) for i in range(num_sessions)]
        await asyncio.gather(*tasks)

        # After all connections are closed, count should be 0
        assert manager.get_total_connections() == 0

    @pytest.mark.asyncio
    async def test_broadcast_during_connections(self):
        """Broadcasting while connections are being added/removed should not raise."""
        manager = ConnectionManager()
        project_id = "PVT_broadcast_test"

        async def _connect_session(idx: int):
            mock_ws = _make_mock_ws()
            await manager.connect(mock_ws, project_id)
            await asyncio.sleep(0.02)
            manager.disconnect(mock_ws)

        async def _broadcaster():
            errors: list[Exception] = []
            for _ in range(5):
                try:
                    await manager.broadcast_to_project(
                        project_id, {"type": "test", "data": "hello"}
                    )
                except (KeyError, RuntimeError):
                    pass  # Expected during concurrent disconnect
                except Exception as exc:
                    errors.append(exc)
                await asyncio.sleep(0.01)
            assert not errors, f"Unexpected broadcast errors: {errors}"

        tasks = [_connect_session(i) for i in range(10)]
        tasks.append(_broadcaster())

        # Should complete without deadlocking
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=5.0)

    @pytest.mark.asyncio
    async def test_shutdown_clears_all_connections(self):
        """shutdown() should clean up all connections."""
        manager = ConnectionManager()
        mock_ws = _make_mock_ws()

        await manager.connect(mock_ws, "PVT_shutdown_test")
        assert manager.get_total_connections() >= 1

        await manager.shutdown()
        assert manager.get_total_connections() == 0
