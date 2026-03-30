from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base import BaseAgent
from app.agents.prompts import FIXER_HUMAN_PROMPT, FIXER_SYSTEM_PROMPT
from app.graph.state import AgentState
from app.core.config import get_settings


class FixerAgent(BaseAgent):
    """
    Fixer Agent — Sixth and final agent in the ACMP pipeline.
    Only activated when Validator finds failures.

    Responsibilities:
    - Receive modernized code that failed validation
    - Receive exact error logs from Docker sandbox
    - Fix SYNTAX ERRORS ONLY
    - Never modify logic, behavior or function signatures
    - Hand fixed code back to Validator for re-testing

    This agent operates in a loop with Validator:
    Fixer → Validator → Fixer → Validator
    Until tests pass or max_retries is exceeded.

    Input  (from state): modern_code, error_logs,
                         metadata, retry_count
    Output (to state)  : modern_code, retry_count
    """

    def __init__(self):
        settings = get_settings()
        self.settings = settings
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.model,
            temperature=0       # zero creativity — pure syntax fixing
                                # any randomness risks logic changes
        )


    def _clean_response(self, response_text: str) -> str:
        """
        Clean LLM response removing any markdown
        the LLM may have added despite instructions.

        Args:
            response_text: Raw string response from LLM

        Returns:
            Clean fixed code string
        """
        cleaned = response_text.strip()

        # Handle markdown code blocks
        if "```" in cleaned:
            parts = cleaned.split("```")
            if len(parts) >= 2:
                code_block = parts[1]
                lines = code_block.split("\n")
                # Remove language identifier line if present
                if lines[0].strip().lower() in [
                    "python", "javascript",
                    "typescript", "java", ""
                ]:
                    lines = lines[1:]
                cleaned = "\n".join(lines)

        return cleaned.strip()


    def _extract_relevant_errors(
        self,
        error_logs: str,
        max_lines: int = 50
    ) -> str:
        """
        Extract the most relevant error lines from validation logs.
        Prevents sending enormous log files to the LLM
        which wastes tokens and reduces fix quality.

        Args:
            error_logs: Full stdout/stderr from Docker run
            max_lines:       Maximum lines to send to LLM

        Returns:
            Trimmed error log string
        """
        if not error_logs:
            return "No error logs available"

        lines = error_logs.strip().split("\n")

        # If logs are short enough — send everything
        if len(lines) <= max_lines:
            return error_logs

        # Otherwise prioritize lines containing error keywords
        error_keywords = [
            "error", "exception", "failed",
            "syntaxerror", "traceback", "assert",
            "TypeError", "ValueError", "ImportError"
        ]

        error_lines = []
        other_lines = []

        for line in lines:
            if any(
                keyword in line.lower()
                for keyword in error_keywords
            ):
                error_lines.append(line)
            else:
                other_lines.append(line)

        # Combine error lines first then fill with others up to max
        combined = error_lines + other_lines
        return "\n".join(combined[:max_lines])


    async def run(self, state: AgentState) -> dict:
        """
        Main entry point for the Fixer Agent.
        Called by fixer_node in nodes.py

        Args:
            state: Current AgentState containing
                   modern_code, error_logs,
                   metadata and retry_count

        Returns:
            dict: {
                "modern_code": "syntax fixed code",
                "retry_count": incremented count
            }
        """
        modern_code      = state.get("modern_code", "")
        error_logs  = state.get("error_logs", "")
        metadata         = state.get("metadata", {})
        retry_count      = state.get("retry_count", 0)
        language         = metadata.get("language", "unknown")

        # Extract most relevant errors to send to LLM
        relevant_errors = self._extract_relevant_errors(
            error_logs
        )

        messages = [
            SystemMessage(content=FIXER_SYSTEM_PROMPT),
            HumanMessage(content=FIXER_HUMAN_PROMPT.format(
                language=language,
                error_logs=relevant_errors,
                code=modern_code,
                retry_count=retry_count + 1,
                max_retries=self.settings.max_retries
            ))
        ]

        # Async LLM call
        response = await self.llm.ainvoke(messages)

        # Clean response
        fixed_code = self._clean_response(response.content)

        print("\n\n[FixerAgent] LLM Responded\n", retry_count)

        # Increment retry count
        new_retry_count = retry_count + 1

        return {
            "modern_code": fixed_code,
            "retry_count": new_retry_count
        }