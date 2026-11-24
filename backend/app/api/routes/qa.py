"""
Question-answering route using RAG + Gemini.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.db.database import get_db
from app.schemas.schemas import QuestionRequest, AnswerResponse
from app.services.rag_service import answer_question

router = APIRouter(prefix="/api/qa", tags=["qa"])


@router.post("/ask", response_model=AnswerResponse)
async def ask(
    payload: QuestionRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    from app.main import gemini_model
    return await answer_question(
        question=payload.question,
        db=db,
        top_k=payload.top_k,
        gemini_model=gemini_model,
    )
