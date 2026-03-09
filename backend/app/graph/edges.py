from app.graph.state import AgentState
from app.core.config import get_settings


def after_validator(state: AgentState) -> str:
    """
    Called by LangGraph after every validator_node run.

    Pass criteria:
    - status is explicitly 'validation_passed'

    If failed and retries remain, route to fixer.
    Otherwise end the pipeline.
    """
    settings    = get_settings()
    status      = state.get("status",      "")
    retry_count = state.get("retry_count", 0)

    # ── CASE 1: Syntax check passed ──────
    if status == "validation_passed":
        print(f"[EDGES] Syntax check passed — ending pipeline")
        return "end"

    # ── CASE 2: Max retries exceeded ──────────
    if retry_count >= settings.max_retries:
        print(f"[EDGES] Max retries ({settings.max_retries}) exceeded — ending")
        return "end"

    # ── CASE 3: Still failing, retries left ───
    print(f"[EDGES] Syntax check failed — sending to fixer (retry {retry_count + 1}/{settings.max_retries})")
    return "fixer"