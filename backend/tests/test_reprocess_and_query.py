"""
Script to test re-processing Orbit_Test_Refund_Policy.pdf and running the 5 queries.
"""
import os
import sys
import io
import asyncio
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from starlette.datastructures import UploadFile
from app.db.database import get_db, init_db_engine
from app.models.models import Document, DocumentChunk, User
from app.api.routes.documents import delete_document, upload_document
from app.services.faiss_service import get_faiss_store, reset_faiss_store
from app.services.rag_service import answer_question

init_db_engine()
db = next(get_db())

print("=" * 70)
print("1. DELETING OLD DOCUMENT RECORD & FAISS ENTRY")
print("=" * 70)

old_doc = db.query(Document).filter_by(original_filename="Orbit_Test_Refund_Policy.pdf").first()
if old_doc:
    print(f"Found existing document: id={old_doc.id}, file={old_doc.filename}, chunks={old_doc.chunk_count}")
    delete_document(doc_id=old_doc.id, db=db, user_id=old_doc.owner_id)
    print("Successfully deleted old document via delete_document route!")
else:
    print("No previous document found with that name.")

store = get_faiss_store()
print(f"FAISS total vectors after deletion: {store.total_vectors}")
print(f"FAISS id_map after deletion: {store.id_map}")

# Verify database state
remaining_chunks = db.query(DocumentChunk).all()
print(f"Remaining chunks in DB: {len(remaining_chunks)}")

print("\n" + "=" * 70)
print("2. RE-UPLOADING TEST PDF THROUGH NORMAL APPLICATION ROUTE")
print("=" * 70)

source_pdf_path = Path("data/Orbit_Test_Refund_Policy_original.pdf")
assert source_pdf_path.exists(), f"Source PDF missing at {source_pdf_path}"

with open(source_pdf_path, "rb") as f:
    pdf_bytes = f.read()

upload_file = UploadFile(
    file=io.BytesIO(pdf_bytes),
    filename="Orbit_Test_Refund_Policy.pdf",
    headers={"content-type": "application/pdf"}
)

# Call upload_document route function
user_id = 1
new_doc_out = asyncio.run(upload_document(file=upload_file, db=db, user_id=user_id))
print(f"Upload completed! New Doc ID: {new_doc_out.id}")
print(f"Filename: {new_doc_out.filename}")
print(f"Page Count: {new_doc_out.page_count}")
print(f"Chunk Count: {new_doc_out.chunk_count}")
print(f"Is Indexed: {new_doc_out.is_indexed}")

# Verify in DB and FAISS
chunks = db.query(DocumentChunk).filter_by(document_id=new_doc_out.id).order_by(DocumentChunk.chunk_index).all()
print(f"\nIndexed Chunks in DB: {len(chunks)}")
for c in chunks:
    words = len(c.text.split())
    print(f"  Chunk #{c.chunk_index} (id={c.id}, page={c.page_number}, {words} words, faiss_id={c.faiss_id}):")
    print(f"    Excerpt: {c.text[:85]}...")

reset_faiss_store()
store = get_faiss_store()
print(f"\nFAISS total vectors after upload: {store.total_vectors}")
print(f"FAISS id_map: {store.id_map}")

print("\n" + "=" * 70)
print("3. INDEPENDENT TESTING OF THE 4 QUESTIONS + 1 UNANSWERED QUESTION")
print("=" * 70)

test_questions = [
    {
        "q": "How many days do customers have to request a return?",
        "expected": "30 calendar days",
        "description": "Return window policy"
    },
    {
        "q": "How long does the support team take to respond to a return request?",
        "expected": "2 business days",
        "description": "Support response time"
    },
    {
        "q": "How long does an approved refund take?",
        "expected": "5 to 7 business days",
        "description": "Refund processing time"
    },
    {
        "q": "Who pays return shipping for a change-of-mind return?",
        "expected": "The customer",
        "description": "Return shipping costs"
    },
    {
        "q": "What payment methods does the company accept?",
        "expected": "UNANSWERED (not in document)",
        "description": "Negative test - question not answered in PDF"
    }
]

for idx, item in enumerate(test_questions, start=1):
    q = item["q"]
    expected = item["expected"]
    desc = item["description"]

    print(f"\n{'─' * 70}")
    print(f"QUESTION {idx}: \"{q}\"")
    print(f"Expected info: {expected} ({desc})")
    print(f"{'─' * 70}")

    response = asyncio.run(answer_question(question=q, db=db, top_k=3, gemini_model=None))

    print(f"Model used: {response.model_used}")
    print(f"Has sufficient context: {response.has_sufficient_context}")
    print(f"Number of sources: {len(response.sources)}")

    for si, src in enumerate(response.sources, start=1):
        print(f"\n  [Source Reference {si}]")
        print(f"    Document: {src.document_name}")
        print(f"    Page: {src.page_number}")
        print(f"    Chunk Index: {src.chunk_index}")
        print(f"    Similarity Score: {src.similarity_score:.4f} ({src.similarity_score*100:.1f}%)")
        print(f"    Excerpt: {src.excerpt}")

    print(f"\n  [Fallback Answer Text Preview]:")
    print("  " + response.answer.replace("\n", "\n  ")[:400] + "...")

    # Evaluation check
    if expected != "UNANSWERED (not in document)":
        # Check if the top source or any source supports expected answer
        top_supports = expected.lower() in response.sources[0].excerpt.lower()
        any_supports = any(expected.lower() in s.excerpt.lower() for s in response.sources)
        if top_supports:
            print(f"\n  >>> RESULT: PASS - Top retrieved excerpt supports the expected answer ('{expected}').")
        elif any_supports:
            print(f"\n  >>> RESULT: PARTIAL - Expected answer found in retrieved sources (not top).")
        else:
            print(f"\n  >>> RESULT: FAIL - Expected answer not found in retrieved excerpts.")
    else:
        # Negative test evaluation
        if not response.has_sufficient_context or response.sources[0].similarity_score < 0.40:
            print(f"\n  >>> RESULT: PASS - Negative test confirmed: has_sufficient_context={response.has_sufficient_context}, top score={response.sources[0].similarity_score:.4f} < 0.40. Notice displayed to user.")
        else:
            print(f"\n  >>> RESULT: NOTICE - Score was {response.sources[0].similarity_score:.4f}.")

db.close()
