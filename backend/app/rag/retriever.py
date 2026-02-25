"""Retriever utilities for the RAG module."""

from __future__ import annotations

from typing import Any

from langchain_community.vectorstores import FAISS

from .config import RAGConfigError


def get_retriever(vector_store: FAISS) -> Any:
    """Convert a FAISS vector store into a retriever.

    Args:
        vector_store: Initialized FAISS vector store.

    Returns:
        A retriever object configured with ``search_kwargs={"k": 5}``.

    Raises:
        RAGConfigError: If vector_store is missing.
    """
    if vector_store is None:
        raise RAGConfigError("vector_store must be provided.")

    return vector_store.as_retriever(search_kwargs={"k": 5})
