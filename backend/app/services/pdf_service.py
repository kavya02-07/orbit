"""
PDF text extraction using PyMuPDF (fitz).
Returns a list of (page_number, text) tuples.
"""
from pathlib import Path
import fitz  # PyMuPDF


def extract_pages(file_path: str | Path) -> list[tuple[int, str]]:
    """
    Open a PDF and extract text from every page.
    Returns [(page_number_1_indexed, text), ...]
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages: list[tuple[int, str]] = []
    with fitz.open(str(path)) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            pages.append((i, text))

    return pages


def get_page_count(file_path: str | Path) -> int:
    with fitz.open(str(file_path)) as doc:
        return doc.page_count
