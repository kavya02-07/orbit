"""
Ticket management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.database import get_db
from app.models.models import Ticket, TicketStatus, TicketCategory
from app.schemas.schemas import TicketCreate, TicketUpdate, TicketOut, TicketListResponse
from app.core.security import get_current_user_id
from app.services.classifier_service import classify_ticket_keywords

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    category, confidence = classify_ticket_keywords(payload.title, payload.description)

    ticket = Ticket(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        category=category,
        ai_category_confidence=confidence,
        owner_id=user_id,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return TicketOut.model_validate(ticket)


@router.get("/", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: TicketStatus | None = Query(None, alias="status"),
    category_filter: TicketCategory | None = Query(None, alias="category"),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Ticket).where(Ticket.owner_id == user_id)
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)
    if category_filter:
        stmt = stmt.where(Ticket.category == category_filter)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar_one()

    stmt = stmt.order_by(Ticket.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    tickets = list(db.execute(stmt).scalars().all())

    return TicketListResponse(
        items=[TicketOut.model_validate(t) for t in tickets],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Ticket).where(Ticket.id == ticket_id, Ticket.owner_id == user_id)
    ticket = db.execute(stmt).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return TicketOut.model_validate(ticket)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Ticket).where(Ticket.id == ticket_id, Ticket.owner_id == user_id)
    ticket = db.execute(stmt).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    db.commit()
    db.refresh(ticket)
    return TicketOut.model_validate(ticket)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Ticket).where(Ticket.id == ticket_id, Ticket.owner_id == user_id)
    ticket = db.execute(stmt).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(ticket)
    db.commit()
