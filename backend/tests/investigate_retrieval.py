"""
Comprehensive investigation script for the 5 queries against the currently indexed FAISS and DB.
"""
import os
import sys
import sqlite3
from pathlib import Path
import numpy as np

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from app.core.config import get_settings
from app.db.database import init_db_engine, get_db
from app.models.models import Document, DocumentChunk
from app.services.faiss_service import get_faiss_store
from app.services.embedding_service import embed_query, embed_texts, get_embedding_model
from app.services.rag_service import answer_question
import asyncio

settings = get_settings()
print(f"Settings FAISS index path: {settings.faiss_index_path}")
print(f"Settings embedding model: {settings.embedding_model}")

init_db_engine()
db = next(get_db())

# Check document and chunk records
docs = db.query(Document).all()
print(f"\n--- Documents in DB: {len(docs)} ---")
for d in docs:
    print(f"  Doc ID: {d.id}, Filename: {d.filename}, Original: {d.original_filename}, Chunks: {d.chunk_count}, Indexed: {d.is_indexed}")

chunks = db.query(DocumentChunk).order_by(DocumentChunk.id).all()
print(f"\n--- Chunks in DB: {len(chunks)} ---")
for c in chunks:
    words = len(c.text.split())
    print(f"  Chunk ID: {c.id}, Index: {c.chunk_index}, Page: {c.page_number}, Words: {words}, Faiss ID: {c.faiss_id}")
    print(f"    Text: {c.text[:100]}...")

# Check FAISS index
store = get_faiss_store()
print(f"\n--- FAISS Index ---")
print(f"  Total vectors (ntotal): {store.index.ntotal}")
print(f"  Metric type: {store.index.metric_type} (0=INNER_PRODUCT, 1=L2)")
print(f"  Vector dimension: {store.index.d}")
print(f"  id_map: {store.id_map}")

# Reconstruct and check vector norms in FAISS
print("\n--- FAISS Vector Norms ---")
for i in range(store.index.ntotal):
    v = store.index.reconstruct(i)
    norm = np.linalg.norm(v)
    chunk_db_id = store.id_map[i] if i < len(store.id_map) else None
    print(f"  FAISS row {i} -> Chunk DB ID {chunk_db_id}: norm = {norm:.6f}, shape = {v.shape}")

# Re-embed the chunks from DB fresh and compare with what is in FAISS!
print("\n--- Comparing Stored FAISS Vectors with Fresh Embeddings of DB Chunks ---")
fresh_embeddings = embed_texts([c.text for c in chunks])
for i, c in enumerate(chunks):
    stored_v = store.index.reconstruct(i)
    fresh_v = fresh_embeddings[i]
    diff = np.max(np.abs(stored_v - fresh_v))
    cosine_sim = np.dot(stored_v, fresh_v) / (np.linalg.norm(stored_v) * np.linalg.norm(fresh_v))
    print(f"  Chunk {c.id} (row {i}): max absolute diff = {diff:.6e}, cosine sim to fresh = {cosine_sim:.6f}")

# Test the 5 queries
queries = [
    "How many days do customers have to request a return?",
    "How long does the support team take to respond?",
    "How long does an approved refund take?",
    "Who pays return shipping for a change-of-mind return?",
    "What payment methods does the company accept?"
]

print("\n" + "="*80)
print("TESTING THE 5 QUERIES INDEPENDENTLY")
print("="*80)

query_results = []

for q_idx, q in enumerate(queries, 1):
    print(f"\n{'#'*80}")
    print(f"QUERY {q_idx}: \"{q}\"")
    print(f"{'#'*80}")

    # 1. Exact query received
    print(f"1. Exact query: {q!r}")

    # 2. Embedding model
    model = get_embedding_model()
    print(f"2. Embedding model: {model}")

    # Generate query embedding
    q_vec = embed_query(q)
    print(f"   Query vector shape: {q_vec.shape}, norm: {np.linalg.norm(q_vec):.6f}")

    # 3. Direct FAISS search
    raw_hits = store.search(q_vec, top_k=5)
    print(f"\n3. Direct FAISS raw search results (top {len(raw_hits)}):")
    for rank, h in enumerate(raw_hits, 1):
        cid = h["chunk_db_id"]
        score = h["score"]
        c_obj = db.query(DocumentChunk).filter_by(id=cid).first()
        c_text = c_obj.text if c_obj else "MISSING"
        print(f"   Rank {rank}: Chunk ID={cid}, Score={score:.4f} ({score*100:.1f}%)")
        print(f"           Excerpt: {c_text[:120]}...")

    # 4. Full answer_question RAG pipeline
    coro = answer_question(q, db=db, top_k=5, gemini_model=None)
    try:
        coro.send(None)
        ans_resp = None
    except StopIteration as e:
        ans_resp = e.value
    print(f"\n4. RAG answer_question output:")
    print(f"   model_used: {ans_resp.model_used}")
    print(f"   has_sufficient_context: {ans_resp.has_sufficient_context}")
    print(f"   sources count: {len(ans_resp.sources)}")
    print(f"   Source order:")
    for s_idx, s in enumerate(ans_resp.sources, 1):
        print(f"     Source {s_idx}: Doc={s.document_name}, Page={s.page_number}, Chunk_idx={s.chunk_index}, Score={s.similarity_score:.4f} ({s.similarity_score*100:.1f}%)")
        print(f"               Excerpt: {s.excerpt[:90]}...")

    print(f"\n   Answer text preview:\n   " + ans_resp.answer.replace("\n", "\n   ")[:300] + "...")

    query_results.append({
        "query": q,
        "hits": [(h["chunk_db_id"], h["score"]) for h in raw_hits],
        "sources": [(s.chunk_index, s.similarity_score) for s in ans_resp.sources]
    })

# Summary Comparison
print("\n" + "="*80)
print("RANKING COMPARISON ACROSS ALL 5 QUERIES")
print("="*80)
for r in query_results:
    hit_str = ", ".join([f"ID {cid} ({score*100:.1f}%)" for cid, score in r["hits"]])
    print(f"Query: {r['query'][:45]}... -> [{hit_str}]")

db.close()
