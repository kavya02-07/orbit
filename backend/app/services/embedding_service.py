"""
Embedding generation using Sentence Transformers (all-MiniLM-L6-v2).
Singleton pattern to load the model only once per process, lazy-loaded on demand.
"""
from functools import lru_cache
import numpy as np

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_model():
    """Lazy-load SentenceTransformer from local cache for instant offline execution."""
    from sentence_transformers import SentenceTransformer
    settings = get_settings()
    try:
        return SentenceTransformer(settings.embedding_model, local_files_only=True)
    except Exception:
        return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Generate normalized float32 embeddings for a list of texts.
    Returns shape (N, D) numpy array.
    """
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=64,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return embeddings.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Single query embedding, shape (1, D)."""
    return embed_texts([query])
