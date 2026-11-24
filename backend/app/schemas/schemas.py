"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.models import TicketCategory, TicketPriority, TicketStatus


# ── Auth ───────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Tickets ────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    description: str = Field(..., min_length=10)
    priority: TicketPriority = TicketPriority.medium


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    description: Optional[str] = Field(None, min_length=10)
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    resolution_notes: Optional[str] = None


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    category: TicketCategory
    ai_category_confidence: Optional[float]
    resolution_notes: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketListResponse(BaseModel):
    items: list[TicketOut]
    total: int
    page: int
    page_size: int


# ── Documents ──────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    page_count: int
    chunk_count: int
    is_indexed: bool
    owner_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Q&A ────────────────────────────────────────────────────────────────────────

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class SourceReference(BaseModel):
    document_id: int
    document_name: str
    chunk_index: int
    page_number: Optional[int]
    excerpt: str
    similarity_score: float


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceReference]
    model_used: str
    has_sufficient_context: bool


# ── Analytics ─────────────────────────────────────────────────────────────────

class TicketStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_category: dict[str, int]
    by_priority: dict[str, int]


class SystemStats(BaseModel):
    total_users: int
    total_tickets: int
    total_documents: int
    total_chunks: int
    tickets: TicketStats
