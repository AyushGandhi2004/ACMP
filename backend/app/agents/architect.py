import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.base import BaseAgent
from app.graph.state import AgentState
from app.core.config import get_settings


# ─────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────

SYSTEM_PROMPT = """
You are a senior software architect specialized in code modernization
and technology migration.

Your job is to analyze legacy code and create a detailed, 
step by step transformation plan to modernize it.

You will be provided with:
1. The original legacy code
2. Detected language and framework
3. Relevant migration documentation snippets

STRICT RULES:
- Return ONLY a valid JSON object
- No explanations
- No markdown
- No backticks
- No extra text of any kind not even the language and framework name

JSON format to return:
{
    "steps": [
        "Step 1: description of first transformation",
        "Step 2: description of second transformation"
    ],
    "documentation_snippets": [
        "relevant documentation excerpt used for planning"
    ]
}

Make steps specific, actionable and ordered correctly.
Each step should describe exactly what needs to change and why.
"""

HUMAN_PROMPT = """
Create a detailed modernization plan for this code.

DETECTED METADATA:
Language  : {language}
Framework : {framework}
Version   : {version}

RELEVANT MIGRATION DOCUMENTATION:
{documentation}

ORIGINAL LEGACY CODE:
{code}

Return the transformation plan as a JSON object.
Be specific about what patterns to update, what APIs are deprecated,
and what modern equivalents should be used.
"""


class ArchitectAgent(BaseAgent):
    """
    Architect Agent — Third agent in the ACMP pipeline.

    Responsibilities:
    - Query ChromaDB RAG system for relevant migration docs
    - Analyze original code against retrieved documentation
    - Generate a detailed step by step transformation plan

    This is the RAG agent — it combines retrieval with generation.

    Input  (from state): original_code, metadata
    Output (to state)  : transformation_plan dict
    """

    def __init__(self):
        settings = get_settings()
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.model,
            temperature=0       # deterministic planning
        )


    def _parse_response(self, response_text: str) -> dict:
        """
        Safely parse the LLM JSON response.
        Falls back to a basic plan if parsing fails.

        Args:
            response_text: Raw string response from LLM

        Returns:
            dict with steps and documentation_snippets keys
        """
        try:
            cleaned = response_text.strip()

            # Handle markdown code blocks
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]

            parsed = json.loads(cleaned)

            return {
                "steps": parsed.get("steps", []),
                "documentation_snippets": parsed.get(
                    "documentation_snippets", []
                )
            }

        except (json.JSONDecodeError, KeyError, AttributeError):
            # Return a basic fallback plan so pipeline continues
            return {
                "steps": [
                    "Step 1: Analyze and update deprecated syntax",
                    "Step 2: Update dependencies to modern versions",
                    "Step 3: Apply modern design patterns"
                ],
                "documentation_snippets": []
            }


    async def _get_documentation(
        self,
        language: str,
        framework: str
    ) -> str:
        """
        Query ChromaDB RAG system for relevant migration docs.
        Filters by language and framework metadata.

        Args:
            language:  Detected programming language
            framework: Detected framework

        Returns:
            Concatenated documentation string for prompt injection
        """
        try:
            # Import here to avoid circular imports
            # RAG system is built in Step 5
            from app.rag.retrieval import retrieve_documents

            docs = await retrieve_documents(
                query=f"migrate {language} {framework} modernization best practices",
                language=language,
                framework=framework,
                n_results=5         # top 5 most relevant chunks
            )

            if not docs:
                return "No specific migration documentation found. Apply general modernization best practices."

            # Concatenate all retrieved chunks into one string
            return "\n\n---\n\n".join(docs)

        except Exception:
            # If RAG fails — pipeline continues with general knowledge
            return "No documentation retrieved. Apply general modernization best practices."


    async def run(self, state: AgentState) -> dict:
        """
        Main entry point for the Architect Agent.
        Called by architect_node in nodes.py

        Args:
            state: Current AgentState containing
                   original_code and metadata

        Returns:
            dict: {"transformation_plan": {...}}
        """
        original_code = state.get("original_code", "")
        metadata      = state.get("metadata", {})
        language      = metadata.get("language", "unknown")
        framework     = metadata.get("framework", "unknown")
        version       = metadata.get("version", "unknown")

        # Step 1 — Retrieve relevant documentation from ChromaDB
        documentation = await self._get_documentation(language, framework)

        # Step 2 — Build messages with code + docs + metadata
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=HUMAN_PROMPT.format(
                language=language,
                framework=framework,
                version=version,
                documentation=documentation,
                code=original_code
            ))
        ]

        # Step 3 — Async LLM call
        response = await self.llm.ainvoke(messages)

        # Step 4 — Parse and validate response
        transformation_plan = self._parse_response(response.content)

        return {
            "transformation_plan": transformation_plan
        }