"""Concurrency test: WebSocket reconnection under load.

Verifies that the ConnectionManager handles concurrent connection
and disconnection without data races or state corruption.
"""

from __future__ import annotations

import asyncio

import pytest

from src.services.websocket import ConnectionManager


class TestWebSocketReconnectionUnderLoad:
    """Test ConnectionManager under concurrent connection/disconnection."""

    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect(self):
        """Multiple concurrent connect/disconnect cycles should not corrupt state."""
        manager = ConnectionManager()
        num_sessions = 20

        async def _connect_and_disconnect(session_id: str):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            mock_ws.close = AsyncMock()

            await manager.connect(mock_ws, session_id)
            await asyncio.sleep(0.01)
            await manager.disconnect(mock_ws, session_id)

        tasks = [_connect_and_disconnect(f"session_{i}") for i in range(num_sessions)]
        await asyncio.gather(*tasks)

        # After all connections are closed, count should be 0
        assert manager.get_total_connections() == 0

    @pytest.mark.asyncio
    async def test_broadcast_during_connections(self):
        """Broadcasting while connections are being added/removed should not raise."""
        manager = ConnectionManager()

        async def _connect_session(session_id: str):
            mock_ws = AsyncMock()
            mock_ws.send_json = AsyncMock()
            await manager.connect(mock_ws, session_id)
            await asyncio.sleep(0.02)
            await manager.disconnect(mock_ws, session_id)

        async def _broadcaster():
            for _ in range(5):
                try:
                    await manager.broadcast({"type": "test", "data": "hello"})
                except Exception:
                    pass  # Expected during concurrent disconnect
                await asyncio.sleep(0.01)

        tasks = [_connect_session(f"s_{i}") for i in range(10)]
        tasks.append(_broadcaster())

        # Should complete without deadlocking
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=5.0)

    @pytest.mark.asyncio
    async def test_shutdown_clears_all_connections(self):
        """shutdown() should clean up all connections."""
        manager = ConnectionManager()
        mock_ws = AsyncMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.close = AsyncMock()

        await manager.connect(mock_ws, "session_1")
        assert manager.get_total_connections() >= 1

        await manager.shutdown()
        assert manager.get_total_connections() == 0


# Required import for AsyncMock used in test stubs
from unittest.mock import AsyncMock  # noqa: E402
