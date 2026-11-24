# Orbit — AI-Powered Intelligent Support & Knowledge Assistant

Orbit is a full-stack AI assistant that helps teams manage support tickets, search uploaded knowledge documents, and receive Gemini-powered answers with reliable source citations.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + TypeScript |
| Backend | Python 3.10+ + FastAPI |
| Database | SQLite + SQLAlchemy (async) |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Embeddings | Sentence Transformers `all-MiniLM-L6-v2` |
| Vector Search | FAISS |
| PDF Extraction | PyMuPDF |
| AI / LLM | Google Gemini (gemini-1.5-flash) |

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
cp .env.example .env
# Edit .env — set GEMINI_API_KEY and SECRET_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000  
API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

## Features

- **User Registration & Login** — JWT-secured accounts
- **Support Ticket Management** — Create, view, update, and filter tickets
- **Automatic Ticket Classification** — AI-categorised into Billing, Technical, Account, etc.
- **PDF Knowledge Base** — Upload PDF documents for AI-indexed retrieval
- **RAG Question Answering** — Gemini answers grounded in your documents
- **Source Citations** — Every answer links to the exact document chunk used
- **Analytics Dashboard** — Ticket trends, category distribution, retrieval metrics
- **Evaluation Suite** — Recall@5, citation accuracy, classification accuracy

## Project Structure

```
orbit/
├── AGENTS.md           # Project instructions
├── README.md
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── api/routes/ # FastAPI route handlers
│   │   ├── core/       # Config, security, JWT
│   │   ├── db/         # SQLAlchemy engine & session
│   │   ├── models/     # ORM table models
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # PDF, FAISS, Gemini, classifier
│   │   └── utils/      # Chunker, password hash
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── components/ # Shared UI components
│       ├── pages/      # Route-level page components
│       ├── services/   # API client
│       ├── hooks/      # Custom React hooks
│       └── assets/
└── docs/
    ├── ARCHITECTURE.md
    ├── PROJECT_STATUS.md
    └── DEVELOPMENT_LOG.md
```

## Environment Variables

See `backend/.env.example` for the full list. Required:

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `SECRET_KEY` | JWT signing secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |

## Running Tests

```bash
cd backend
venv\Scripts\activate
pytest tests/ -v
```

## Docs

- [Architecture](docs/ARCHITECTURE.md)
- [Project Status](docs/PROJECT_STATUS.md)
- [Development Log](docs/DEVELOPMENT_LOG.md)
