from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base import BaseAgent
from app.graph.state import AgentState
from app.core.config import get_settings


# ─────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────

SYSTEM_PROMPT = """
You are a senior software engineer specialized in writing 
comprehensive unit tests.

Your job is to analyze the provided source code and generate 
unit tests that completely lock in the original behavior.

STRICT RULES:
- Generate ONLY the test code
- No explanations
- No markdown
- No backticks
- Raw code only
- Use the appropriate test framework:
    Python      → pytest
    JavaScript  → jest
    TypeScript  → jest
    Java        → JUnit

TEST REQUIREMENTS:
- Test every function present in the code
- Test normal expected inputs
- Test edge cases (empty inputs, zero values, None/null)
- Test boundary conditions
- Each test must have a clear descriptive name
- Tests must be self contained and runnable
"""

HUMAN_PROMPT = """
Generate comprehensive unit tests for this {language} code.
Framework detected: {framework}

Original code to test:

{code}

Remember:
- Test every function
- Cover edge cases
- Return ONLY raw test code
- No explanations or markdown
"""


class AnchorAgent(BaseAgent):
    """
    Anchor Agent — Second agent in the ACMP pipeline.

    Responsibilities:
    - Analyze original code structure
    - Generate comprehensive unit tests
    - Lock in original behavior as a test contract
      that modernized code must satisfy

    Input  (from state): original_code, metadata
    Output (to state)  : unit_tests string
    """

    def __init__(self):
        settings = get_settings()
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.model,
            temperature=0.1     # slight creativity for test variety
                                # but mostly deterministic
        )


    def _clean_response(self, response_text: str) -> str:
        """
        Clean LLM response in case it added markdown
        despite being told not to.

        Args:
            response_text: Raw string response from LLM

        Returns:
            Clean test code string
        """
        cleaned = response_text.strip()

        # Handle markdown code blocks
        if "```" in cleaned:
            # Extract content between first and last backtick blocks
            parts = cleaned.split("```")
            # parts[1] contains the code block content
            if len(parts) >= 2:
                code_block = parts[1]
                # Remove language identifier if present
                # e.g. "python\nimport pytest..." → "import pytest..."
                lines = code_block.split("\n")
                if lines[0].strip().lower() in [
                    "python", "javascript",
                    "typescript", "java", ""
                ]:
                    lines = lines[1:]   # remove first line (language tag)
                cleaned = "\n".join(lines)

        return cleaned.strip()


    async def run(self, state: AgentState) -> dict:
        """
        Main entry point for the Anchor Agent.
        Called by anchor_node in nodes.py

        Args:
            state: Current AgentState containing
                   original_code and metadata

        Returns:
            dict: {"unit_tests": "test code string"}
        """
        original_code = state.get("original_code", "")
        metadata      = state.get("metadata", {})
        language      = metadata.get("language", "unknown")
        framework     = metadata.get("framework", "unknown")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=HUMAN_PROMPT.format(
                language=language,
                framework=framework,
                code=original_code
            ))
        ]

        # Async LLM call
        response = await self.llm.ainvoke(messages)

        # Clean response
        unit_tests = self._clean_response(response.content)

        return {
            "unit_tests": unit_tests
        }