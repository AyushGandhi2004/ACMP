import chromadb

from app.core.config import get_settings
from app.rag.embeddings import get_embedding_function


# ─────────────────────────────────────────
# CHROMADB CONNECTION
# ─────────────────────────────────────────

def get_chroma_collection():
    """
    Connect to ChromaDB and return the collection.
    Mirrors the connection pattern in ingestion.py
    to ensure consistent collection access.

    Returns:
        ChromaDB collection object
    """
    settings = get_settings()

    client = chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port
    )

    collection = client.get_or_create_collection(
        name=settings.chroma_collection_name,
        embedding_function=get_embedding_function()
    )

    return collection


# ─────────────────────────────────────────
# METADATA FILTER BUILDER
# Builds ChromaDB where clause based on
# available language and framework info
# ─────────────────────────────────────────

def build_metadata_filter(
    language: str,
    framework: str
) -> dict | None:
    """
    Build ChromaDB metadata filter based on
    detected language and framework.

    Filter Strategy (most specific → least specific):
        1. language AND framework  → most targeted results
        2. language only           → when framework is unknown
        3. None                    → no filter, last resort fallback

    Args:
        language:  Detected programming language
        framework: Detected framework or "unknown"

    Returns:
        ChromaDB where clause dict or None
    """
    # Normalize inputs
    language  = language.lower().strip()
    framework = framework.lower().strip()

    # ── Strategy 1: Both language and framework known ──
    if language != "unknown" and framework != "unknown":
        return {
            "$and": [
                {"language":  {"$eq": language}},
                {"framework": {"$eq": framework}}
            ]
        }

    # ── Strategy 2: Only language known ───────────────
    if language != "unknown":
        return {
            "language": {"$eq": language}
        }

    # ── Strategy 3: Nothing known — no filter ─────────
    # Returns most semantically similar docs regardless
    # of language or framework
    return None


# ─────────────────────────────────────────
# MAIN RETRIEVAL FUNCTION
# Called by Architect Agent during pipeline
# ─────────────────────────────────────────

async def retrieve_documents(
    query: str,
    language: str,
    framework: str,
    n_results: int = 5
) -> list[str]:
    """
    Query ChromaDB for documents relevant to
    the modernization task.

    Retrieval Strategy:
        1. Try most specific filter (language + framework)
        2. If no results → try language only filter
        3. If still no results → try no filter at all
        4. If still nothing → return empty list

    This cascading fallback ensures the Architect
    always gets SOMETHING to work with if docs exist.

    Args:
        query:     Natural language search query
        language:  Detected programming language
        framework: Detected framework or "unknown"
        n_results: Number of chunks to retrieve

    Returns:
        List of relevant document chunk strings
    """
    settings = get_settings()

    try:
        collection = get_chroma_collection()

        # Check if collection has any documents at all
        # Avoids querying an empty collection
        collection_count = collection.count()
        if collection_count == 0:
            return []

        # Adjust n_results if collection is smaller
        # than requested — ChromaDB throws error otherwise
        n_results = min(n_results, collection_count)

        # ── Attempt 1: Language + Framework filter ────
        where_filter = build_metadata_filter(language, framework)

        results = _query_collection(
            collection=collection,
            query=query,
            n_results=n_results,
            where_filter=where_filter
        )

        if results:
            return results

        # ── Attempt 2: Language only filter ──────────
        # Only retry if we were previously filtering
        # by both language and framework
        if (
            language != "unknown"
            and framework != "unknown"
        ):
            language_only_filter = build_metadata_filter(
                language=language,
                framework="unknown"  # forces language-only filter
            )

            results = _query_collection(
                collection=collection,
                query=query,
                n_results=n_results,
                where_filter=language_only_filter
            )

            if results:
                return results

        # ── Attempt 3: No filter at all ───────────────
        results = _query_collection(
            collection=collection,
            query=query,
            n_results=n_results,
            where_filter=None
        )

        return results

    except Exception:
        # RAG failure must never crash the pipeline
        # Architect falls back to general LLM knowledge
        return []


# ─────────────────────────────────────────
# INTERNAL QUERY HELPER
# Keeps retrieval logic clean and DRY
# ─────────────────────────────────────────

def _query_collection(
    collection,
    query: str,
    n_results: int,
    where_filter: dict | None
) -> list[str]:
    """
    Execute a ChromaDB query and return document strings.
    Internal helper — not called directly by other modules.

    Args:
        collection:   ChromaDB collection object
        query:        Natural language search query
        n_results:    Number of results to retrieve
        where_filter: ChromaDB metadata filter or None

    Returns:
        List of document chunk strings
        Empty list if query fails or returns nothing
    """
    try:
        # Build query kwargs
        query_kwargs = {
            "query_texts": [query],
            "n_results":   n_results,
        }

        # Only add where clause if filter exists
        if where_filter is not None:
            query_kwargs["where"] = where_filter

        results = collection.query(**query_kwargs)

        # ChromaDB returns nested lists
        # results["documents"] = [[chunk1, chunk2, ...]]
        # We want the inner list — the actual chunks
        documents = results.get("documents", [[]])
        if documents and len(documents) > 0:
            return documents[0]     # unwrap outer list

        return []

    except Exception:
        return []
