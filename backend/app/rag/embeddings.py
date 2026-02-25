"""Embedding model initialization for the RAG module."""

from __future__ import annotations

try:
    from langchain_ollama import OllamaEmbeddings
except ImportError:  # pragma: no cover - fallback for older installations
    from langchain_community.embeddings import OllamaEmbeddings

from .config import RAGConfigError, get_rag_config


def get_embedding_model() -> OllamaEmbeddings:
    """Create and return an Ollama embeddings model instance.

    Returns:
        An initialized ``OllamaEmbeddings`` object.

    Raises:
        RAGConfigError: If Ollama configuration is missing or initialization fails.
    """
    config = get_rag_config()
    config.validate_embeddings()

    try:
        return OllamaEmbeddings(
            base_url=config.ollama_base_url,
            model=config.embedding_model,
        )
    except Exception as exc:  # pragma: no cover - runtime/environment dependent
        raise RAGConfigError("Failed to initialize OllamaEmbeddings.") from exc
