"""
SQLAlchemy ORM models for Orbit.
Compatible with Python 3.14 & SQLAlchemy 2.0.
"""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text, Float
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ── Enums ──────────────────────────────────────────────────────────────────────

class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TicketCategory(str, enum.Enum):
    account = "account"
    billing = "billing"
    technical = "technical"
    cancellation = "cancellation"
    feature = "feature"
    security = "security"
    uncategorized = "uncategorized"


# ── Models ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="owner", lazy="selectin")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="owner", lazy="selectin")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.open)
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority), default=TicketPriority.medium)
    category: Mapped[TicketCategory] = mapped_column(Enum(TicketCategory), default=TicketCategory.uncategorized)
    ai_category_confidence = mapped_column(Float, nullable=True)
    resolution_notes = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="tickets")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    page_number = mapped_column(Integer, nullable=True)
    faiss_id = mapped_column(BigInteger, nullable=True, index=True)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
