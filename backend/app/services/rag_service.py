"""
Gemini-powered RAG service.
Retrieves relevant chunks via FAISS, builds a grounded prompt,
generates an answer, and returns structured citations.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import get_settings
from app.models.models import DocumentChunk, Document
from app.schemas.schemas import AnswerResponse, SourceReference
from app.services.embedding_service import embed_query
from app.services.faiss_service import get_faiss_store


SYSTEM_PROMPT = """You are Orbit, an AI knowledge assistant.
Answer the user's question using ONLY the provided document excerpts.
If the excerpts do not contain sufficient information to answer, say so explicitly.
Do not invent facts, policies, or citations not found in the provided context.
Be concise, accurate, and cite the document names when referencing specific information."""


SIMILARITY_THRESHOLD = 0.40


async def answer_question(
    question: str,
    db: Session,
    top_k: int = 5,
    gemini_model=None,
    min_similarity: float = SIMILARITY_THRESHOLD,
) -> AnswerResponse:
    settings = get_settings()

    query_vec = embed_query(question)
    store = get_faiss_store()
    hits = store.search(query_vec, top_k=top_k)

    if not hits:
        return AnswerResponse(
            question=question,
            answer="No relevant documents were found in the knowledge base. Please upload relevant PDF documents first.",
            sources=[],
            model_used=settings.gemini_model,
            has_sufficient_context=False,
        )

    # Filter out low-relevance chunks below the minimum similarity threshold
    filtered_hits = [h for h in hits if h["score"] >= min_similarity]

    if not filtered_hits:
        return AnswerResponse(
            question=question,
            answer="The uploaded documentation does not contain sufficient information to answer your question.",
            sources=[],
            model_used=settings.gemini_model,
            has_sufficient_context=False,
        )

    chunk_ids = [h["chunk_db_id"] for h in filtered_hits]
    score_map = {h["chunk_db_id"]: h["score"] for h in filtered_hits}

    stmt = select(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids))
    chunks: list[DocumentChunk] = list(db.execute(stmt).scalars().all())

    doc_ids = list({c.document_id for c in chunks})
    doc_stmt = select(Document).where(Document.id.in_(doc_ids))
    docs = {d.id: d for d in db.execute(doc_stmt).scalars().all()}

    chunks_sorted = sorted(chunks, key=lambda c: score_map.get(c.id, 0.0), reverse=True)

    context_parts = []
    sources: list[SourceReference] = []

    for chunk in chunks_sorted:
        doc = docs.get(chunk.document_id)
        doc_name = doc.original_filename if doc else f"Document {chunk.document_id}"
        excerpt = chunk.text[:500]

        context_parts.append(
            f"[Source: {doc_name}, Page {chunk.page_number or '?'}]\n{excerpt}"
        )
        sources.append(SourceReference(
            document_id=chunk.document_id,
            document_name=doc_name,
            chunk_index=chunk.chunk_index,
            page_number=chunk.page_number,
            excerpt=excerpt,
            similarity_score=round(score_map.get(chunk.id, 0.0), 4),
        ))

    context_text = "\n\n---\n\n".join(context_parts)
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"### Retrieved Document Excerpts\n\n{context_text}\n\n"
        f"### User Question\n{question}\n\n"
        f"### Answer"
    )

    if gemini_model is None:
        header = (
            "[Gemini API key not configured] "
            "Retrieved context is available but AI generation is disabled. "
            "Please set GEMINI_API_KEY in your .env file."
        )

        # In Gemini-disabled mode, display only the top 2–3 chunks that passed the threshold
        displayed_sources = sources[:3]
        excerpt_blocks = []
        for i, src in enumerate(displayed_sources, start=1):
            page_info = f"Page {src.page_number}" if src.page_number is not None else "Page ?"
            score_pct = f"{src.similarity_score * 100:.1f}%"
            excerpt_blocks.append(
                f"[Source {i}: {src.document_name} — {page_info} (Match: {score_pct})]\n{src.excerpt}"
            )

        all_excerpts = "\n\n".join(excerpt_blocks)
        count_label = f"Top relevant excerpt{'s' if len(displayed_sources) != 1 else ''}"
        answer_text = f"{header}\n\n{count_label}:\n\n{all_excerpts}"
        has_context = True
        sources = displayed_sources
    else:
        try:
            response = await gemini_model.generate_content_async(prompt)
            answer_text = response.text.strip()
            no_info_phrases = [
                "do not contain", "not enough information", "cannot answer",
                "no information", "insufficient", "not found in",
            ]
            has_context = not any(p in answer_text.lower() for p in no_info_phrases)
        except Exception as e:
            answer_text = f"AI generation failed: {str(e)}"
            has_context = False

    return AnswerResponse(
        question=question,
        answer=answer_text,
        sources=sources,
        model_used=settings.gemini_model,
        has_sufficient_context=has_context,
    )
