"""Document chunking utilities for the RAG module."""

from __future__ import annotations

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .config import RAGConfigError


def split_documents(
    documents: list[Document], metadata: dict[str, object]
) -> list[Document]:
    """Split documents into chunks and attach shared metadata.

    Args:
        documents: Source LangChain documents to split.
        metadata: Metadata to merge into each produced chunk.

    Returns:
        A list of chunked LangChain ``Document`` objects.

    Raises:
        RAGConfigError: If input types are invalid.
    """
    if documents is None:
        return []

    if not isinstance(documents, list):
        raise RAGConfigError("documents must be provided as a list of Document.")
    if not isinstance(metadata, dict):
        raise RAGConfigError("metadata must be provided as a dictionary.")
    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(documents)

    for chunk in chunks:
        chunk.metadata.update(metadata)

    return chunks
