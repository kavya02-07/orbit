"""
FAISS index management — build, persist, load, and search.
Uses cosine similarity via inner product on normalised vectors.
"""
import json
import os
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from app.core.config import get_settings


class FaissStore:
    """
    Wraps a FAISS IndexFlatIP (inner product = cosine for normalised vecs).
    Maintains a parallel list mapping FAISS row-id → chunk DB id.
    """

    DIMENSION = 384  # all-MiniLM-L6-v2

    def __init__(self, index_dir: Optional[str] = None):
        settings = get_settings()
        self.index_dir = Path(index_dir or settings.faiss_index_path)
        self.index_path = self.index_dir / "index.faiss"
        self.map_path = self.index_dir / "id_map.json"
        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.DIMENSION)
        self.id_map: list[int] = []  # faiss_row_id → chunk_db_id
        self._load_if_exists()

    # ── Persistence ────────────────────────────────────────────────────────────

    def _load_if_exists(self):
        if self.index_path.exists() and self.map_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.map_path) as f:
                self.id_map = json.load(f)

    def save(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(self.index_path))
        with open(self.map_path, "w") as f:
            json.dump(self.id_map, f)

    # ── Indexing ───────────────────────────────────────────────────────────────

    def add_embeddings(self, embeddings: np.ndarray, chunk_db_ids: list[int]):
        """Add normalised float32 embeddings and their corresponding DB chunk ids."""
        if embeddings.shape[0] == 0:
            return
        self.index.add(embeddings)
        self.id_map.extend(chunk_db_ids)
        self.save()

    def remove_by_faiss_ids(self, faiss_ids: list[int]):
        """Remove vectors by their FAISS internal row ids (IDSelectorBatch)."""
        if not faiss_ids:
            return
        selector = faiss.IDSelectorBatch(np.array(faiss_ids, dtype=np.int64))
        self.index.remove_ids(selector)
        # Rebuild id_map — keep entries not in the removed set
        removed = set(faiss_ids)
        self.id_map = [cid for i, cid in enumerate(self.id_map) if i not in removed]
        self.save()

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
        """
        Search the index with a normalised query vector.
        Returns list of {chunk_db_id, score} dicts sorted by descending score.
        """
        if self.index.ntotal == 0:
            return []

        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.id_map):
                continue
            results.append({
                "chunk_db_id": self.id_map[idx],
                "score": float(dist),
            })
        return results

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal


# Module-level singleton
_store: Optional[FaissStore] = None


def get_faiss_store() -> FaissStore:
    global _store
    if _store is None:
        _store = FaissStore()
    return _store


def reset_faiss_store():
    """Force reload from disk (e.g. after adding new vectors in another process)."""
    global _store
    _store = None
