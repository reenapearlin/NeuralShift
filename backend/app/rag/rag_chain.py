"""Core RAG orchestration functions for indexing, retrieval, and analysis."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter

from langchain.schema import Document

from .config import RAGConfigError
from .embeddings import get_embedding_model
from .llama_model import get_llm
from .loader import load_pdf
from .prompt_templates import (
    KEYWORD_EXTRACTION_PROMPT,
    STRUCTURED_REPORT_PROMPT,
    SUMMARY_PROMPT,
)
from .retriever import get_retriever
from .text_splitter import split_documents
from .vector_store import add_documents_to_index, create_or_load_index, save_index


_STRUCTURED_REPORT_KEYS = {
    "case_title",
    "court",
    "legal_issue",
    "relevant_sections",
    "limitation_analysis",
    "penalty",
    "judgement",
    "key_principles",
}


def index_document(file_path: str, metadata: dict[str, object]) -> None:
    """Index a PDF document into the FAISS vector store.

    Args:
        file_path: Local path to the PDF file.
        metadata: Metadata to be attached to every generated chunk.

    Raises:
        RAGConfigError: If indexing fails or input metadata is invalid.
        FileNotFoundError: If the PDF file does not exist.
    """
    if not isinstance(metadata, dict):
        raise RAGConfigError("metadata must be provided as a dictionary.")

    documents = load_pdf(file_path=file_path)
    chunks = split_documents(documents=documents, metadata=metadata)
    if not chunks:
        raise RAGConfigError("No content extracted from PDF; nothing to index.")

    embedding_model = get_embedding_model()
    vector_store = add_documents_to_index(
        chunks=chunks,
        embedding_model=embedding_model,
    )
    save_index(vector_store=vector_store)


def search_similar_cases(query: str) -> list[Document]:
    """Retrieve top similar chunks for a lawyer query.

    Args:
        query: Search text to match against indexed legal chunks.

    Returns:
        List of relevant ``Document`` objects. Returns an empty list if no index
        exists yet.

    Raises:
        RAGConfigError: If query is invalid or retrieval fails.
    """
    if not isinstance(query, str) or not query.strip():
        raise RAGConfigError("query must be a non-empty string.")

    embedding_model = get_embedding_model()
    vector_store = create_or_load_index(embedding_model=embedding_model)
    if vector_store is None:
        return []

    retriever = get_retriever(vector_store=vector_store)
    try:
        return retriever.invoke(query.strip())
    except Exception as exc:  # pragma: no cover - runtime/library dependent
        raise RAGConfigError("Failed to retrieve similar cases.") from exc


def generate_summary(case_text: str) -> str:
    """Generate a legal summary focused on facts, issue, reasoning, judgment.

    Args:
        case_text: Raw case text.

    Returns:
        Generated summary text.

    Raises:
        RAGConfigError: If input is invalid or generation fails.
    """
    if not isinstance(case_text, str) or not case_text.strip():
        raise RAGConfigError("case_text must be a non-empty string.")

    llm = get_llm()
    prompt = SUMMARY_PROMPT.format(case_text=case_text.strip())
    try:
        result = llm.invoke(prompt)
    except Exception as exc:  # pragma: no cover - runtime/library dependent
        raise RAGConfigError("Failed to generate summary.") from exc
    return str(result).strip()


def generate_structured_report(case_text: str) -> dict[str, object]:
    """Generate a strict structured legal report as a dictionary.

    Args:
        case_text: Raw case text.

    Returns:
        Dictionary with required legal report keys.

    Raises:
        RAGConfigError: If input is invalid or JSON parsing/validation fails.
    """
    if not isinstance(case_text, str) or not case_text.strip():
        raise RAGConfigError("case_text must be a non-empty string.")

    llm = get_llm()
    prompt = STRUCTURED_REPORT_PROMPT.format(case_text=case_text.strip())
    try:
        raw_output = str(llm.invoke(prompt)).strip()
    except Exception as exc:  # pragma: no cover - runtime/library dependent
        raise RAGConfigError("Failed to generate structured report.") from exc

    parsed = _parse_json_object(raw_output)
    normalized = _normalize_structured_report(parsed)
    return normalized


def extract_legal_keywords(case_text: str) -> list[str]:
    """Extract important legal terminologies from case text.

    Uses LLM output first; if parsing fails, falls back to rule-based extraction.

    Args:
        case_text: Raw case text.

    Returns:
        List of legal keywords.

    Raises:
        RAGConfigError: If input is invalid.
    """
    if not isinstance(case_text, str) or not case_text.strip():
        raise RAGConfigError("case_text must be a non-empty string.")

    llm = get_llm()
    prompt = KEYWORD_EXTRACTION_PROMPT.format(case_text=case_text.strip())
    try:
        raw_output = str(llm.invoke(prompt)).strip()
        parsed_keywords = _parse_python_list_of_strings(raw_output)
        if parsed_keywords:
            return parsed_keywords
    except Exception:
        pass

    return _rule_based_legal_keywords(case_text=case_text)


def _parse_json_object(raw_output: str) -> dict[str, object]:
    """Parse a JSON object from raw model output."""
    if not raw_output:
        raise RAGConfigError("Structured report output is empty.")

    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw_output, flags=re.DOTALL)
        if not match:
            raise RAGConfigError("Structured report is not valid JSON.")
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise RAGConfigError("Structured report JSON parsing failed.") from exc

    if not isinstance(parsed, dict):
        raise RAGConfigError("Structured report must be a JSON object.")
    return parsed


def _normalize_structured_report(parsed: dict[str, object]) -> dict[str, object]:
    """Ensure structured report has exact required keys and value types."""
    report: dict[str, object] = {
        "case_title": "",
        "court": "",
        "legal_issue": "",
        "relevant_sections": [],
        "limitation_analysis": "",
        "penalty": "",
        "judgement": "",
        "key_principles": [],
    }

    for key in report:
        if key not in parsed:
            continue
        value = parsed[key]
        if key in {"relevant_sections", "key_principles"}:
            report[key] = _coerce_to_string_list(value)
        else:
            report[key] = "" if value is None else str(value).strip()

    return report


def _parse_python_list_of_strings(raw_output: str) -> list[str]:
    """Parse a Python-style list of strings from model output."""
    if not raw_output:
        return []

    candidate = raw_output
    try:
        parsed = ast.literal_eval(candidate)
    except (SyntaxError, ValueError):
        match = re.search(r"\[.*\]", raw_output, flags=re.DOTALL)
        if not match:
            return []
        try:
            parsed = ast.literal_eval(match.group(0))
        except (SyntaxError, ValueError):
            return []

    return _coerce_to_string_list(parsed)


def _coerce_to_string_list(value: object) -> list[str]:
    """Convert input value into a clean list of unique non-empty strings."""
    if not isinstance(value, list):
        return []

    seen: set[str] = set()
    cleaned: list[str] = []
    for item in value:
        if item is None:
            continue
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
    return cleaned


def _rule_based_legal_keywords(case_text: str) -> list[str]:
    """Fallback keyword extraction using legal phrase patterns and frequency."""
    normalized_text = case_text.lower()

    phrase_patterns = [
        r"section\s+\d+[a-z]?",
        r"negotiable instruments act",
        r"dishonou?r(?:ed|)",
        r"cheque(?:\s+bounce)?",
        r"statutory notice",
        r"limitation period",
        r"legally enforceable debt",
        r"presumption under section 139",
        r"complainant",
        r"accused",
        r"conviction",
        r"acquittal",
        r"sentence",
        r"fine",
        r"compensation",
    ]

    matched_terms: list[str] = []
    for pattern in phrase_patterns:
        matches = re.findall(pattern, normalized_text, flags=re.IGNORECASE)
        for match in matches:
            term = re.sub(r"\s+", " ", match).strip()
            if term:
                matched_terms.append(term)

    token_pattern = re.compile(r"\b[a-zA-Z][a-zA-Z\s]{3,40}\b")
    stop_words = {
        "this",
        "that",
        "with",
        "from",
        "have",
        "were",
        "been",
        "court",
        "case",
        "under",
        "shall",
        "there",
        "their",
        "which",
        "where",
        "would",
        "could",
        "should",
    }
    token_counts = Counter(
        token.strip().lower()
        for token in token_pattern.findall(case_text)
        if token.strip().lower() not in stop_words
    )

    frequent_terms = [term for term, _ in token_counts.most_common(15)]
    combined = matched_terms + frequent_terms
    return _coerce_to_string_list(combined)
