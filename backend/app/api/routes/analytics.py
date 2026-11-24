"""
Analytics route — ticket stats, system overview.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.security import get_current_user_id
from app.db.database import get_db
from app.models.models import Ticket, Document, User, DocumentChunk, TicketStatus, TicketCategory, TicketPriority
from app.schemas.schemas import SystemStats, TicketStats
from app.services.faiss_service import get_faiss_store

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/stats", response_model=SystemStats)
def get_stats(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    total_users = db.execute(select(func.count(User.id))).scalar_one()
    total_docs = db.execute(select(func.count(Document.id)).where(Document.owner_id == user_id)).scalar_one()
    total_chunks = db.execute(select(func.count(DocumentChunk.id))).scalar_one()
    total_tickets = db.execute(select(func.count(Ticket.id)).where(Ticket.owner_id == user_id)).scalar_one()

    # By status
    by_status: dict[str, int] = {s.value: 0 for s in TicketStatus}
    rows = db.execute(
        select(Ticket.status, func.count(Ticket.id))
        .where(Ticket.owner_id == user_id)
        .group_by(Ticket.status)
    ).all()
    for status_val, count in rows:
        val = status_val.value if hasattr(status_val, "value") else str(status_val)
        by_status[val] = count

    # By category
    by_category: dict[str, int] = {c.value: 0 for c in TicketCategory}
    rows = db.execute(
        select(Ticket.category, func.count(Ticket.id))
        .where(Ticket.owner_id == user_id)
        .group_by(Ticket.category)
    ).all()
    for cat_val, count in rows:
        val = cat_val.value if hasattr(cat_val, "value") else str(cat_val)
        by_category[val] = count

    # By priority
    by_priority: dict[str, int] = {p.value: 0 for p in TicketPriority}
    rows = db.execute(
        select(Ticket.priority, func.count(Ticket.id))
        .where(Ticket.owner_id == user_id)
        .group_by(Ticket.priority)
    ).all()
    for prio_val, count in rows:
        val = prio_val.value if hasattr(prio_val, "value") else str(prio_val)
        by_priority[val] = count

    return SystemStats(
        total_users=total_users,
        total_tickets=total_tickets,
        total_documents=total_docs,
        total_chunks=total_chunks,
        tickets=TicketStats(
            total=total_tickets,
            by_status=by_status,
            by_category=by_category,
            by_priority=by_priority,
        ),
    )


@router.get("/faiss-info")
def faiss_info(user_id: int = Depends(get_current_user_id)):
    store = get_faiss_store()
    return {
        "total_indexed_vectors": store.total_vectors,
        "index_dimension": store.DIMENSION,
    }
