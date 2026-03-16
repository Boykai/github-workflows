"""WebSocket connection manager for real-time updates."""

import asyncio

from fastapi import WebSocket

from src.logging_utils import get_logger

logger = get_logger(__name__)

# Module-level lock for connection mutations
_ws_lock: asyncio.Lock | None = None


def _get_ws_lock() -> asyncio.Lock:
    """Create the shared websocket lock lazily inside the active event loop."""
    global _ws_lock
    if _ws_lock is None:
        _ws_lock = asyncio.Lock()
    return _ws_lock


class ConnectionManager:
    """Manages WebSocket connections for real-time project updates."""

    def __init__(self):
        # Map project_id -> set of connected websockets
        self._connections: dict[str, set[WebSocket]] = {}
        # Map websocket -> project_id for cleanup
        self._socket_projects: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        """
        Accept a new WebSocket connection for a project.

        Args:
            websocket: The WebSocket connection
            project_id: GitHub Project ID to subscribe to
        """
        await websocket.accept()

        async with _get_ws_lock():
            if project_id not in self._connections:
                self._connections[project_id] = set()

            self._connections[project_id].add(websocket)
            self._socket_projects[websocket] = project_id

        logger.info(
            "WebSocket connected for project %s (total: %d)",
            project_id,
            len(self._connections.get(project_id, set())),
        )

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        project_id = self._socket_projects.pop(websocket, None)
        if project_id and project_id in self._connections:
            self._connections[project_id].discard(websocket)
            if not self._connections[project_id]:
                del self._connections[project_id]

            logger.info("WebSocket disconnected from project %s", project_id)

    async def broadcast_to_project(self, project_id: str, message: dict) -> None:
        """
        Broadcast a message to all connections for a project.

        Args:
            project_id: GitHub Project ID
            message: Message to broadcast (will be JSON encoded)
        """
        connections = self._connections.get(project_id, set())
        if not connections:
            logger.debug("No connections to broadcast to for project %s", project_id)
            return

        logger.info(
            "Broadcasting %s to project %s (%d connections)",
            message.get("type", "unknown"),
            project_id,
            len(connections),
        )

        disconnected = []
        # Snapshot the set to avoid RuntimeError if it is mutated during iteration
        for websocket in list(connections):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning("Failed to send to WebSocket: %s", e)
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for ws in disconnected:
            self.disconnect(ws)

        logger.debug(
            "Broadcast complete to project %s: %d/%d successful",
            project_id,
            len(connections) - len(disconnected),
            len(connections),
        )

    def get_connection_count(self, project_id: str) -> int:
        """Get number of active connections for a project."""
        return len(self._connections.get(project_id, set()))

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self._connections.values())

    async def shutdown(self) -> None:
        """Close and forget all tracked WebSocket connections."""
        sockets = list(self._socket_projects)
        self._connections.clear()
        self._socket_projects.clear()

        for websocket in sockets:
            try:
                await websocket.close()
            except Exception:
                logger.debug("Failed to close WebSocket during shutdown", exc_info=True)


# Global connection manager instance
connection_manager = ConnectionManager()
