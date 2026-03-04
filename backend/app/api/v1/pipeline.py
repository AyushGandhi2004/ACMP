import asyncio
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.events import manager
from app.domain.models import PipelineRequest, PipelineResponse, ModernizationResult
from app.graph.pipeline import graph
from app.graph.state import AgentState


router = APIRouter()


# ─────────────────────────────────────────
# IN MEMORY RESULT STORE
# ─────────────────────────────────────────

pipeline_results: dict[str, dict] = {}


# ─────────────────────────────────────────
# BACKGROUND TASK
# Runs the full LangGraph pipeline ONCE
# Captures final state from last snapshot
# Streams events to WebSocket as it runs
# ─────────────────────────────────────────

async def execute_pipeline(
    session_id: str,
    initial_state: AgentState
) -> None:
    """
    Runs the ACMP pipeline exactly ONCE using astream.

    astream yields a snapshot after each node completes.
    Each snapshot is a dict: { "node_name": {fields node updated} }

    LangGraph merges state across nodes internally.
    We track the last snapshot to get the final merged state.

    Flow:
        astream yields node snapshots
            → we broadcast new events after each node
            → we track the last snapshot
        After stream ends → last snapshot has final state
            → build result → store → send completion event
    """

    try:
        last_sent_index = 0
        final_state = None

        # ── stream_mode="values" gives complete ──
        # accumulated state after each node
        # instead of just the node's output delta
        async for current_state in graph.astream(
            initial_state,
            config={"recursion_limit": 50},
            stream_mode="values"    # ← KEY CHANGE
        ):
            # current_state is now the FULL merged state
            # not just what the last node updated
            # print("\n\n\nCurrent State Snapshot:\n", current_state)
            final_state = current_state

            # Events list is fully accumulated
            # so last_sent_index tracking works correctly
            all_events = current_state.get("events", [])
            new_events  = all_events[last_sent_index:]

            if new_events:
                await manager.broadcast_pipeline_events(
                    session_id,
                    new_events
                )
                last_sent_index = len(all_events)

        # ── Pipeline complete ─────────────────────
        if not final_state:
            raise ValueError("Pipeline produced no output")

        result = ModernizationResult(
            session_id=session_id,
            original_code=final_state.get("original_code", ""),
            modern_code=final_state.get("modern_code", ""),
            language=final_state.get("metadata", {}).get("language", "unknown"),
            framework=final_state.get("metadata", {}).get("framework", "unknown"),
            transformation_plan=final_state.get("transformation_plan", {}),
            error_logs=final_state.get("error_logs", ""),
            status=final_state.get("status", "unknown")
        )

        pipeline_results[session_id] = result.model_dump()

        await manager.send_event(session_id, {
            "type":   "pipeline_complete",
            "status": final_state.get("status", "unknown"),
            "result": result.model_dump()
        })

    except Exception as e:
        error_result = {
            "session_id": session_id,
            "status":     "failed",
            "error":      str(e)
        }
        pipeline_results[session_id] = error_result

        await manager.send_event(session_id, {
            "type":    "pipeline_error",
            "status":  "failed",
            "message": f"Pipeline failed: {str(e)}"
        })

# ─────────────────────────────────────────
# POST /run
# ─────────────────────────────────────────

@router.post("/run", response_model=PipelineResponse, status_code=201)
async def run_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Accepts code from frontend.
    Builds initial state.
    Kicks off pipeline as background task.
    Returns session_id immediately.
    Frontend opens WebSocket using session_id
    to receive live events.
    """
    session_id = str(uuid4())

    initial_state: AgentState = {
        "session_id":          session_id,
        "original_code":       request.code,
        "metadata":            {
            "language": request.language.value
            if request.language else "unknown"
        },
        "unit_tests":          "",
        "transformation_plan": {},
        "modern_code":         "",
        "error_logs":     "",
        "status":              "started",
        "retry_count":         0,
        "events":              []
    }

    # ── This is where the graph gets invoked ──
    # BackgroundTasks runs execute_pipeline
    # AFTER the response is sent to frontend
    # Frontend immediately opens WebSocket
    # Pipeline streams events through manager
    background_tasks.add_task(
        execute_pipeline,
        session_id,
        initial_state
    )

    return PipelineResponse(
        session_id=session_id,
        status="started",
        message="Pipeline started. Connect to WebSocket for live updates."
    )


# ─────────────────────────────────────────
# GET /result/{session_id}
# Retrieve final result of a completed run
# Useful if WebSocket disconnected early
# ─────────────────────────────────────────

@router.get(
    "/result/{session_id}",
    status_code=200
)
async def get_pipeline_result(session_id: str) -> dict:
    """
    Retrieve the final result of a completed pipeline run.
    Useful when WebSocket disconnects before completion
    or when polling is preferred over WebSocket.

    Args:
        session_id: Unique pipeline run identifier

    Returns:
        ModernizationResult dict if found

    Raises:
        HTTPException 404 if session not found or still running
    """
    result = pipeline_results.get(session_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No result found for session {session_id}. "
                   f"Pipeline may still be running."
        )

    return result