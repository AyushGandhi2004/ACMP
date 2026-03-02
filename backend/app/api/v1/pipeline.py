import asyncio
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.events import manager
from app.domain.models import PipelineRequest, PipelineResponse, ModernizationResult
from app.graph.pipeline import graph
from app.graph.state import AgentState


# ─────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────

router = APIRouter()


# ─────────────────────────────────────────
# IN MEMORY RESULT STORE
# Stores final pipeline results keyed by session_id
# Allows GET /result/{session_id} to retrieve them
# Can be swapped to Redis in production
# ─────────────────────────────────────────

pipeline_results: dict[str, dict] = {}


# ─────────────────────────────────────────
# BACKGROUND TASK
# Runs the full LangGraph pipeline
# Streams events to frontend via WebSocket
# ─────────────────────────────────────────

async def execute_pipeline(
    session_id: str,
    initial_state: AgentState
) -> None:
    """
    Background task that runs the full ACMP pipeline.
    Invoked by the /run endpoint via BackgroundTasks.

    Flow:
        1. Run LangGraph pipeline with initial state
        2. After each node — broadcast new events via WebSocket
        3. On completion — store result + send final event
        4. On failure — send error event + store failed result

    Args:
        session_id:    Unique identifier for this run
        initial_state: Initial AgentState with code and session_id
    """
    try:
        # ── Track which events have been sent ────────
        # LangGraph returns ALL events in state after each node
        # We track the last sent index to send only NEW events
        last_sent_index = 0

        # ── Stream pipeline execution ─────────────────
        # astream returns state snapshots after each node
        async for state_snapshot in graph.astream(
            initial_state,
            config={"recursion_limit": 50}
        ):
            # Each snapshot is a dict:
            # {"node_name": updated_state_fields}
            # We need to get the actual state values
            for node_name, node_output in state_snapshot.items():

                # Get all events accumulated so far
                all_events = node_output.get("events", [])

                # Send only new events since last broadcast
                new_events = all_events[last_sent_index:]
                if new_events:
                    await manager.broadcast_pipeline_events(
                        session_id,
                        new_events
                    )
                    last_sent_index = len(all_events)

        # ── Pipeline complete ─────────────────────────
        # Get the final state by invoking once more
        # to get the complete merged state
        final_state = await graph.ainvoke(
            initial_state,
            config={"recursion_limit": 50}
        )

        # ── Build result object ───────────────────────
        result = ModernizationResult(
            session_id=session_id,
            original_code=final_state.get("original_code", ""),
            modern_code=final_state.get("modern_code", ""),
            language=final_state.get("metadata", {}).get(
                "language", "unknown"
            ),
            framework=final_state.get("metadata", {}).get(
                "framework", "unknown"
            ),
            transformation_plan=final_state.get(
                "transformation_plan", {}
            ),
            error_logs=final_state.get("error_logs", ""),
            status=final_state.get("status", "unknown")
        )

        # ── Store result for GET /result/{session_id} ─
        pipeline_results[session_id] = result.model_dump()

        # ── Send completion event via WebSocket ───────
        await manager.send_event(session_id, {
            "type":   "pipeline_complete",
            "status": final_state.get("status", "unknown"),
            "result": result.model_dump()
        })

    except Exception as e:
        # ── Handle pipeline failure ───────────────────
        error_result = {
            "session_id": session_id,
            "status":     "failed",
            "error":      str(e)
        }

        # Store failed result
        pipeline_results[session_id] = error_result

        # Notify frontend of failure
        await manager.send_event(session_id, {
            "type":    "pipeline_error",
            "status":  "failed",
            "message": f"Pipeline failed: {str(e)}"
        })


# ─────────────────────────────────────────
# POST /run
# Triggers a new pipeline run
# Returns session_id immediately
# Pipeline runs in background
# ─────────────────────────────────────────

@router.post(
    "/run",
    response_model=PipelineResponse,
    status_code=201
)
async def run_pipeline(
    request: PipelineRequest,
    background_tasks: BackgroundTasks
) -> PipelineResponse:
    """
    Start a new code modernization pipeline run.

    Immediately returns a session_id.
    Frontend uses session_id to open WebSocket
    and receive live agent updates.

    Args:
        request:          PipelineRequest with code + optional language
        background_tasks: FastAPI BackgroundTasks for async execution

    Returns:
        PipelineResponse with session_id, status, message
    """

    # Generate unique session ID for this run
    session_id = str(uuid4())

    # Build initial pipeline state
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

    # Add pipeline execution as background task
    # Route returns immediately — pipeline runs async
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