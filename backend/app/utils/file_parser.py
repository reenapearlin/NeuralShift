"""File parsing helpers for uploaded-context enrichment and PDF extraction."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from PyPDF2 import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """Extract full text from a PDF file; return empty string on failure."""
    try:
        reader = PdfReader(file_path)
        text_parts: list[str] = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return " ".join(text_parts).strip()
    except Exception:
        return ""


def normalize_text(value: Optional[str]) -> str:
    """Normalize text by collapsing whitespace and trimming edges."""
    if not value:
        return ""
    return " ".join(value.split())


def extract_search_file_context(
    search_input: Mapping[str, Any],
    max_chars: int = 1000,
) -> str:
    """Extract optional uploaded file context from a search payload."""
    candidates = [
        search_input.get("file_text"),
        search_input.get("uploaded_text"),
        search_input.get("file_summary"),
    ]

    for item in candidates:
        cleaned = normalize_text(str(item)) if item is not None else ""
        if cleaned:
            return cleaned[:max_chars]

    return ""


def append_file_context_to_query(
    base_query: str,
    search_input: Mapping[str, Any],
    max_chars: int = 1000,
) -> str:
    """Append uploaded file context when file_upload_flag is enabled."""
    if not search_input.get("file_upload_flag"):
        return base_query

    file_context = extract_search_file_context(
        search_input=search_input,
        max_chars=max_chars,
    )
    if not file_context:
        return base_query

    return f"{base_query} | uploaded context: {file_context}"
