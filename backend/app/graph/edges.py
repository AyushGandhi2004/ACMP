from app.graph.state import AgentState
from app.core.config import get_settings




def after_validator(state: AgentState) -> str:
    """
    Called by LangGraph after every validator_node run.
    Reads the current state and decides what happens next.

    Returns:
        "end"   → pipeline finishes (success or max retries exceeded)
        "fixer" → send to fixer agent for syntax correction

    Decision Logic:
        1. Did validation pass?     → end (success)
        2. Exceeded max retries?    → end (failed)
        3. Otherwise               → fixer (try again)
    """

    settings = get_settings()
    status = state.get("status", "")
    retry_count = state.get("retry_count", 0)

    # ─────────────────────────────────────────
    # CASE 1 — Validation Passed
    # Tests ran successfully in Docker sandbox
    # Pipeline is complete — go to END
    # ─────────────────────────────────────────
    if status == "validation_passed":
        return "end"

    # ─────────────────────────────────────────
    # CASE 2 — Max Retries Exceeded
    # Fixer has tried too many times
    # Stop the loop — go to END as failed
    # ─────────────────────────────────────────
    if retry_count >= settings.max_retries:
        return "end"

    # ─────────────────────────────────────────
    # CASE 3 — Validation Failed, Retries Left
    # Send to Fixer for syntax correction
    # Fixer will loop back to Validator
    # ─────────────────────────────────────────
    return "fixer"
