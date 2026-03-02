import os
import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import get_settings
from app.core.security import create_access_token, get_current_admin, verify_password
from app.rag.ingestion import get_chroma_collection, ingest_document


# ─────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────

router = APIRouter()


# ─────────────────────────────────────────
# TEMP UPLOAD DIRECTORY
# Files are saved here before ingestion
# Cleaned up after ingestion completes
# ─────────────────────────────────────────

UPLOAD_DIR = Path("/temp_sandboxes/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────
# POST /login
# Admin authentication endpoint
# Returns JWT access token on success
# ─────────────────────────────────────────

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends()
) -> dict:
    """
    Admin login endpoint.
    Validates credentials against .env values.
    Returns JWT access token on success.

    Uses OAuth2PasswordRequestForm which expects:
        - username: string
        - password: string
    Sent as form data — not JSON.

    Args:
        form_data: OAuth2 form with username and password

    Returns:
        dict with access_token and token_type

    Raises:
        HTTPException 401 if credentials are invalid
    """
    settings = get_settings()

    # Verify username
    if form_data.username != settings.admin_username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify password using constant time comparison
    if not verify_password(form_data.password, settings.admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Create and return access token
    access_token = create_access_token(
        data={"sub": form_data.username}
    )

    return {
        "access_token": access_token,
        "token_type":   "bearer"
    }


# ─────────────────────────────────────────
# POST /documents/upload
# Upload a document to the RAG knowledge base
# Protected — requires valid admin JWT
# ─────────────────────────────────────────

@router.post("/documents/upload", status_code=201)
async def upload_document(
    file: UploadFile   = File(...),
    language: str      = Form(...),
    framework: str     = Form(...),
    current_admin: str = Depends(get_current_admin)
) -> dict:
    """
    Upload a document to the RAG knowledge base.
    Document is chunked, embedded and stored in ChromaDB.

    Accepts:
        file:     .txt, .md, or .pdf file
        language: Programming language this doc covers
                  e.g. "python", "javascript"
        framework: Framework this doc covers
                  e.g. "django", "flask", "unknown"

    Protected by JWT — must include Authorization header:
        Authorization: Bearer <token>

    Args:
        file:          Uploaded file object
        language:      Target language for RAG filtering
        framework:     Target framework for RAG filtering
        current_admin: Injected by get_current_admin dependency

    Returns:
        Ingestion summary dict

    Raises:
        HTTPException 400 if file type not supported
        HTTPException 500 if ingestion fails
    """

    # ── Validate file type ────────────────────────
    allowed_extensions = {".txt", ".md", ".pdf"}
    file_extension = Path(file.filename).suffix.lower()

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_extension} not supported. "
                   f"Allowed: {allowed_extensions}"
        )

    # ── Save uploaded file to temp directory ─────
    # UploadFile is a stream — must save to disk
    # before passing path to ingest_document()
    temp_file_path = UPLOAD_DIR / file.filename

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # ── Run ingestion pipeline ────────────────────
    try:
        result = await ingest_document(
            file_path=str(temp_file_path),
            language=language.lower().strip(),
            framework=framework.lower().strip()
        )

        if result["status"] == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )

        return result

    finally:
        # ── Always clean up temp file ─────────────
        # Whether ingestion succeeded or failed
        # temp file must be removed
        try:
            os.remove(temp_file_path)
        except Exception:
            pass    # cleanup failure should never crash the response


# ─────────────────────────────────────────
# GET /documents
# List all documents stored in ChromaDB
# Protected — requires valid admin JWT
# ─────────────────────────────────────────

@router.get("/documents", status_code=200)
async def list_documents(
    current_admin: str = Depends(get_current_admin)
) -> dict:
    """
    List all documents currently stored in ChromaDB.
    Shows source filenames, languages and frameworks.

    Protected by JWT — must include Authorization header:
        Authorization: Bearer <token>

    Args:
        current_admin: Injected by get_current_admin dependency

    Returns:
        dict with total count and list of document metadata

    Raises:
        HTTPException 500 if ChromaDB query fails
    """
    try:
        collection = get_chroma_collection()

        # Get all stored items with their metadata
        # We only need metadata — not the actual content
        results = collection.get(
            include=["metadatas"]
        )

        metadatas = results.get("metadatas", [])

        # Deduplicate by source filename
        # Multiple chunks from same file → show file once
        seen_sources  = set()
        unique_documents = []

        for metadata in metadatas:
            source = metadata.get("source", "unknown")
            if source not in seen_sources:
                seen_sources.add(source)
                unique_documents.append({
                    "source":    source,
                    "language":  metadata.get("language",  "unknown"),
                    "framework": metadata.get("framework", "unknown")
                })

        return {
            "total":     len(unique_documents),
            "documents": unique_documents
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve documents: {str(e)}"
        )