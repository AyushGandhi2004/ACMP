import asyncio
from fastapi import WebSocket


# ─────────────────────────────────────────
# CONNECTION MANAGER
# Maintains all active WebSocket connections
# indexed by session_id
# ─────────────────────────────────────────

class ConnectionManager:
    """
    Manages all active WebSocket connections.

    Each pipeline run has a unique session_id.
    Frontend opens a WebSocket using that session_id.
    Pipeline background task sends events through
    this manager to reach the correct frontend client.

    Usage:
        from app.core.events import manager

        # In WebSocket endpoint:
        await manager.connect(session_id, websocket)

        # In pipeline background task:
        await manager.send_event(session_id, event_data)
    """

    def __init__(self):
        # Dict mapping session_id → WebSocket connection
        # {
        #   "abc-123": <WebSocket>,
        #   "def-456": <WebSocket>
        # }
        self.active_connections: dict[str, WebSocket] = {}


    async def connect(
        self,
        session_id: str,
        websocket: WebSocket
    ) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            session_id: Unique pipeline run identifier
            websocket:  FastAPI WebSocket object
        """
        await websocket.accept()
        self.active_connections[session_id] = websocket


    def disconnect(self, session_id: str) -> None:
        """
        Remove a WebSocket connection when client disconnects.
        Safe to call even if session_id doesn't exist.

        Args:
            session_id: Unique pipeline run identifier
        """
        self.active_connections.pop(session_id, None)


    async def send_event(
        self,
        session_id: str,
        event_data: dict
    ) -> None:
        """
        Send a single JSON event to a specific client.
        Silently ignores if session has no active connection.
        This handles the case where frontend disconnected
        before pipeline finished.

        Args:
            session_id: Target client identifier
            event_data: Dict to serialize and send as JSON
        """
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json(event_data)
            except Exception:
                # Client disconnected mid-send
                # Remove stale connection silently
                self.disconnect(session_id)


    async def broadcast_pipeline_events(
        self,
        session_id: str,
        events: list[dict]
    ) -> None:
        """
        Send a list of AgentEvents to a specific client.
        Called after each pipeline node completes
        to stream agent activity to the frontend.

        Args:
            session_id: Target client identifier
            events:     List of AgentEvent dicts from state
        """
        for event in events:
            await self.send_event(session_id, event)
            # Small delay between events so frontend
            # can render each one visually before the next
            await asyncio.sleep(0.1)


    def is_connected(self, session_id: str) -> bool:
        """
        Check if a session has an active WebSocket connection.
        Useful for pipeline to know if anyone is listening.

        Args:
            session_id: Unique pipeline run identifier

        Returns:
            True if connected, False otherwise
        """
        return session_id in self.active_connections


# ─────────────────────────────────────────
# MODULE LEVEL SINGLETON
# Import this instance everywhere
# Never create a new ConnectionManager
# ─────────────────────────────────────────
manager = ConnectionManager()