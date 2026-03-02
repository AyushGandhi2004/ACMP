from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.websocket import router as websocket_router
from app.api.v1.admin import router as admin_router


# ─────────────────────────────────────────
# FASTAPI APPLICATION
# ─────────────────────────────────────────

app = FastAPI(
    title="ACMP - Autonomous Code Modernization Platform",
    description="""
    A multi-agent AI system that refactors legacy code
    into modern standards while maintaining 100% functional parity.

    ## Agents
    - **Profiler**     — Detects language, framework and version
    - **Logic Anchor** — Generates unit tests to lock in behavior
    - **Architect**    — Queries RAG and builds transformation plan
    - **Engineer**     — Refactors code using transformation plan
    - **Validator**    — Runs tests in Docker sandbox
    - **Fixer**        — Fixes syntax errors and retries validation

    ## Flow
    Upload legacy code → Pipeline runs → Receive modernized code
    """,
    version="1.0.0",
    docs_url="/docs",       # Swagger UI available at /docs
    redoc_url="/redoc"      # ReDoc available at /redoc
)


# ─────────────────────────────────────────
# CORS MIDDLEWARE
# Must be added BEFORE routers
# Allows frontend on port 5173 to call
# backend on port 8000
# ─────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://127.0.0.1:5173",   # Alternate localhost
    ],
    allow_credentials=True,         # Allow cookies and auth headers
    allow_methods=["*"],            # Allow all HTTP methods
    allow_headers=["*"],            # Allow all headers
)


# ─────────────────────────────────────────
# ROUTERS
# Register all API routers with prefixes
# ─────────────────────────────────────────

# Pipeline routes — /api/v1/pipeline/run
#                   /api/v1/pipeline/result/{session_id}
app.include_router(
    pipeline_router,
    prefix="/api/v1/pipeline",
    tags=["Pipeline"]
)

# WebSocket route — /api/v1/ws/{session_id}
app.include_router(
    websocket_router,
    prefix="/api/v1",
    tags=["WebSocket"]
)

# Admin routes — /api/v1/admin/login
#                /api/v1/admin/documents/upload
#                /api/v1/admin/documents
app.include_router(
    admin_router,
    prefix="/api/v1/admin",
    tags=["Admin"]
)


# ─────────────────────────────────────────
# HEALTH CHECK
# Simple endpoint to verify backend is running
# Used by Docker Compose healthcheck
# and frontend to verify connectivity
# ─────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.
    Returns 200 if backend is running correctly.
    """
    return {
        "status":  "healthy",
        "service": "ACMP Backend",
        "version": "1.0.0"
    }


# ─────────────────────────────────────────
# ROOT ENDPOINT
# Friendly message for anyone hitting
# the root URL directly
# ─────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint.
    Returns basic API information.
    """
    return {
        "message": "Welcome to ACMP - Autonomous Code Modernization Platform",
        "docs":    "http://localhost:8000/docs",
        "health":  "http://localhost:8000/health",
        "version": "1.0.0"
    }