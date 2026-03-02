import uuid
from pathlib import Path

import chromadb

from app.core.config import get_settings
from app.rag.embeddings import get_embedding_function


# ─────────────────────────────────────────
# SUPPORTED FILE TYPES
# ─────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


# ─────────────────────────────────────────
# CHROMADB CLIENT
# Module level singleton
# Connect once — reuse everywhere
# ─────────────────────────────────────────

def get_chroma_collection():
    """
    Connect to ChromaDB and return the collection.
    Uses HttpClient to connect to ChromaDB Docker service.
    Uses get_or_create_collection for safe initialization.

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
# TEXT EXTRACTION
# Extract raw text from different file types
# ─────────────────────────────────────────

def extract_text(file_path: str) -> str:
    """
    Extract raw text content from uploaded file.
    Supports: .txt, .md, .pdf

    Args:
        file_path: Absolute path to the uploaded file

    Returns:
        Extracted text as a single string

    Raises:
        ValueError: If file type is not supported
    """
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {SUPPORTED_EXTENSIONS}"
        )

    # ── Plain text and Markdown ──────────────
    if extension in {".txt", ".md"}:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fallback encoding for non-UTF8 files
            return path.read_text(encoding="latin-1")

    # ── PDF ──────────────────────────────────
    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            extracted_pages = []

            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        extracted_pages.append(page_text)
                except Exception:
                    # Skip malformed pages — don't crash entire PDF
                    continue

            if not extracted_pages:
                return ""

            return "\n\n".join(extracted_pages)

        except Exception as e:
            raise ValueError(f"PDF extraction failed: {str(e)}")

    return ""


# ─────────────────────────────────────────
# TEXT CHUNKING
# Split long documents into overlapping chunks
# ─────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int,
    overlap: int
) -> list[str]:
    """
    Split a long document into overlapping chunks.

    Why overlapping?
    Important context often sits at chunk boundaries.
    Overlap ensures no information is lost at split points.

    Example with chunk_size=500, overlap=50:
        Chunk 1: characters 0   → 500
        Chunk 2: characters 450 → 950   (50 char overlap)
        Chunk 3: characters 900 → 1400  (50 char overlap)

    Args:
        text:       Full document text to split
        chunk_size: Maximum characters per chunk
        overlap:    Characters to overlap between chunks

    Returns:
        List of text chunk strings
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Don't cut in the middle of a word
        # Find the last space before the cut point
        if end < len(text):
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        # Move forward by chunk_size minus overlap
        # This creates the sliding window effect
        start = end - overlap

        # Safety check — prevent infinite loop
        # if overlap >= chunk_size
        if start <= 0 or start >= len(text):
            break

    return chunks


# ─────────────────────────────────────────
# MAIN INGESTION FUNCTION
# Orchestrates the full ingestion pipeline
# ─────────────────────────────────────────

async def ingest_document(
    file_path: str,
    language: str,
    framework: str
) -> dict:
    """
    Main ingestion pipeline.
    Extracts, chunks and stores a document in ChromaDB.

    Pipeline:
        1. Extract text from file
        2. Split into overlapping chunks
        3. Generate unique ID for each chunk
        4. Store chunks in ChromaDB with metadata
        5. Return ingestion summary

    Args:
        file_path: Path to the uploaded document
        language:  Programming language this doc covers
        framework: Framework this doc covers

    Returns:
        dict: {
            "status": "success" or "failed",
            "chunks_stored": int,
            "source": filename,
            "language": language,
            "framework": framework,
            "message": human readable result
        }
    """
    settings = get_settings()
    path = Path(file_path)
    filename = path.name

    try:
        # ── Step 1: Extract text ─────────────────
        text = extract_text(file_path)

        if not text or not text.strip():
            return {
                "status": "failed",
                "chunks_stored": 0,
                "source": filename,
                "language": language,
                "framework": framework,
                "message": "No text could be extracted from the file"
            }

        # ── Step 2: Chunk the text ───────────────
        chunks = chunk_text(
            text=text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap
        )

        if not chunks:
            return {
                "status": "failed",
                "chunks_stored": 0,
                "source": filename,
                "language": language,
                "framework": framework,
                "message": "Document produced no chunks after splitting"
            }

        # ── Step 3: Connect to ChromaDB ──────────
        collection = get_chroma_collection()

        # ── Step 4: Prepare data for ChromaDB ────
        ids        = []
        documents  = []
        metadatas  = []

        for i, chunk in enumerate(chunks):
            # Unique ID: prevents duplicate chunk storage
            # Uses uuid + filename + index for guaranteed uniqueness
            chunk_id = f"{uuid.uuid4().hex}_{filename}_{i}"

            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "language":    language.lower().strip(),
                "framework":   framework.lower().strip(),
                "source":      filename,
                "chunk_index": i
            })

        # ── Step 5: Store in ChromaDB ────────────
        # ChromaDB handles embedding generation internally
        # using our registered embedding function
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        return {
            "status": "success",
            "chunks_stored": len(chunks),
            "source": filename,
            "language": language,
            "framework": framework,
            "message": f"Successfully stored {len(chunks)} chunks from {filename}"
        }

    except Exception as e:
        return {
            "status": "failed",
            "chunks_stored": 0,
            "source": filename,
            "language": language,
            "framework": framework,
            "message": f"Ingestion failed: {str(e)}"
        }