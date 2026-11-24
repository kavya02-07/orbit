"""
Document upload, listing, and deletion routes.
Handles PDF upload, text extraction, chunking, embedding, and FAISS indexing.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import get_current_user_id
from app.db.database import get_db
from app.models.models import Document, DocumentChunk
from app.schemas.schemas import DocumentOut
from app.services.pdf_service import extract_pages
from app.services.embedding_service import embed_texts
from app.services.faiss_service import get_faiss_store
from app.utils.chunker import chunk_pages

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    settings = get_settings()

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = upload_dir / unique_name

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        filename=unique_name,
        original_filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        owner_id=user_id,
    )
    db.add(doc)
    db.flush()

    try:
        pages = extract_pages(file_path)
        doc.page_count = len(pages)

        chunks_data = chunk_pages(pages)
        doc.chunk_count = len(chunks_data)

        db_chunks: list[DocumentChunk] = []
        for cd in chunks_data:
            chunk = DocumentChunk(
                document_id=doc.id,
                chunk_index=cd["chunk_index"],
                text=cd["text"],
                page_number=cd["page_number"],
            )
            db.add(chunk)
            db_chunks.append(chunk)

        db.flush()

        texts = [c.text for c in db_chunks]
        embeddings = embed_texts(texts)

        store = get_faiss_store()
        faiss_start = store.total_vectors
        store.add_embeddings(embeddings, [c.id for c in db_chunks])

        for i, chunk in enumerate(db_chunks):
            chunk.faiss_id = faiss_start + i

        doc.is_indexed = True
        db.commit()
        db.refresh(doc)

    except Exception as e:
        db.rollback()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

    return DocumentOut.model_validate(doc)


@router.get("/", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Document).where(Document.owner_id == user_id).order_by(Document.created_at.desc())
    docs = list(db.execute(stmt).scalars().all())
    return [DocumentOut.model_validate(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Document).where(Document.id == doc_id, Document.owner_id == user_id)
    doc = db.execute(stmt).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    stmt = select(Document).where(Document.id == doc_id, Document.owner_id == user_id)
    doc = db.execute(stmt).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    store = get_faiss_store()
    faiss_ids = [c.faiss_id for c in doc.chunks if c.faiss_id is not None]
    if faiss_ids:
        store.remove_by_faiss_ids(faiss_ids)

    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    db.delete(doc)
    db.commit()
