"""
Orbit Backend — FastAPI Application Entry Point
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.db.database import init_db_engine, _engine
from app.models.models import Base
from app.api.routes import auth, tickets, documents, qa, analytics

gemini_model: Optional[object] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    global gemini_model
    settings = get_settings()

    # Ensure directories exist
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.faiss_index_path).mkdir(parents=True, exist_ok=True)

    # Init database
    engine = init_db_engine()
    Base.metadata.create_all(bind=engine)

    # Init Gemini if API key is set
    if settings.gemini_api_key:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            gemini_model = genai.GenerativeModel(settings.gemini_model)
            print(f"[Orbit] Gemini model '{settings.gemini_model}' initialised.")
        except Exception as e:
            print(f"[Orbit] WARNING: Gemini initialisation failed: {e}")
            gemini_model = None
    else:
        print("[Orbit] Note: GEMINI_API_KEY not configured. AI generation will provide retrieved context.")

    print("[Orbit] Backend ready.")
    yield

    if _engine:
        _engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Orbit — AI Support & Knowledge Assistant",
        description="Backend API for ticket management, PDF knowledge ingestion, and AI-powered Q&A.",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(tickets.router)
    app.include_router(documents.router)
    app.include_router(qa.router)
    app.include_router(analytics.router)

    @app.get("/", tags=["health"])
    def root():
        return {"service": "Orbit Backend", "status": "running", "version": "1.0.0"}

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
