"""
Diagnostic script: Investigate whether different questions retrieve different chunks.
Tests the full pipeline: PDF extraction → chunking → embedding → FAISS search → RAG answer.
Does NOT use Gemini. Does NOT modify any existing code.
"""
import os
import sys
import shutil
from pathlib import Path

# Setup clean isolated test environment
TEST_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(TEST_DIR))

DIAG_DB = "./diag_test.db"
DIAG_FAISS = "./data/diag_faiss"
DIAG_UPLOADS = "./data/diag_uploads"

os.environ["DATABASE_URL"] = f"sqlite:///{DIAG_DB}"
os.environ["SECRET_KEY"] = "diag-test-secret-key-32chars"
os.environ["GEMINI_API_KEY"] = ""
os.environ["UPLOAD_DIR"] = DIAG_UPLOADS
os.environ["FAISS_INDEX_PATH"] = DIAG_FAISS
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Clean up previous diagnostic files
for p in [DIAG_DB, DIAG_FAISS, DIAG_UPLOADS]:
    path = Path(p)
    if path.is_dir():
        shutil.rmtree(path)
    elif path.is_file():
        os.remove(path)

Path(DIAG_UPLOADS).mkdir(parents=True, exist_ok=True)
Path(DIAG_FAISS).mkdir(parents=True, exist_ok=True)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.models import Base, User, Document, DocumentChunk
from app.services.pdf_service import extract_pages
from app.utils.chunker import chunk_pages
from app.services.embedding_service import embed_texts, embed_query
from app.services.faiss_service import FaissStore
from app.services.rag_service import answer_question

# Initialize clean database
engine = create_engine(f"sqlite:///{DIAG_DB}", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
db = Session()

# Create user
user = User(email="diag@orbit.dev", full_name="Diagnostics", hashed_password="x")
db.add(user)
db.commit()
db.refresh(user)

print("=" * 70)
print("ORBIT RETRIEVAL BUG DIAGNOSTIC")
print("=" * 70)

# ── Step 1: Create the test PDF ──────────────────────────────────────────────
# We need a PDF with distinctly different sections to test retrieval discrimination
test_pdf_path = Path("tests/sample_docs/Orbit_Test_Refund_Policy.pdf")

# If the PDF doesn't exist, create it using reportlab or fitz
if not test_pdf_path.exists():
    print(f"[INFO] Creating test PDF at {test_pdf_path}...")
    import fitz  # PyMuPDF
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text(
        (72, 72),
        """ORBIT TEST REFUND POLICY

Section 1: Return Window
Customers have 30 calendar days from the date of purchase to request a return 
for any product. Items must be unused and in their original packaging. After 
the 30-day window has passed, returns will not be accepted under any 
circumstances. The return window begins on the date shown on the purchase 
receipt or delivery confirmation email.

Section 2: Response Time
Our dedicated support team will acknowledge and respond to all return 
requests within 2 business days of submission. Business days are defined 
as Monday through Friday, excluding public holidays. If you do not receive 
a response within 2 business days, please contact our escalation department.""",
        fontsize=11,
        fontname="helv",
    )

    page2 = doc.new_page()
    page2.insert_text(
        (72, 72),
        """Section 3: Refund Processing Time
Once a return has been approved by our team, the refund will be processed 
and credited to the original payment method within 5 to 7 business days. 
International transactions may take an additional 3 to 5 business days 
depending on the customer's bank processing times.

Section 4: Return Shipping Costs
For returns due to a change-of-mind, the customer is responsible for all 
return shipping costs. Orbit does not provide prepaid return shipping labels 
for change-of-mind returns. The customer must arrange and pay for shipping 
at their own expense. For returns due to defective products or shipping 
errors, Orbit will provide a prepaid return shipping label at no cost to 
the customer.

Section 5: Non-Returnable Items
Gift cards, downloadable software, and personalized items cannot be returned. 
Perishable goods must be reported within 48 hours of delivery. Clearance 
items marked as final sale are not eligible for returns or exchanges.""",
        fontsize=11,
        fontname="helv",
    )

    doc.save(str(test_pdf_path))
    doc.close()
    print(f"[OK] Created {test_pdf_path}")
else:
    print(f"[OK] Test PDF exists: {test_pdf_path}")

# ── Step 2: Extract and chunk ────────────────────────────────────────────────
print("\n--- Step 2: PDF Extraction & Chunking ---")
pages = extract_pages(str(test_pdf_path))
print(f"Extracted {len(pages)} pages")
for i, (pnum, text) in enumerate(pages):
    print(f"  Page {pnum}: {len(text)} chars, preview: {text[:80].strip()!r}...")

# Use smaller chunk size for better discrimination
chunks = chunk_pages(pages, chunk_size=200, chunk_overlap=40)
print(f"\nGenerated {len(chunks)} chunks:")
for c in chunks:
    preview = c['text'][:100].replace('\n', ' ').strip()
    print(f"  Chunk {c['chunk_index']} (page {c['page_number']}): {preview!r}...")

# ── Step 3: Embed & Index ────────────────────────────────────────────────────
print("\n--- Step 3: Embedding & FAISS Indexing ---")
doc_record = Document(
    filename="Orbit_Test_Refund_Policy.pdf",
    original_filename="Orbit_Test_Refund_Policy.pdf",
    file_path=str(test_pdf_path),
    file_size=test_pdf_path.stat().st_size,
    page_count=len(pages),
    chunk_count=len(chunks),
    is_indexed=True,
    owner_id=user.id,
)
db.add(doc_record)
db.flush()

chunk_objs = []
for c in chunks:
    co = DocumentChunk(
        document_id=doc_record.id,
        chunk_index=c["chunk_index"],
        text=c["text"],
        page_number=c["page_number"],
    )
    db.add(co)
    chunk_objs.append(co)
db.flush()
db.commit()

texts = [c["text"] for c in chunks]
vecs = embed_texts(texts)
print(f"Embedding matrix shape: {vecs.shape}")

store = FaissStore(index_dir=DIAG_FAISS)
chunk_ids = [co.id for co in chunk_objs]
store.add_embeddings(vecs, chunk_ids)
print(f"FAISS index total vectors: {store.total_vectors}")
print(f"FAISS id_map: {store.id_map}")

# ── Step 4: Run the 4 diagnostic queries ─────────────────────────────────────
print("\n" + "=" * 70)
print("DIAGNOSTIC QUERIES - TESTING RETRIEVAL DISCRIMINATION")
print("=" * 70)

questions = [
    ("How many days do customers have to request a return?", "30 calendar days"),
    ("How long does the support team take to respond to a return request?", "2 business days"),
    ("How long does an approved refund take?", "5 to 7 business days"),
    ("Who pays return shipping for a change-of-mind return?", "The customer"),
]

for qi, (question, expected) in enumerate(questions, 1):
    print(f"\n{'─' * 70}")
    print(f"Query {qi}: {question!r}")
    print(f"Expected answer contains: {expected!r}")
    print(f"{'─' * 70}")

    # Step A: Generate query embedding
    q_vec = embed_query(question)
    print(f"  Query embedding shape: {q_vec.shape}, norm: {(q_vec ** 2).sum() ** 0.5:.4f}")

    # Step B: FAISS search
    hits = store.search(q_vec, top_k=5)
    print(f"  FAISS returned {len(hits)} hits:")
    for rank, h in enumerate(hits, 1):
        chunk_db = db.query(DocumentChunk).filter_by(id=h['chunk_db_id']).first()
        excerpt = chunk_db.text[:120].replace('\n', ' ').strip() if chunk_db else "N/A"
        contains_expected = expected.lower() in chunk_db.text.lower() if chunk_db else False
        marker = " ★ CONTAINS EXPECTED" if contains_expected else ""
        print(f"    #{rank}: chunk_db_id={h['chunk_db_id']}, score={h['score']:.4f}, "
              f"chunk_index={chunk_db.chunk_index if chunk_db else '?'}, "
              f"page={chunk_db.page_number if chunk_db else '?'}{marker}")
        print(f"         excerpt: {excerpt!r}")

    # Step C: RAG pipeline (without Gemini)
    import app.services.rag_service as rag_mod
    rag_mod.get_faiss_store = lambda: store

    coro = answer_question(question=question, db=db, top_k=5, gemini_model=None)
    try:
        coro.send(None)
        qa_res = None
    except StopIteration as e:
        qa_res = e.value

    if qa_res:
        print(f"\n  RAG Answer (truncated): {qa_res.answer[:200]!r}")
        print(f"  Sources returned: {len(qa_res.sources)}")
        for si, src in enumerate(qa_res.sources, 1):
            print(f"    Source {si}: doc={src.document_name!r}, page={src.page_number}, "
                  f"chunk_idx={src.chunk_index}, score={src.similarity_score:.4f}")
            print(f"              excerpt(first 100): {src.excerpt[:100].replace(chr(10), ' ')!r}")

        # Check: does the top excerpt contain the expected answer?
        top_excerpt = qa_res.sources[0].excerpt if qa_res.sources else ""
        if expected.lower() in top_excerpt.lower():
            print(f"\n  ✅ PASS: Top source contains expected answer ({expected!r})")
        else:
            # Check if any source has it
            any_match = any(expected.lower() in s.excerpt.lower() for s in qa_res.sources)
            if any_match:
                print(f"\n  ⚠️  PARTIAL: Expected answer found in sources but NOT in #1 position")
            else:
                print(f"\n  ❌ FAIL: Expected answer ({expected!r}) NOT found in any source excerpt")
    else:
        print(f"\n  ❌ ERROR: answer_question returned None")

# ── Step 5: Check for identical results ──────────────────────────────────────
print("\n" + "=" * 70)
print("CROSS-QUERY COMPARISON — Are different queries returning the same chunks?")
print("=" * 70)

all_top_chunks = []
for question, _ in questions:
    q_vec = embed_query(question)
    hits = store.search(q_vec, top_k=3)
    top_ids = [h['chunk_db_id'] for h in hits]
    all_top_chunks.append((question[:50], top_ids))

for i, (q, ids) in enumerate(all_top_chunks):
    print(f"  Q{i+1} ({q}...): top 3 chunk_db_ids = {ids}")

# Check uniqueness
all_id_tuples = [tuple(ids) for _, ids in all_top_chunks]
unique_tuples = set(all_id_tuples)
if len(unique_tuples) == 1:
    print("\n  ❌ BUG CONFIRMED: All 4 queries returned the EXACT SAME top-3 chunk IDs!")
elif len(unique_tuples) < len(all_id_tuples):
    print(f"\n  ⚠️  PARTIAL BUG: Only {len(unique_tuples)} unique result sets out of {len(all_id_tuples)} queries")
else:
    print(f"\n  ✅ OK: All {len(unique_tuples)} queries returned DIFFERENT top-3 chunks")

# Cleanup
db.close()
print("\n[DIAGNOSTIC COMPLETE]")
