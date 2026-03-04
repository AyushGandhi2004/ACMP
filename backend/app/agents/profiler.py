import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base import BaseAgent
from app.graph.state import AgentState
from app.core.config import get_settings
from app.domain.enums import SupportedLanguage, SupportedFramework


# ─────────────────────────────────────────
# PROMPTS
# Defined as constants at module level
# Easy to tune without touching logic
# ─────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert code analysis engine specialized in detecting 
programming languages, frameworks, and version patterns.

Your job is to analyze the provided source code and return a JSON object.

STRICT RULES:
- Return ONLY a valid JSON object
- No explanations
- No markdown
- No backticks
- No extra text of any kind

JSON format to return:
{
    "language": "<detected language in lowercase>",
    "framework": "<detected framework in lowercase or unknown>",
    "version": "<detected version as string or unknown>"
}

Valid languages: python, javascript, typescript, java
Valid frameworks: django, flask, fastapi, express, react, spring, unknown
"""

HUMAN_PROMPT = """
Analyze this code and return the JSON detection result:

{code}
"""


class ProfilerAgent(BaseAgent):
    """
    Profiler Agent — First agent in the ACMP pipeline.

    Responsibilities:
    - Detect programming language
    - Detect framework being used
    - Detect version patterns

    Input  (from state): original_code
    Output (to state)  : metadata dict
    """

    def __init__(self):
        settings = get_settings()
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.model,
            temperature=0       # deterministic — no creativity needed for detection
        )


    def _parse_response(self, response_text: str) -> dict:
        """
        Safely parse the LLM JSON response.
        Falls back to safe defaults if parsing fails.

        Args:
            response_text: Raw string response from LLM

        Returns:
            dict with language, framework, version keys
        """
        try:
            # Clean response in case LLM added backticks despite instructions
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                # Remove opening and closing backticks
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]   # remove the word "json"

            parsed = json.loads(cleaned)

            # Validate language against supported enum
            # If LLM returns an unsupported language — store as raw string
            language = parsed.get("language", "unknown").lower().strip()
            try:
                SupportedLanguage(language)     # validate it exists in enum
            except ValueError:
                language = "unknown"

            # Validate framework against supported enum
            framework = parsed.get("framework", "unknown").lower().strip()
            try:
                SupportedFramework(framework)   # validate it exists in enum
            except ValueError:
                framework = "unknown"

            return {
                "language": language,
                "framework": framework,
                "version": parsed.get("version", "unknown")
            }

        except (json.JSONDecodeError, KeyError, AttributeError):
            # If anything goes wrong — return safe defaults
            # Pipeline continues rather than crashing
            return {
                "language": "unknown",
                "framework": "unknown",
                "version": "unknown"
            }


    async def run(self, state: AgentState) -> dict:
        """
        Main entry point for the Profiler Agent.
        Called by profiler_node in nodes.py

        Args:
            state: Current ACMPState

        Returns:
            dict: {"metadata": {...}}
        """
        original_code = state.get("original_code", "")

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=HUMAN_PROMPT.format(code=original_code))
        ]

        # Async LLM call — never use .invoke() in async context
        response = await self.llm.ainvoke(messages)

        # Parse and validate the response
        metadata = self._parse_response(response.content)

        print("\n[ProfilerAgent] Detected Metadata:\n", metadata)

        return {
            "metadata": metadata
        }