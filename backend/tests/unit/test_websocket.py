"""Unit tests for WebSocket connection manager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.websocket import ConnectionManager, connection_manager


class TestConnectionManager:
    """Tests for the ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        """Create a fresh ConnectionManager instance."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.fixture
    def mock_websocket2(self):
        """Create a second mock WebSocket."""
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager, mock_websocket):
        """Should accept the WebSocket connection."""
        await manager.connect(mock_websocket, "PVT_123")

        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_adds_to_connections(self, manager, mock_websocket):
        """Should track the connection for the project."""
        await manager.connect(mock_websocket, "PVT_123")

        assert manager.get_connection_count("PVT_123") == 1

    @pytest.mark.asyncio
    async def test_connect_multiple_to_same_project(self, manager, mock_websocket, mock_websocket2):
        """Should track multiple connections to the same project."""
        await manager.connect(mock_websocket, "PVT_123")
        await manager.connect(mock_websocket2, "PVT_123")

        assert manager.get_connection_count("PVT_123") == 2

    @pytest.mark.asyncio
    async def test_connect_to_different_projects(self, manager, mock_websocket, mock_websocket2):
        """Should track connections to different projects separately."""
        await manager.connect(mock_websocket, "PVT_123")
        await manager.connect(mock_websocket2, "PVT_456")

        assert manager.get_connection_count("PVT_123") == 1
        assert manager.get_connection_count("PVT_456") == 1
        assert manager.get_total_connections() == 2

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_websocket):
        """Should remove the WebSocket from tracking."""
        await manager.connect(mock_websocket, "PVT_123")
        assert manager.get_connection_count("PVT_123") == 1

        manager.disconnect(mock_websocket)

        assert manager.get_connection_count("PVT_123") == 0

    @pytest.mark.asyncio
    async def test_disconnect_unknown_websocket(self, manager, mock_websocket):
        """Should handle disconnecting an unknown WebSocket gracefully."""
        # Should not raise
        manager.disconnect(mock_websocket)

        assert manager.get_total_connections() == 0

    @pytest.mark.asyncio
    async def test_disconnect_removes_project_when_empty(self, manager, mock_websocket):
        """Should clean up empty project entries."""
        await manager.connect(mock_websocket, "PVT_123")
        manager.disconnect(mock_websocket)

        # Internal state should be clean
        assert "PVT_123" not in manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_connections(
        self, manager, mock_websocket, mock_websocket2
    ):
        """Should send message to all connections for a project."""
        await manager.connect(mock_websocket, "PVT_123")
        await manager.connect(mock_websocket2, "PVT_123")

        message = {"type": "test", "data": "hello"}
        await manager.broadcast_to_project("PVT_123", message)

        mock_websocket.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_only_to_target_project(self, manager, mock_websocket, mock_websocket2):
        """Should only send to connections for the specified project."""
        await manager.connect(mock_websocket, "PVT_123")
        await manager.connect(mock_websocket2, "PVT_456")

        message = {"type": "test"}
        await manager.broadcast_to_project("PVT_123", message)

        mock_websocket.send_json.assert_called_once_with(message)
        mock_websocket2.send_json.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_to_no_connections(self, manager):
        """Should handle broadcast to project with no connections."""
        # Should not raise
        await manager.broadcast_to_project("PVT_NONE", {"type": "test"})

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_send(self, manager, mock_websocket, mock_websocket2):
        """Should handle and clean up connections that fail to receive."""
        await manager.connect(mock_websocket, "PVT_123")
        await manager.connect(mock_websocket2, "PVT_123")

        # First websocket fails
        mock_websocket.send_json.side_effect = Exception("Connection closed")

        await manager.broadcast_to_project("PVT_123", {"type": "test"})

        # Failed connection should be removed
        assert manager.get_connection_count("PVT_123") == 1
        # Working connection should still be there
        mock_websocket2.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_snapshot_prevents_set_mutation_error(self, manager):
        """Bug fix: broadcast_to_project must snapshot the connections set.

        Previously, broadcast_to_project iterated directly over the mutable
        set reference from self._connections. If a failed send triggered
        disconnect() during iteration, a RuntimeError ('Set changed size
        during iteration') could occur. The fix copies the set to a list
        before iterating.
        """
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock(side_effect=Exception("dead"))

        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        ws3 = MagicMock()
        ws3.accept = AsyncMock()
        ws3.send_json = AsyncMock()

        await manager.connect(ws1, "PVT_SNAP")
        await manager.connect(ws2, "PVT_SNAP")
        await manager.connect(ws3, "PVT_SNAP")

        # Should not raise RuntimeError even though ws1 fails and gets removed
        await manager.broadcast_to_project("PVT_SNAP", {"type": "test"})

        # ws1 should be disconnected, ws2 and ws3 should remain
        assert manager.get_connection_count("PVT_SNAP") == 2
        ws2.send_json.assert_called_once()
        ws3.send_json.assert_called_once()

    def test_get_connection_count_unknown_project(self, manager):
        """Should return 0 for unknown projects."""
        assert manager.get_connection_count("PVT_UNKNOWN") == 0

    @pytest.mark.asyncio
    async def test_get_total_connections(self, manager, mock_websocket, mock_websocket2):
        """Should return total count across all projects."""
        assert manager.get_total_connections() == 0

        await manager.connect(mock_websocket, "PVT_123")
        assert manager.get_total_connections() == 1

        await manager.connect(mock_websocket2, "PVT_456")
        assert manager.get_total_connections() == 2


class TestGlobalConnectionManager:
    """Tests for the global connection_manager instance."""

    def test_global_instance_exists(self):
        """Should have a global ConnectionManager instance."""
        assert connection_manager is not None
        assert isinstance(connection_manager, ConnectionManager)
