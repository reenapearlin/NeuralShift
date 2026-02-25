"""Ollama LLM initialization for the RAG module."""

from __future__ import annotations

from functools import lru_cache

try:
    from langchain_ollama import OllamaLLM
except ImportError:  # pragma: no cover - fallback for older installations
    from langchain_community.llms import Ollama as OllamaLLM

from .config import RAGConfigError, get_rag_config


@lru_cache(maxsize=1)
def get_llm() -> OllamaLLM:
    """Return a cached OllamaLLM instance for local inference.

    The model is initialized once and reused for subsequent calls.

    Returns:
        Initialized ``OllamaLLM`` model instance.

    Raises:
        RAGConfigError: If model configuration is invalid or init fails.
    """
    config = get_rag_config()
    config.validate_llm()

    try:
        return OllamaLLM(
            model=config.llm_model,
            base_url=config.ollama_base_url,
            temperature=config.llm_temperature,
            num_predict=config.llm_max_tokens,
        )
    except Exception as exc:  # pragma: no cover - runtime/system dependent
        raise RAGConfigError("Failed to initialize OllamaLLM.") from exc
