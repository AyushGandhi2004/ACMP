# ACMP — Autonomous Code Modernization Platform

> Upload legacy code. Watch 6 AI agents modernize it in real time. Get production-ready output with passing tests.

---

## What Is ACMP?

ACMP is a multi-agent AI pipeline that takes legacy source code and automatically modernizes it to current standards — preserving all original behavior and validating the output in a real Docker sandbox.

You paste old code. Six specialized AI agents collaborate to analyze, plan, rewrite, test and fix it. You get modernized code with a side-by-side diff and test results.

---

## Demo

```
Input  → Python 2.7 Django 1.x legacy code
Output → Python 3.12 modern code
```

---

## Architecture

```
Frontend (React + Vite)
        ↓ POST /api/v1/pipeline/run
FastAPI Backend
        ↓ returns session_id immediately
        ↓ runs pipeline in BackgroundTask
LangGraph State Machine
        ↓
  ┌─────────────────────────────────────┐
  │  1. Profiler    → detects language  │
  │  2. Anchor      → writes tests      │
  │  3. Architect   → RAG + plan        │
  │  4. Engineer    → rewrites code     │
  │  5. Tester      → runs in Docker    │
  │  6. Fixer       → fixes failures    │
  └─────────────────────────────────────┘
        ↓ WebSocket streams live events
Frontend shows live agent activity + diff
```

### Agent Responsibilities

| Agent | Job | LLM |
|---|---|---|
| **Profiler** | Detects language, framework, version | Groq |
| **Anchor** | Generates unit tests from original code | Groq |
| **Architect** | Queries RAG docs, builds transformation plan | Groq + ChromaDB |
| **Engineer** | Rewrites code following the plan | Groq |
| **Tester** | Runs tests in isolated Docker container | Docker SDK |
| **Fixer** | Fixes syntax errors, loops back to Validator | Groq |

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq (`llama-3.3-70b-versatile`) — free tier |
| Embeddings | `all-MiniLM-L6-v2` — runs locally, free |
| Vector DB | ChromaDB — local, no API key needed |
| Orchestration | LangGraph state machine |
| Backend | FastAPI + async Python |
| Sandbox | Docker SDK — isolated container per run |
| Frontend | React + Vite + Tailwind CSS |
| State | Zustand |
| Realtime | WebSocket |
| Auth | JWT (admin panel only) |

---

## Project Structure

```
acmp/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── base.py            # Abstract base agent
│   │   │   ├── profiler.py        # Language detection
│   │   │   ├── logic_anchor.py    # Test generation
│   │   │   ├── architect.py       # RAG + planning
│   │   │   ├── engineer.py        # Code modernization
│   │   │   ├── tester.py          # Docker sandbox execution
│   │   │   └── fixer.py           # Syntax error fixing
│   │   ├── graph/
│   │   │   ├── state.py           # ACMPState TypedDict
│   │   │   ├── nodes.py           # LangGraph node wrappers
│   │   │   ├── edges.py           # Conditional routing logic
│   │   │   └── pipeline.py        # Graph assembly + compilation
│   │   ├── rag/
│   │   │   ├── ingestion.py       # Chunk + embed + store docs
│   │   │   ├── retrieval.py       # Query ChromaDB
│   │   │   └── embeddings.py      # Sentence transformer setup
│   │   ├── api/v1/
│   │   │   ├── pipeline.py        # POST /run, GET /result
│   │   │   ├── websocket.py       # WS /ws/{session_id}
│   │   │   └── admin.py           # Login + doc upload
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic settings
│   │   │   ├── security.py        # JWT auth
│   │   │   └── events.py          # WebSocket manager
│   │   ├── domain/
│   │   │   ├── models.py          # Pydantic schemas
│   │   │   └── enums.py           # Language + framework enums
│   │   └── main.py                # FastAPI app entrypoint
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx           # Pipeline UI
│   │   │   └── Admin.jsx          # Doc upload + login
│   │   ├── components/
│   │   │   ├── CodeInput/         # Paste or upload code
│   │   │   ├── AgentPanel/        # Live WebSocket activity
│   │   │   ├── DiffViewer/        # Side-by-side code diff
│   │   │   ├── Banner/            # Success / error banner
│   │   │   └── LanguageSelector/  # Language picker
│   │   ├── hooks/
│   │   │   ├── useWebSocket.js    # WebSocket connection hook
│   │   │   └── usePipeline.js     # Pipeline orchestration hook
│   │   ├── services/
│   │   │   └── api.js             # Axios API client
│   │   ├── store/                 # Zustand state
│   │   └── App.jsx
│   ├── Dockerfile
│   └── package.json
├── chroma_data/                   # Persisted ChromaDB vectors
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites

- Docker + Docker Compose installed
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/acmp.git
cd acmp
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```dotenv
# LLM
GROQ_API_KEY=your_groq_api_key_here
MODEL=llama-3.3-70b-versatile

# Admin Panel
ADMIN_SECRET_KEY=your_secret_key_min_32_chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_admin_password

# Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8000
CHROMA_COLLECTION_NAME=acmp_knowledge

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000

# Pipeline
MAX_RETRIES=3
DOCKER_TIMEOUT=60
```

### 3. Start all services

```bash
docker compose up --build
```

This starts:
- **Frontend** → http://localhost:5173
- **Backend** → http://localhost:8000
- **ChromaDB** → http://localhost:8001
- **API Docs** → http://localhost:8000/docs

### 4. Run your first modernization

1. Open http://localhost:5173
2. Paste your legacy code into the editor
3. Select the language
4. Click **Run Pipeline**
5. Watch the 6 agents work in real time
6. Get your modernized code with a side-by-side diff

---

## Admin Panel — RAG Document Upload

The Architect agent uses ChromaDB to retrieve migration documentation relevant to your code. The more relevant docs you upload, the better the transformation plans become.

### Login

Navigate to http://localhost:5173/admin

Default credentials are whatever you set in `.env`:
```
Username: your ADMIN_USERNAME value
Password: your ADMIN_PASSWORD value
```

### Upload Migration Docs

Upload `.txt`, `.md`, or `.pdf` files tagged with a language and framework. Examples of useful docs:

- Django 1.x → 4.x migration guide
- Python 2 → 3 porting guide
- Flask migration notes
- Express.js upgrade guides

The Architect agent will automatically query these when it detects a matching language and framework in the submitted code.

---

## Supported Languages

| Language | Framework Detection | Test Runner |
|---|---|---|
| Python | Django, Flask, FastAPI | pytest |
| JavaScript | Express, React | Jest |
| TypeScript | Express, React | Jest + ts-jest |
| Java | Spring | JUnit |

---

## How The Pipeline Works

### 1. Profiler
Sends the code to Groq and asks it to identify the language, framework and version. Returns structured JSON like `{"language": "python", "framework": "django", "version": "1.11"}`.

### 2. Logic Anchor
Generates comprehensive unit tests for the **original** code. These tests become the behavioral contract — the modernized code must pass them to prove functional parity.

### 3. Architect
Queries ChromaDB for migration documentation matching the detected language and framework. Combines retrieved docs with the original code to produce a step-by-step transformation plan.

### 4. Engineer
Follows the transformation plan to rewrite the code in modern standards. Strict prompt rules ensure function names, signatures and behavior are preserved exactly.

### 5. Validator (Tester)
Spins up a fresh Docker container with the appropriate runtime (`python:3.12-slim`, `node:20-slim`, `openjdk:21-slim`). Writes both the modernized code and unit tests into the container and runs them. Returns logs and a pass/fail status.

### 6. Fixer
If validation fails, the Fixer reads the error logs and fixes syntax errors in the modernized code. Loops back to the Validator. Retries up to `MAX_RETRIES` times.

### Pass Threshold
The pipeline accepts a run as successful if **80% or more tests pass**. This prevents a single hallucinated test edge case from blocking an otherwise perfectly modernized codebase.

---

## Environment Variables Reference

| Variable | Description | Example |
|---|---|---|
| `GROQ_API_KEY` | Your Groq API key | `gsk_...` |
| `MODEL` | Groq model to use | `llama-3.3-70b-versatile` |
| `ADMIN_SECRET_KEY` | JWT signing secret (min 32 chars) | `super-secret-key-...` |
| `ADMIN_USERNAME` | Admin panel username | `admin` |
| `ADMIN_PASSWORD` | Admin panel password | `password123` |
| `EMBEDDING_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `CHROMA_HOST` | ChromaDB hostname | `chromadb` |
| `CHROMA_PORT` | ChromaDB port | `8000` |
| `CHROMA_COLLECTION_NAME` | ChromaDB collection name | `acmp_knowledge` |
| `BACKEND_HOST` | FastAPI bind host | `0.0.0.0` |
| `BACKEND_PORT` | FastAPI port | `8000` |
| `VITE_API_BASE_URL` | Frontend API base URL | `http://localhost:8000` |
| `VITE_WS_BASE_URL` | Frontend WebSocket base URL | `ws://localhost:8000` |
| `MAX_RETRIES` | Max Fixer → Validator loops | `3` |
| `DOCKER_TIMEOUT` | Container timeout in seconds | `60` |

---

## Troubleshooting

### Pipeline fails immediately
```bash
docker logs acmp-backend-1 -f
```
Check for missing environment variables or Groq API key issues.

### Tests not found in container
Ensure `docker-compose.yml` does **not** use a bind mount for sandboxes. The tester agent uses inline base64 file injection — no volume mount needed.

### ChromaDB connection error
ChromaDB takes a few seconds to start. If the backend starts before ChromaDB is ready:
```bash
docker compose restart backend
```

### Groq rate limit errors
The free Groq tier has rate limits. If you hit them:
- Wait 60 seconds and retry
- Or upgrade to a paid Groq plan

### Frontend shows pipeline failed despite good code
Check the test pass rate in backend logs. If 8+/10 tests pass but the pipeline still fails, verify the 80% threshold logic is in `edges.py`.

---

## Development

### Run backend only (without Docker)

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Run frontend only

```bash
cd frontend
npm install
npm run dev
```

### View API documentation

FastAPI auto-generates interactive docs:
- Swagger UI → http://localhost:8000/docs
- ReDoc → http://localhost:8000/redoc

### Check backend logs

```bash
docker logs acmp-backend-1 -f
```

### Rebuild after code changes

```bash
docker compose up --build
```

---

## Roadmap

- [ ] Support for more languages (Rust, Go, C++)
- [ ] Streaming diff updates as Engineer writes code
- [ ] Side-by-side test results viewer in frontend
- [ ] Download modernized code as zip
- [ ] GitHub integration — submit PR with modernized code automatically
- [ ] Batch processing — modernize entire repositories
- [ ] Custom transformation rules per project

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add my feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## Acknowledgements

- [Groq](https://groq.com) — blazing fast LLM inference
- [LangGraph](https://github.com/langchain-ai/langgraph) — agent orchestration
- [ChromaDB](https://www.trychroma.com) — local vector database
- [sentence-transformers](https://www.sbert.net) — free local embeddings


## Future Plans

- Make it compatible with AI Agents like cursor.
- Fine Tuning it for better results.
- Bringing more language and framework support.
- Making the system prompt more dynamic for the part that involves language and framework specific instructions to reduce the token costs.
- Implement Logger for better debugging capabilities.
- Improve the tester, make it more faster, compatible with all the language and frameworks ans lightweight.
- Make all the hardcoded values of the versions in the docker and tester dynamic 
mention them in a file and call from there.