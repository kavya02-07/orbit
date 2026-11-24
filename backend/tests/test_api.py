"""
Comprehensive test suite for Orbit Backend.
Tests all layers: Auth, Tickets, Documents, Retrieval, Classification, and Analytics.
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test_orbit.db"
os.environ["SECRET_KEY"] = "test-secret-key-orbit-ai-assistant-12345"
os.environ["GEMINI_API_KEY"] = ""
os.environ["UPLOAD_DIR"] = "./data/test_uploads"
os.environ["FAISS_INDEX_PATH"] = "./data/test_faiss"

from app.models.models import Base, User, Ticket, Document, DocumentChunk, TicketStatus, TicketPriority, TicketCategory
from app.schemas.schemas import (
    UserRegister, TicketCreate, TicketUpdate, QuestionRequest
)
from app.api.routes.auth import register, login
from app.api.routes.tickets import create_ticket, get_ticket, list_tickets, update_ticket, delete_ticket
from app.api.routes.analytics import get_stats
from app.core.security import create_access_token, decode_token
from app.utils.password import hash_password, verify_password
from app.utils.chunker import chunk_text, clean_text, chunk_pages
from app.services.classifier_service import classify_ticket_keywords
from app.services.faiss_service import FaissStore


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///./test_orbit.db", connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db(engine):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ── Health & Root Tests ─────────────────────────────────────────────────────────

def test_health_and_root():
    from app.main import app
    # Verify app routes are registered
    routes = [route.path for route in app.routes]
    assert "/health" in routes
    assert "/" in routes
    assert "/api/auth/register" in routes
    assert "/api/tickets/" in routes
    assert "/api/documents/upload" in routes
    assert "/api/qa/ask" in routes
    assert "/api/analytics/stats" in routes


# ── Auth & Password Tests ──────────────────────────────────────────────────────

def test_password_hashing():
    password = "SecurePassword123!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)


def test_jwt_tokens():
    token = create_access_token({"sub": "42"})
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert "exp" in payload


def test_user_registration(db):
    payload = UserRegister(email="alice@orbit.dev", full_name="Alice Smith", password="Password123!")
    res = register(payload, db=db)
    assert res.access_token is not None
    assert res.user.email == "alice@orbit.dev"
    assert res.user.full_name == "Alice Smith"


def test_duplicate_registration(db):
    payload = UserRegister(email="alice@orbit.dev", full_name="Alice Smith", password="Password123!")
    with pytest.raises(Exception):
        register(payload, db=db)


# ── Ticket Management Tests ────────────────────────────────────────────────────

def test_create_ticket_with_auto_classification(db):
    user = db.query(User).filter_by(email="alice@orbit.dev").first()
    ticket_in = TicketCreate(
        title="Double billed on monthly subscription invoice",
        description="I noticed two charges of $49 on my credit card statement for this month. Please issue a refund.",
        priority=TicketPriority.high,
    )
    ticket = create_ticket(ticket_in, db=db, user_id=user.id)
    assert ticket.id is not None
    assert ticket.title == "Double billed on monthly subscription invoice"
    assert ticket.priority == TicketPriority.high
    assert ticket.category == TicketCategory.billing
    assert ticket.ai_category_confidence > 0.0


def test_list_and_filter_tickets(db):
    user = db.query(User).filter_by(email="alice@orbit.dev").first()
    # Create another ticket
    create_ticket(
        TicketCreate(
            title="Application crashes on startup with error",
            description="Every time I open the app, it crashes with a memory fault error exception.",
            priority=TicketPriority.critical,
        ),
        db=db,
        user_id=user.id,
    )
    res = list_tickets(page=1, page_size=10, status_filter=None, category_filter=None, db=db, user_id=user.id)
    assert res.total >= 2
    assert len(res.items) >= 2


def test_get_and_update_ticket(db):
    user = db.query(User).filter_by(email="alice@orbit.dev").first()
    tickets_res = list_tickets(page=1, page_size=1, status_filter=None, category_filter=None, db=db, user_id=user.id)
    ticket_id = tickets_res.items[0].id

    # Get
    t = get_ticket(ticket_id=ticket_id, db=db, user_id=user.id)
    assert t.id == ticket_id

    # Update
    updated = update_ticket(
        ticket_id=ticket_id,
        payload=TicketUpdate(status=TicketStatus.resolved, resolution_notes="Refund processed successfully."),
        db=db,
        user_id=user.id,
    )
    assert updated.status == TicketStatus.resolved
    assert updated.resolution_notes == "Refund processed successfully."


# ── Ticket Classification Tests ───────────────────────────────────────────────

def test_ticket_classification_all_categories():
    test_cases = [
        ("Unable to login or reset account password", "My user credentials fail and account is locked.", TicketCategory.account),
        ("Disputed charge on billing invoice", "Please refund the subscription fee payment on my credit card.", TicketCategory.billing),
        ("System crash and timeout error bug", "Getting unexpected broken crash glitch on installation.", TicketCategory.technical),
        ("Please cancel and close my account subscription", "I want to terminate service and unsubscribe immediately.", TicketCategory.cancellation),
        ("Feature request: add dark mode theme", "We would like to request support for export to csv format.", TicketCategory.feature),
        ("Suspicious phishing attempt and security breach", "Detected unauthorized login and 2fa security malware attempt.", TicketCategory.security),
    ]
    for title, desc, expected_cat in test_cases:
        cat, conf = classify_ticket_keywords(title, desc)
        assert cat == expected_cat, f"Expected {expected_cat} for '{title}', got {cat}"
        assert conf > 0.0


# ── Text Chunking & Extraction Tests ──────────────────────────────────────────

def test_clean_text():
    raw = "  Hello \t\t world!\r\n\r\n\n\nNew   line.  "
    cleaned = clean_text(raw)
    assert cleaned == "Hello world!\n\nNew line."


def test_chunk_text_overlap():
    words = [f"word{i}" for i in range(100)]
    text = " ".join(words)
    chunks = list(chunk_text(text, chunk_size=30, chunk_overlap=5))
    assert len(chunks) == 4
    # Check overlap: last 5 words of chunk 0 should match first 5 words of chunk 1
    c0_words = chunks[0].split()
    c1_words = chunks[1].split()
    assert c0_words[-5:] == c1_words[:5]


def test_chunk_pages():
    pages = [
        (1, "This is page one content about billing policy and refund terms."),
        (2, "This is page two content about technical installation and system requirements."),
    ]
    chunks = chunk_pages(pages, chunk_size=50, chunk_overlap=10)
    assert len(chunks) == 2
    assert chunks[0]["page_number"] == 1
    assert chunks[1]["page_number"] == 2
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


# ── FAISS Vector Store Tests ──────────────────────────────────────────────────

def test_faiss_vector_store(tmp_path):
    import numpy as np
    store = FaissStore(index_dir=str(tmp_path / "faiss"))
    assert store.total_vectors == 0

    # Create synthetic normalized embeddings (2 vectors, 384 dim)
    vecs = np.random.randn(2, 384).astype(np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)

    store.add_embeddings(vecs, chunk_db_ids=[101, 102])
    assert store.total_vectors == 2

    # Query with exact first vector
    results = store.search(vecs[0:1], top_k=2)
    assert len(results) == 2
    assert results[0]["chunk_db_id"] == 101
    assert results[0]["score"] > 0.99  # Cosine similarity to itself is ~1.0

    # Persistence check
    reloaded_store = FaissStore(index_dir=str(tmp_path / "faiss"))
    assert reloaded_store.total_vectors == 2


# ── Analytics Tests ───────────────────────────────────────────────────────────

def test_analytics_stats(db):
    user = db.query(User).filter_by(email="alice@orbit.dev").first()
    stats = get_stats(db=db, user_id=user.id)
    assert stats.total_users >= 1
    assert stats.total_tickets >= 2
    assert "open" in stats.tickets.by_status or "resolved" in stats.tickets.by_status
    assert "billing" in stats.tickets.by_category
