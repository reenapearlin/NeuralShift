"""FAISS vector store management for the RAG module."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain.schema import Document
from langchain_community.vectorstores import FAISS

from .config import RAGConfigError, get_rag_config


def create_or_load_index(embedding_model: Any) -> FAISS | None:
    """Load an existing FAISS index, or prepare storage for a new index.

    Args:
        embedding_model: Pre-initialized embedding model used by FAISS.

    Returns:
        Loaded ``FAISS`` instance if available; otherwise ``None`` when the
        index does not exist yet.

    Raises:
        RAGConfigError: If the embedding model is missing or index loading fails.
    """
    if embedding_model is None:
        raise RAGConfigError("embedding_model must be provided.")

    config = get_rag_config()
    config.ensure_faiss_directory()

    index_path = config.faiss_index_path
    faiss_file = index_path / "index.faiss"
    pkl_file = index_path / "index.pkl"

    if not faiss_file.exists() or not pkl_file.exists():
        return None

    try:
        return FAISS.load_local(
            folder_path=str(index_path),
            embeddings=embedding_model,
            allow_dangerous_deserialization=True,
        )
    except Exception as exc:  # pragma: no cover - library/runtime dependent
        raise RAGConfigError(f"Failed to load FAISS index from {index_path}") from exc


def add_documents_to_index(
    chunks: list[Document], embedding_model: Any
) -> FAISS:
    """Create a FAISS index or append chunks to an existing one.

    Args:
        chunks: Chunked documents to be stored in FAISS.
        embedding_model: Pre-initialized embedding model used by FAISS.

    Returns:
        Updated ``FAISS`` vector store.

    Raises:
        RAGConfigError: If inputs are invalid or index update fails.
    """
    if embedding_model is None:
        raise RAGConfigError("embedding_model must be provided.")
    if not isinstance(chunks, list):
        raise RAGConfigError("chunks must be provided as a list of Document.")
    if not chunks:
        raise RAGConfigError("chunks list is empty; nothing to index.")

    vector_store = create_or_load_index(embedding_model=embedding_model)

    try:
        if vector_store is None:
            vector_store = FAISS.from_documents(chunks, embedding_model)
        else:
            vector_store.add_documents(chunks)
    except Exception as exc:  # pragma: no cover - library/runtime dependent
        raise RAGConfigError("Failed to add documents to FAISS index.") from exc

    return vector_store


def save_index(vector_store: FAISS) -> None:
    """Persist a FAISS index to local disk.

    Args:
        vector_store: FAISS vector store to persist.

    Raises:
        RAGConfigError: If vector store is missing or save operation fails.
    """
    if vector_store is None:
        raise RAGConfigError("vector_store must be provided.")

    config = get_rag_config()
    config.ensure_faiss_directory()

    index_path: Path = config.faiss_index_path
    index_path.mkdir(parents=True, exist_ok=True)

    try:
        vector_store.save_local(str(index_path))
    except Exception as exc:  # pragma: no cover - library/runtime dependent
        raise RAGConfigError(f"Failed to save FAISS index to {index_path}") from exc
