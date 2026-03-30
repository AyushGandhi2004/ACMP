from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base import BaseAgent
from app.agents.prompts import ENGINEER_HUMAN_PROMPT, build_engineer_system_prompt
from app.graph.state import AgentState
from app.core.config import get_settings


class EngineerAgent(BaseAgent):
    """
    Engineer Agent — Fourth agent in the ACMP pipeline.

    Responsibilities:
    - Receive original code and transformation plan
    - Refactor code to modern standards
    - Strictly preserve all function names and signatures
    - Strictly preserve all original behavior

    This is the most critical agent — output quality
    depends entirely on prompt precision.

    Input  (from state): original_code, metadata, transformation_plan
    Output (to state)  : modern_code string
    """

    def __init__(self):
        settings = get_settings()
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.model,
            temperature=0.1     # very low — slight flexibility for
                                # modern code style improvements
                                # but behavior must stay identical
        )


    def _clean_response(self, response_text: str) -> str:
        """
        Clean LLM response removing any markdown
        the LLM may have added despite instructions.

        Args:
            response_text: Raw string response from LLM

        Returns:
            Clean modernized code string
        """
        cleaned = response_text.strip()

        # Handle markdown code blocks
        if "```" in cleaned:
            parts = cleaned.split("```")
            if len(parts) >= 2:
                code_block = parts[1]
                # Remove language identifier line if present
                lines = code_block.split("\n")
                if lines[0].strip().lower() in [
                    "python", "javascript",
                    "typescript", "java", ""
                ]:
                    lines = lines[1:]
                cleaned = "\n".join(lines)

        return cleaned.strip()


    def _format_transformation_plan(
        self,
        transformation_plan: dict
    ) -> str:
        """
        Format the transformation plan dict into
        a clean readable string for prompt injection.

        Args:
            transformation_plan: dict from Architect agent

        Returns:
            Formatted string representation of the plan
        """
        steps = transformation_plan.get("steps", [])
        docs  = transformation_plan.get("documentation_snippets", [])

        # Format steps as numbered list
        formatted_steps = "\n".join([
            f"{i + 1}. {step}"
            for i, step in enumerate(steps)
        ])

        # Format documentation snippets if present
        formatted_docs = ""
        if docs:
            formatted_docs = "\n\nRELEVANT DOCUMENTATION:\n" + "\n---\n".join(docs)

        return formatted_steps + formatted_docs


    async def run(self, state: AgentState) -> dict:
        """
        Main entry point for the Engineer Agent.
        Called by engineer_node in nodes.py

        Args:
            state: Current AgentState containing
                   original_code, metadata,
                   and transformation_plan

        Returns:
            dict: {"modern_code": "modernized code string"}
        """
        original_code       = state.get("original_code", "")
        metadata            = state.get("metadata", {})
        transformation_plan = state.get("transformation_plan", {})
        language            = metadata.get("language", "unknown")
        framework           = metadata.get("framework", "unknown")
        version             = metadata.get("version", "unknown")

        # Format transformation plan for prompt
        formatted_plan = self._format_transformation_plan(
            transformation_plan
        )
        system_prompt = build_engineer_system_prompt(
            language=language,
            framework=framework
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=ENGINEER_HUMAN_PROMPT.format(
                language=language,
                framework=framework,
                version=version,
                transformation_plan=formatted_plan,
                code=original_code
            ))
        ]

        # Async LLM call
        response = await self.llm.ainvoke(messages)

        # Clean response
        modern_code = self._clean_response(response.content)

        print("\n\nmodern_code produced\n")  # Debugging output

        return {
            "modern_code": modern_code
        }