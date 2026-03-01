
from backend.app.domain.models import AgentEvent
from backend.app.graph.state import AgentState
from backend.app.core.config import get_settings

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

def profiler_node(state : AgentState):
    """
    Receives original code.
    Detects language, framework and version.
    Updates: metadata, status, events
    """
    running_event = create_event(
        agent_name="profiler",
        status="running",
        message="Analyzing code to detect language, framework and version"
        )
    
    metadata = {
        "language" : ,
        "framework" : ,
        "version" : 
    }

    completed_event = create_event(
        agent_name="profiler",
        status="completed",
        message="Language detected successfully",
        data=metadata
    )

    return {
        "metadata" : metadata,
        "status" : "profiling_complete",
        "events" : [running_event, completed_event]
    }



def anchor_node(state : AgentState):
    """
    Receives original code along with metada
    Genrates unit tests.
    Updates : unit_tests, status, events
    """

    running_event = create_event(
        agent_name="logic_anchor",
        status="running",
        message="Generating Unit tests to ensure the Original behaviour Locks in"
        )
    
    unit_tests = ""

    completed_event = create_event(
        agent_name="logic_anchor",
        status="complete",
        message="Unit Tests generated successfully"
        )
    
    return {
        "unit_tests" : unit_tests,
        "status" : "anchoring_complete",
        "events" : [running_event,completed_event]
    }

    


def architect_node(state : AgentState):
    """
    Receives the original code and metadata,
    Queries the ChromaDB fro relevant migration docs,
    Produces a step by step Transformation Plan,
    Updates : transformation_plan, status and events
    """

    running_event = create_event(
        agent_name="architect",
        status="running",
        message="Querying knowledge base and building transformation plan..."
        )
    transformation_plan = {
        'steps' : [],
        "documentation_snippets" : []
    }

    completed_event = create_event(
        agent_name="architect",
        status="complete",
        message="Transformation Plan created successfully",
        data = transformation_plan
        )
    
    return {
        "transformation_plan" : transformation_plan,
        "status" : "planning_complete",
        "events" : [running_event, completed_event]    
    }





def engineer_node(state : AgentState):
    """
    Receives original code and transformation plan.
    Produces modernized code that preserves all original behavior.
    Updates: modern_code, status, events
    """

    running_event = create_event(
        agent_name="engineer",
        status="running",
        message="Refactoring code using transformation plan..."
    )

    # --- Real agent logic will replace this in Step 4 ---
    modern_code = "# Modernized code placeholder"
    # ----------------------------------------------------

    completed_event = create_event(
        agent_name="engineer",
        status="completed",
        message="Code refactored successfully"
    )

    return {
        "modern_code": modern_code,
        "status": "engineering_complete",
        "events": [running_event, completed_event]
    }




def tester_node(state : AgentState):
    """
    Receives modern code and unit tests.
    Builds a Docker container, runs tests, captures logs.
    Updates: validation_logs, status, events
    """

    running_event = create_event(
        agent_name="validator",
        status="running",
        message="Running tests in Docker sandbox..."
    )

    # --- Real agent logic will replace this in Step 4 ---
    validation_logs = "All tests passed"
    validation_status = "validation_passed"
    # ----------------------------------------------------

    completed_event = create_event(
        agent_name="validator",
        status="completed",
        message="Validation complete",
        data={"validation_status": validation_status}
    )

    return {
        "validation_logs": validation_logs,
        "status": validation_status,
        "events": [running_event, completed_event]
    }




def fixer_node(state : AgentState):
    """
    Receives modern code and validation error logs.
    Fixes SYNTAX ONLY — no logic modification allowed.
    Updates: modern_code, retry_count, status, events
    """

    current_retry = state.get("retry_count", 0)

    running_event = create_event(
        agent_name="fixer",
        status="running",
        message=f"Attempting syntax fix — retry {current_retry + 1}...",
        data={"retry_count": current_retry + 1}
    )

    # --- Real agent logic will replace this in Step 4 ---
    fixed_code = state.get("modern_code", "")
    # ----------------------------------------------------

    completed_event = create_event(
        agent_name="fixer",
        status="completed",
        message=f"Syntax fix attempt {current_retry + 1} complete"
    )

    return {
        "modern_code": fixed_code,
        "retry_count": current_retry + 1,
        "status": "fixing_complete",
        "events": [running_event, completed_event]
    }
