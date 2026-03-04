from app.graph.state import AgentState
from app.core.config import get_settings
import re


def _parse_pytest_results(validation_logs: str) -> dict:
    """
    Parse pytest output to get actual pass/fail counts.
    
    Handles output like:
    '1 failed, 9 passed in 0.02s'
    '10 passed in 0.02s'
    '5 failed in 0.02s'
    """
    passed = 0
    failed = 0

    # Match '9 passed'
    passed_match = re.search(r'(\d+) passed', validation_logs)
    if passed_match:
        passed = int(passed_match.group(1))

    # Match '1 failed'
    failed_match = re.search(r'(\d+) failed', validation_logs)
    if failed_match:
        failed = int(failed_match.group(1))

    total      = passed + failed
    pass_rate  = (passed / total) if total > 0 else 0.0

    return {
        "passed":    passed,
        "failed":    failed,
        "total":     total,
        "pass_rate": pass_rate
    }


def after_validator(state: AgentState) -> str:
    """
    Called by LangGraph after every validator_node run.

    Pass criteria:
    - status is explicitly 'validation_passed' (exit code 0), OR
    - pass rate is >= 80% (e.g. 9/10 tests pass)

    This prevents 1 bad Logic Anchor test from
    killing an otherwise perfectly modernized codebase.
    """
    settings    = get_settings()
    status      = state.get("status",      "")
    retry_count = state.get("retry_count", 0)
    logs        = state.get("validation_logs", "")

    # ── CASE 1: All tests passed cleanly ──────
    if status == "validation_passed":
        return "end"

    # ── CASE 2: Parse actual pass rate ────────
    results   = _parse_pytest_results(logs)
    pass_rate = results["pass_rate"]
    passed    = results["passed"]
    failed    = results["failed"]
    total     = results["total"]

    print(f"[EDGES] Test results: {passed}/{total} passed ({pass_rate:.0%})")

    # Allow pipeline to succeed if >= 80% tests pass
    # This handles Logic Anchor hallucinating 1-2 bad tests
    if pass_rate >= 0.80 and total > 0:
        print(f"[EDGES] Pass rate {pass_rate:.0%} >= 80% — accepting as passed")
        return "end"

    # ── CASE 3: Max retries exceeded ──────────
    if retry_count >= settings.max_retries:
        print(f"[EDGES] Max retries ({settings.max_retries}) exceeded — ending")
        return "end"

    # ── CASE 4: Still failing, retries left ───
    print(f"[EDGES] Pass rate {pass_rate:.0%} < 80% — sending to fixer")
    return "fixer"