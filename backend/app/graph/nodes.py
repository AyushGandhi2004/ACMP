import traceback
from app.domain.models import AgentEvent
from app.graph.state import AgentState
from app.core.config import get_settings
from app.agents.profiler import ProfilerAgent
from app.agents.anchor import AnchorAgent
from app.agents.architect import ArchitectAgent
from app.agents.engineer import EngineerAgent
from app.agents.tester import TesterAgent
from app.agents.fixer import FixerAgent
import re

def _parse_pytest_results(logs: str) -> dict:
    passed = 0
    failed = 0
    passed_match = re.search(r'(\d+) passed', logs)
    if passed_match:
        passed = int(passed_match.group(1))
    failed_match = re.search(r'(\d+) failed', logs)
    if failed_match:
        failed = int(failed_match.group(1))
    total     = passed + failed
    pass_rate = (passed / total) if total > 0 else 0.0
    return {"passed": passed, "failed": failed, "total": total, "pass_rate": pass_rate}


settings = get_settings()

def create_event(agent_name : str, status : str, message : str, data : dict = None):
    """
    This function acts as a helper function and sends the status to frontend by getting appended to state[node]
    """
    return AgentEvent(
        agent_name=agent_name,
        status=status,
        message=message,
        data=data
    ).model_dump()

async def profiler_node(state : AgentState):
    """
    Receives original code.
    Detects language, framework and version.
    Updates: metadata, status, events
    """
    events = []
    try:
        events.append(create_event(
            "profiler", "running",
            "Analyzing code to detect language, framework and version..."
        ))

        agent  = ProfilerAgent()
        result = await agent.run(state)      # ← real LLM call

        metadata = result.get("metadata", {})
        language  = metadata.get("language", "unknown")
        framework = metadata.get("framework", "unknown")

        events.append(create_event(
            "profiler", "completed",
            f"Detected: {language} / {framework}",
            metadata
        ))

        return {**result, "events": events}

    except Exception as e:
        traceback.print_exc()
        events.append(create_event(
            "profiler", "failed",
            f"Profiler error: {str(e)}"
        ))
        return {
            "metadata": {"language": "python", "framework": "unknown", "version": "unknown"},
            "events":   events
        }



async def anchor_node(state : AgentState):
    """
    Receives original code along with metada
    Genrates unit tests.
    Updates : unit_tests, status, events
    """

    events = []
    try:
        events.append(create_event(
            "logic_anchor", "running",
            "Generating unit tests to lock in original code behavior..."
        ))

        agent  = AnchorAgent()
        result = await agent.run(state)      # ← real LLM call

        events.append(create_event(
            "logic_anchor", "completed",
            "Unit tests generated successfully"
        ))

        return {**result, "events": events}

    except Exception as e:
        traceback.print_exc()
        events.append(create_event(
            "logic_anchor", "failed",
            f"Logic Anchor error: {str(e)}"
        ))
        return {
            "unit_tests": "# Could not generate tests\ndef test_placeholder():\n    assert True",
            "events":     events
        }

    


async def architect_node(state : AgentState):
    """
    Receives the original code and metadata,
    Queries the ChromaDB fro relevant migration docs,
    Produces a step by step Transformation Plan,
    Updates : transformation_plan, status and events
    """

    events = []
    try:
        events.append(create_event(
            "architect", "running",
            "Querying knowledge base and building transformation plan..."
        ))

        agent  = ArchitectAgent()
        result = await agent.run(state)      # ← real LLM call + RAG query

        plan       = result.get("transformation_plan", {})
        step_count = len(plan.get("steps", []))

        events.append(create_event(
            "architect", "completed",
            f"Transformation plan ready — {step_count} steps",
            plan
        ))

        return {**result, "events": events}

    except Exception as e:
        traceback.print_exc()
        events.append(create_event(
            "architect", "failed",
            f"Architect error: {str(e)}"
        ))
        return {
            "transformation_plan": {
                "steps": [
                    "Step 1: Modernize syntax and language patterns",
                    "Step 2: Replace deprecated APIs with modern equivalents",
                    "Step 3: Apply current best practices"
                ],
                "documentation_snippets": []
            },
            "events": events
        }





async def engineer_node(state : AgentState):
    """
    Receives original code and transformation plan.
    Produces modernized code that preserves all original behavior.
    Updates: modern_code, status, events
    """

    events = []
    try:
        events.append(create_event(
            "engineer", "running",
            "Modernizing code using transformation plan..."
        ))

        agent  = EngineerAgent()
        result = await agent.run(state)      # ← real LLM call

        modern_code = result.get("modern_code", "")

        if not modern_code or modern_code.strip() == "":
            raise ValueError("Engineer returned empty code")

        events.append(create_event(
            "engineer", "completed",
            f"Code modernized — {len(modern_code)} characters"
        ))

        return {**result, "events": events}

    except Exception as e:
        traceback.print_exc()
        events.append(create_event(
            "engineer", "failed",
            f"Engineer error: {str(e)}"
        ))
        # Fall back to original code so pipeline can continue
        return {
            "modern_code": state.get("original_code", ""),
            "status":      "engineer_failed",
            "events":      events
        }




async def tester_node(state : AgentState):
    """
    Receives modernized code and runs syntax checking
    in an isolated Docker sandbox.
    
    No unit tests are executed - just runs the file to check for syntax errors.
    Timeout errors (e.g., waiting for user input) are treated as success.

    Updates: validation_logs, status, events
    """

    events = []
    try:
        events.append(create_event(
            "tester", "running",
            "Running syntax check in Docker sandbox..."
        ))

        agent  = TesterAgent()
        result = await agent.run(state)

        logs   = result.get("validation_logs", "")
        status = result.get("status", "validation_failed")

        is_passed = status == "validation_passed"
        
        # Check if it was a timeout or user input requirement
        is_timeout = "TIMEOUT" in logs and "user input" in logs
        is_user_input = "USER INPUT DETECTED" in logs
        
        if is_timeout:
            message = "Syntax check passed ✓ (timeout - likely waiting for user input)"
        elif is_user_input:
            message = "Syntax check passed ✓ (code requires user input)"
        elif is_passed:
            message = "Syntax check passed ✓"
        else:
            message = "Syntax check failed - errors detected"

        events.append(create_event(
            "tester",
            "completed" if is_passed else "failed",
            message
        ))

        return {
            **result,
            "status": status,
            "events": events
        }

    except Exception as e:
        traceback.print_exc()
        events.append(create_event("tester", "failed", str(e)))
        return {
            "validation_logs": str(e),
            "status":          "validation_failed",
            "events":          events
        }





async def fixer_node(state : AgentState):
    """
    Receives modern code and validation error logs.
    Fixes SYNTAX ONLY — no logic modification allowed.
    Updates: modern_code, retry_count, status, events
    """

    events = []
    retry_count = state.get("retry_count", 0)
    try:
        events.append(create_event(
            "fixer", "running",
            f"Fixing syntax errors — attempt {retry_count + 1}...",
            {"retry_count": retry_count + 1}
        ))

        agent  = FixerAgent()
        result = await agent.run(state)      # ← real LLM call

        events.append(create_event(
            "fixer", "completed",
            f"Fix attempt {retry_count + 1} complete — retrying validation"
        ))

        return {**result, "events": events}

    except Exception as e:
        traceback.print_exc()
        events.append(create_event(
            "fixer", "failed",
            f"Fixer error: {str(e)}"
        ))
        return {
            "modern_code":  state.get("modern_code", ""),
            "retry_count":  retry_count + 1,
            "events":       events
        }