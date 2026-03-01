from langgraph.graph import StateGraph, END
from backend.app.graph.nodes import profiler_node, anchor_node,architect_node, engineer_node, tester_node, fixer_node
from backend.app.graph.state import AgentState
from backend.app.graph.edges import after_validator

def build_pipeline():
    """
    Builds and compiles the ACMP LangGraph pipeline.

    Flow:
        START
          ↓
        profiler
          ↓
        anchor
          ↓
        architect
          ↓
        engineer
          ↓
        validator
          ↓
        after_validator() ← conditional edge
          ├── "end"   → END
          └── "fixer" → fixer → validator (loop)

    Returns:
        Compiled LangGraph StateGraph ready to invoke
    """

    builder = StateGraph(AgentState)

    builder.add_node("profiler",profiler_node)
    builder.add_node("anchor",anchor_node)
    builder.add_node("architect",architect_node)
    builder.add_node("engineer",engineer_node)
    builder.add_node("tester",tester_node)
    builder.add_node("fixer",fixer_node)

    builder.set_entry_point("profiler")
    builder.add_edge("profiler","anchor")
    builder.add_edge("anchor","architect")
    builder.add_edge("architect", "engineer")
    builder.add_edge("engineer", "tester")
    builder.add_conditional_edges("tester", after_validator, {"end" : END, "fixer" : "fixer"})
    builder.add_edge("fixer","tester")

    return builder.compile()


graph = build_pipeline()


