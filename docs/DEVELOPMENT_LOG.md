# Orbit — Development Log & Architectural Decisions

## Phase 0: Project Initialization & Structure Setup
- **Workspace Verification:** Verified that `AGENTS.md` is present in root.
- **Directory Structure:** Created clean modular directory tree:
  - `frontend/` (Vite, React 18, TypeScript, Tailwind CSS)
  - `backend/` (FastAPI, SQLAlchemy, models, routes, services)
  - `docs/` (Architecture, status, logs, evaluation report)
- **Tooling & Baseline:** Initialized `package.json`, `tsconfig.json`, `tailwind.config.cjs`, `requirements.txt`, `.env.example`, `.gitignore`, and `README.md`.

---

## Phase 1: Backend Foundation & Database Layer
- **FastAPI Core Setup:** Configured CORS middleware, API routers with `/api` prefixes, centralized settings with Pydantic `BaseSettings`.
- **Database Architecture Decision (Python 3.14 Adaptation):**
  - *Context:* Initial async setup using `aiosqlite` hung indefinitely under Python 3.14 due to event loop deadlock issues on Windows.
  - *Decision:* Switched all database operations to synchronous SQLAlchemy sessions (`SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)`).
  - *Outcome:* Immediate resolution of blocking calls with rock-solid stability and zero overhead.
- **SQLAlchemy 2.0 Typing Bug Workaround:**
  - *Issue:* `Mapped[Optional[float]]` triggered `TypeError: descriptor '__getitem__' requires a 'typing.Union'` under Python 3.14.
  - *Fix:* Used bare `mapped_column(Float, nullable=True)` and `mapped_column(Text, nullable=True)`.

---

## Phase 2: Authentication & Authorization
- **Password Hashing (Bcrypt adaptation):**
  - *Issue:* `passlib` version 1.7.4 is incompatible with `bcrypt>=4.1.0` and Python 3.14 (raising `ValueError: password cannot be longer than 72 bytes`).
  - *Fix:* Replaced `passlib` with direct Python `bcrypt` library (`bcrypt.hashpw` and `bcrypt.checkpw`) with a safe 72-byte string slice boundary.
- **JWT Implementation:** Built token generation and validation using `PyJWT` with HS256 algorithm and configurable expiration.
- **Route Protection:** Implemented `get_current_user` FastAPI dependency utilizing OAuth2 password bearer flow.

---

## Phase 3: Ticket Management
- **Models & Enums:** Defined `Ticket` model with priority levels (`low`, `medium`, `high`, `urgent`) and status workflows (`open`, `in_progress`, `resolved`, `closed`).
- **CRUD Operations:** Implemented list, create, retrieve, and update endpoints with user-specific ownership isolation.
- **Integrated Hook:** Attached auto-classification hook on ticket creation.

---

## Phase 4: PDF Ingestion & Text Processing
- **PDF Extraction:** Integrated PyMuPDF (`fitz`) for robust extraction across multi-page PDF documents.
- **Text Normalization:** Implemented `clean_text` in `chunker.py` to remove non-printable characters, normalize whitespace, and preserve paragraph structure.
- **Sliding-Window Chunking:** Implemented `chunk_pages` with configurable chunk size (200 words) and overlap (40 words), preserving document page numbers and chunk sequence indices.

---

## Phase 5: Embeddings & Vector Search (FAISS)
- **Embedding Model:** Selected `sentence-transformers/all-MiniLM-L6-v2` producing 384-dimensional dense vectors.
- **FAISS Configuration:** Selected `IndexFlatIP` combined with L2 vector normalization to calculate exact cosine similarity.
- **Offline & Sandbox Compatibility:**
  - Implemented lazy loading of SentenceTransformer with `local_files_only=True` fallback and `HF_HUB_OFFLINE=1` support.
  - Pre-cached model weights into `~/.cache/huggingface/hub/`.
- **Atomic Persistence:** Implemented synchronized saving of `index.faiss` and `chunks.pkl` metadata.

---

## Phase 6 & 7: Gemini RAG Pipeline & Citation Validation
- **RAG Architecture:**
  - Encodes user inquiry into dense query vector.
  - Searches FAISS vector index for top $K$ relevant chunks.
  - Formats grounded prompt incorporating retrieved document text with explicit citations.
  - Dispatches prompt to Google Gemini (`gemini-1.5-flash`).
- **Graceful Fallback Design:**
  - When `GEMINI_API_KEY` is not provided, returns retrieved contexts along with an informative notice, ensuring zero application crashes.
- **Citation Validation:** Each retrieved source includes `document_id`, `document_name`, `page_number`, `chunk_index`, and `similarity_score`.

---

## Phase 8: Ticket Classification Engine
- **Vocabulary-Based Engine:** Defined domain-specific keyword dictionaries for `Account`, `Billing`, `Technical`, `Cancellation`, `Feature`, and `Security`.
- **Confidence Scoring:** Calculates winning category weight against total matches.
- **LLM Extension:** Supports secondary classification via Gemini zero-shot prompt when rule confidence is below threshold.

---

## Phase 9: React Frontend Implementation
- **Component Design:** Built a modular UI using Tailwind CSS with a cohesive dark-slate palette (`#0B0F17` background, `#111827` cards, `#4F46E5` primary accents).
- **Views:**
  - `LoginPage` & `RegisterPage` with form validation.
  - `DashboardPage` featuring key operational metrics and recent activity.
  - `TicketsPage` & `NewTicketPage` with real-time classification preview.
  - `TicketDetailPage` with status workflow progression and resolution notes.
  - `DocumentsPage` with drag-and-drop PDF upload and chunk viewer.
  - `AskPage` with interactive question answering, source reference badges, and score indicators.
  - `AnalyticsPage` with interactive Recharts visualizations (bar charts, pie charts) and benchmark metrics.
- **Production Build:** Verified full TypeScript and Vite build compilation without warnings or errors.

---

## Phase 10: Evaluation & Benchmark Testing
- **Test Dataset:** Created `tests/eval_dataset.json` with 25 curated domain queries and reference PDFs (`Billing_Policy_2026.pdf`, `Technical_Architecture_Guide.pdf`, `Security_and_Compliance_Charter.pdf`).
- **Automated Harness:** Created `tests/run_evaluation.py` measuring:
  - **Retrieval Recall@5:** **100.0%** (25/25)
  - **Citation Accuracy:** **100.0%** (125/125 citations valid)
  - **Context Grounding:** **72.0%** (18/25)
  - **Classification Accuracy:** **76.0%** (19/25)
  - **Retrieval Latency (Mean):** **39.69 ms**
- **Automated Output:** Emitted results directly to `docs/EVALUATION_REPORT.md`.

---

## Phase 11: Final Validation & Delivery
- **Unit & Integration Tests:** Executed pytest suite: `14 passed in 13.14s`.
- **Frontend Build:** Verified production assets:
  - `dist/index.html` (0.48 kB)
  - `dist/assets/index.css` (18.47 kB)
  - `dist/assets/index.js` (696.88 kB)
- **Documentation:** Completed `PROJECT_STATUS.md`, `ARCHITECTURE.md`, `DEVELOPMENT_LOG.md`, and `EVALUATION_REPORT.md`.


---

## Final Verification Audit & Activity Log Reconciliation (November 15, 2026)

### Audit Scope & Objectives
- Investigate earlier activity logs showing `verify_e2e.py` exiting with code 1.
- Run unit test suite, E2E suite, and evaluation harness independently and record actual exit codes and outputs.
- Clarify distinction between code inspection, automated testing, and live network server testing.
- Formally document that live uvicorn server port binding and live Gemini API testing require external execution (user terminal and API key configuration, respectively).

### Key Findings & Reconciliation
1. **`verify_e2e.py` Discrepancy**: The multiple code 1 runs during initial test authoring were due to test-script parameter mismatches (`classify_ticket_keywords`, `update_ticket`, PyMuPDF tuple access, chunking parameter names, FAISS store methods, and Pydantic object attribute access). Once corrected, `verify_e2e.py` exited with code 0 across all 10 checks.
2. **Unit Tests (`test_api.py`)**: 14/14 tests PASSED (exit code 0 in 14.15s).
3. **E2E Tests (`verify_e2e.py`)**: 10/10 checks PASSED (exit code 0).
4. **Evaluation Benchmark (`run_evaluation.py`)**: 25 evaluation queries executed with real measured metrics: Recall@5 = 100%, Citation Accuracy = 100%, Context Grounding = 72.0%, Classification Accuracy = 76.0%, Mean Latency = 31.29 ms.
5. **Live Server Status**: Uvicorn daemon socket binding is unverified inside the automated sandbox; full live testing must be performed via user terminal (`uvicorn app.main:app --port 8000`).
6. **Gemini Integration**: Verified in Local Fallback Mode (retrieved context chunks returned with explicit notice). Live LLM generation is unverified pending entry of a valid `GEMINI_API_KEY`.
