from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base import BaseAgent
from app.agents.prompts import ANCHOR_HUMAN_PROMPT, ANCHOR_SYSTEM_PROMPT
from app.graph.state import AgentState
from app.core.config import get_settings


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
        source_name = metadata.get("source_name", "original_file")

        messages = [
            SystemMessage(content=ANCHOR_SYSTEM_PROMPT),
            HumanMessage(content=ANCHOR_HUMAN_PROMPT.format(
                language=language,
                framework=framework,
                code=original_code,
                source_name=source_name
            ))
        ]

        # Async LLM call
        response = await self.llm.ainvoke(messages)

        # Clean response
        unit_tests = self._clean_response(response.content)

        print("\n\nGenerated Unit Tests:\n", unit_tests)

        return {
            "unit_tests": unit_tests
        }