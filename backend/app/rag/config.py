"""Centralized configuration for the RAG module.

This module is import-safe and performs no heavy initialization at import time.
It only reads environment values and exposes a cached settings object.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


class RAGConfigError(ValueError):
    """Raised when RAG configuration is invalid or incomplete."""


@dataclass(frozen=True)
class RAGConfig:
    """Configuration container for all RAG module components."""

    project_root: Path
    faiss_index_dir: Path
    faiss_index_name: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    ollama_base_url: str
    embedding_model: str
    llm_model: str
    llm_temperature: float
    llm_max_tokens: int

    @property
    def faiss_index_path(self) -> Path:
        """Return the full local path used by FAISS persistence."""
        return self.faiss_index_dir / self.faiss_index_name

    def ensure_faiss_directory(self) -> None:
        """Create FAISS persistence directory if it does not exist."""
        self.faiss_index_dir.mkdir(parents=True, exist_ok=True)

    def validate_chunking(self) -> None:
        """Validate chunk size and overlap settings."""
        if self.chunk_size <= 0:
            raise RAGConfigError("chunk_size must be greater than 0.")
        if self.chunk_overlap < 0:
            raise RAGConfigError("chunk_overlap must be >= 0.")
        if self.chunk_overlap >= self.chunk_size:
            raise RAGConfigError(
                "chunk_overlap must be smaller than chunk_size."
            )

    def validate_retrieval(self) -> None:
        """Validate retrieval settings."""
        if self.top_k <= 0:
            raise RAGConfigError("top_k must be greater than 0.")

    def validate_embeddings(self) -> None:
        """Validate Ollama embeddings configuration."""
        if not self.ollama_base_url.strip():
            raise RAGConfigError(
                "RAG_OLLAMA_BASE_URL is missing. Set it in environment variables."
            )
        if not self.embedding_model.strip():
            raise RAGConfigError("embedding_model must be a non-empty string.")

    def validate_llm(self) -> None:
        """Validate Ollama LLM configuration."""
        if not self.ollama_base_url.strip():
            raise RAGConfigError(
                "RAG_OLLAMA_BASE_URL is missing. Set it in environment variables."
            )
        if not self.llm_model.strip():
            raise RAGConfigError("RAG_LLM_MODEL is missing or empty.")
        if self.llm_temperature < 0.0 or self.llm_temperature > 1.0:
            raise RAGConfigError("llm_temperature must be between 0.0 and 1.0.")


def _resolve_project_root() -> Path:
    """Resolve backend project root from this file location."""
    # backend/app/rag/config.py -> backend
    return Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def get_rag_config() -> RAGConfig:
    """Return a cached RAGConfig instance based on environment variables."""
    project_root = _resolve_project_root()
    default_faiss_dir = project_root / "storage" / "faiss"

    faiss_index_dir = Path(
        os.getenv("RAG_FAISS_INDEX_DIR", str(default_faiss_dir))
    ).expanduser()
    if not faiss_index_dir.is_absolute():
        faiss_index_dir = (project_root / faiss_index_dir).resolve()

    config = RAGConfig(
        project_root=project_root,
        faiss_index_dir=faiss_index_dir,
        faiss_index_name=os.getenv("RAG_FAISS_INDEX_NAME", "section138_cases"),
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
        top_k=int(os.getenv("RAG_TOP_K", "5")),
        ollama_base_url=os.getenv("RAG_OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        embedding_model=os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text"),
        llm_model=os.getenv("RAG_LLM_MODEL", "llama3"),
        llm_temperature=float(os.getenv("RAG_LLM_TEMPERATURE", "0.2")),
        llm_max_tokens=int(os.getenv("RAG_LLM_MAX_TOKENS", "2048")),
    )

    config.validate_chunking()
    config.validate_retrieval()
    return config


__all__ = ["RAGConfig", "RAGConfigError", "get_rag_config"]
