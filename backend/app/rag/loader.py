"""PDF loading utilities for the RAG module."""

from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document

from .config import RAGConfigError


def load_pdf(file_path: str) -> list[Document]:
    """Load a PDF file from local disk and return LangChain documents.

    Args:
        file_path: Absolute or relative path to a PDF file.

    Returns:
        A list of LangChain ``Document`` objects extracted from the PDF.

    Raises:
        RAGConfigError: If the provided path is empty, invalid, or not a file.
        FileNotFoundError: If the file does not exist.
    """
    if not isinstance(file_path, str) or not file_path.strip():
        raise RAGConfigError("Invalid file path: expected a non-empty string.")

    try:
        pdf_path = Path(file_path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise RAGConfigError(f"Invalid file path: {file_path}") from exc

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.is_file():
        raise RAGConfigError(f"Invalid file path: not a file: {pdf_path}")

    loader = PyPDFLoader(str(pdf_path))
    return loader.load()
