import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import manager


# ─────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────

router = APIRouter()


# ─────────────────────────────────────────
# WEBSOCKET ENDPOINT
# Streams live agent updates to frontend
# One connection per pipeline run
# Identified by session_id
# ─────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
) -> None:
    """
    WebSocket endpoint for live pipeline updates.

    Frontend connects here immediately after receiving
    session_id from POST /api/v1/pipeline/run.

    Lifecycle:
        1. Frontend opens connection with session_id
        2. Manager registers the connection
        3. Keep-alive loop holds connection open
        4. Pipeline background task sends events through manager
        5. Frontend receives and renders each AgentEvent
        6. Connection closes when frontend disconnects
           or pipeline sends completion event

    URL Pattern:
        ws://localhost:8000/api/v1/ws/{session_id}

    Args:
        websocket:  FastAPI WebSocket object
        session_id: Unique pipeline run identifier
    """

    # ── Step 1: Register connection with manager ──
    await manager.connect(session_id, websocket)

    try:
        # ── Step 2: Keep connection alive ─────────
        # The pipeline background task sends events
        # through the manager to this connection.
        # We just need to keep it open and handle
        # any incoming messages from frontend.
        while True:
            try:
                # Listen for any messages from frontend
                # Frontend may send "ping" to keep alive
                # or "cancel" to stop the pipeline
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=1.0     # check every second
                )

                # Handle frontend messages
                if data == "ping":
                    await websocket.send_json({
                        "type":    "pong",
                        "message": "Connection alive"
                    })

                elif data == "cancel":
                    await websocket.send_json({
                        "type":    "cancelled",
                        "message": "Pipeline cancellation requested"
                    })
                    break

            except asyncio.TimeoutError:
                # No message from frontend — that is normal
                # Just continue the loop to keep connection open
                continue

    except WebSocketDisconnect:
        # ── Frontend disconnected ─────────────────
        # This is normal — happens when:
        # - User closes the browser tab
        # - User navigates away
        # - Network interruption
        # Pipeline continues running in background
        # Result stored in pipeline_results dict
        manager.disconnect(session_id)

    except Exception:
        # ── Unexpected error ──────────────────────
        # Always clean up connection on any error
        manager.disconnect(session_id)

    finally:
        # ── Always clean up ───────────────────────
        # Ensure connection is removed from manager
        # even if disconnect was already called above
        manager.disconnect(session_id)