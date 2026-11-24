"""
Text chunking utilities for PDF document processing.
"""
import re
from typing import Generator


def clean_text(text: str) -> str:
    """Remove excess whitespace and control characters."""
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 100,
    chunk_overlap: int = 20,
) -> Generator[str, None, None]:
    """
    Split text into overlapping chunks by word boundary.
    Yields individual chunk strings.
    """
    words = text.split()
    if not words:
        return

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words).strip()
        if chunk:
            yield chunk
        if end >= len(words):
            break
        start = max(start + 1, end - chunk_overlap)


def chunk_pages(
    pages: list[tuple[int, str]],  # [(page_number, page_text), ...]
    chunk_size: int = 100,
    chunk_overlap: int = 20,
) -> list[dict]:
    """
    Chunk a list of (page_number, text) pairs.
    Returns list of dicts: {chunk_index, text, page_number}
    """
    all_chunks = []
    chunk_index = 0
    for page_number, raw_text in pages:
        text = clean_text(raw_text)
        if not text:
            continue
        for chunk in chunk_text(text, chunk_size, chunk_overlap):
            all_chunks.append({
                "chunk_index": chunk_index,
                "text": chunk,
                "page_number": page_number,
            })
            chunk_index += 1
    return all_chunks
