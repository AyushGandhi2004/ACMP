from chromadb import EmbeddingFunction
from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


# ─────────────────────────────────────────
# SENTENCE TRANSFORMER EMBEDDING WRAPPER
# Wraps SentenceTransformer in ChromaDB's
# EmbeddingFunction interface so ChromaDB
# can use it directly for storage and search
# ─────────────────────────────────────────

class SentenceTransformerEmbedding(EmbeddingFunction):
    """
    ChromaDB compatible embedding function
    using the free local SentenceTransformer model.

    Model: all-MiniLM-L6-v2
    - Completely free
    - Runs locally — no API calls
    - Fast and lightweight
    - Good semantic search quality

    Downloaded automatically on first use.
    Cached locally after first download.
    """

    def __init__(self):
        settings = get_settings()
        # Load model from settings
        # First run downloads model (~80MB)
        # Subsequent runs load from local cache
        self.model = SentenceTransformer(settings.embedding_model)


    def __call__(self, input: list[str]) -> list[list[float]]:
        """
        ChromaDB calls this method when it needs
        to embed documents or queries.

        Args:
            input: List of strings to embed

        Returns:
            List of embedding vectors (list of floats)
        """
        embeddings = self.model.encode(
            input,
            convert_to_numpy=True,  # faster than tensor conversion
            show_progress_bar=False # no progress spam in production
        )
        return embeddings.tolist()


# ─────────────────────────────────────────
# MODULE LEVEL SINGLETON
# Embedding model is heavy to load
# Create once and reuse everywhere
# ─────────────────────────────────────────
_embedding_function = None


def get_embedding_function() -> SentenceTransformerEmbedding:
    """
    Returns a cached instance of the embedding function.
    Model is loaded exactly once — reused on every call.

    Usage:
        from app.rag.embeddings import get_embedding_function
        ef = get_embedding_function()
    """
    global _embedding_function
    if _embedding_function is None:
        _embedding_function = SentenceTransformerEmbedding()
    return _embedding_function


def embed_text(text: str) -> list[float]:
    """
    Embed a single string and return its vector.
    Convenience function for one-off embeddings.

    Args:
        text: String to embed

    Returns:
        List of floats representing the embedding vector
    """
    ef = get_embedding_function()
    result = ef([text])
    return result[0]    # return first (and only) vector