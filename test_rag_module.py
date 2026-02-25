"""Standalone test script for validating the RAG module end-to-end.

Run from project root:
    python test_rag_module.py
"""

from __future__ import annotations

import json
import os
import subprocess
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from backend.app.rag.loader import load_pdf
from backend.app.rag.rag_chain import (
    extract_legal_keywords,
    generate_structured_report,
    generate_summary,
    index_document,
    search_similar_cases,
)



DEFAULT_SAMPLE_PDF_PATH = (
    "data/legal_pdfs/Aishwariya_Flavour_Food_Pvt_Ltd_vs_Nikhil_Bhardwaj_And_Anr_on_18_February_2026.PDF"
)

DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_LLM_MODEL = "llama3"
DEFAULT_EMBEDDING_MODEL = "nomic-embed-text"


def _ensure_test_env() -> None:
    """Set default environment values so the script runs with minimal setup."""
    os.environ.setdefault("RAG_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    os.environ.setdefault("RAG_LLM_MODEL", DEFAULT_LLM_MODEL)
    os.environ.setdefault("RAG_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    os.environ.setdefault("RAG_TEST_PDF_PATH", DEFAULT_SAMPLE_PDF_PATH)


def _build_case_text(file_path: str) -> str:
    """Load PDF and concatenate page content into a single text string."""
    documents = load_pdf(file_path=file_path)
    return "\n\n".join(doc.page_content for doc in documents if doc.page_content).strip()


def _print_header(title: str) -> None:
    """Print a clean section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def _is_ollama_reachable(base_url: str) -> bool:
    """Check whether Ollama API is reachable."""
    tags_url = f"{base_url.rstrip('/')}/api/tags"
    try:
        with urllib.request.urlopen(tags_url, timeout=3) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def _ensure_ollama_server(base_url: str) -> bool:
    """Ensure Ollama server is available; attempt to start it if needed."""
    if _is_ollama_reachable(base_url):
        return True

    try:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, OSError):
        return False

    # Wait briefly for server startup.
    for _ in range(10):
        if _is_ollama_reachable(base_url):
            return True
        import time

        time.sleep(1)

    return False


def test_indexing_mode(file_path: str, metadata: dict[str, Any]) -> bool:
    """Test indexing mode by indexing one PDF with metadata."""
    _print_header("TEST 1: INDEXING MODE")
    try:
        index_document(file_path=file_path, metadata=metadata)
        print("[PASS] Indexing completed successfully.")
        return True
    except Exception as exc:
        print(f"[FAIL] Indexing failed: {exc}")
        traceback.print_exc()
        return False


def test_query_mode() -> bool:
    """Test query mode by retrieving relevant chunks from FAISS."""
    _print_header("TEST 2: QUERY MODE")
    try:
        results = search_similar_cases("notice period under section 138")
        print(f"Retrieved documents count: {len(results)}")
        if results:
            snippet = results[0].page_content[:300].replace("\n", " ").strip()
            print(f"First document snippet: {snippet}")
        else:
            print("First document snippet: <no documents returned>")
        print("[PASS] Query mode completed.")
        return True
    except Exception as exc:
        print(f"[FAIL] Query mode failed: {exc}")
        traceback.print_exc()
        return False


def test_file_view_mode(file_path: str) -> bool:
    """Test summary, structured report, and keyword extraction flows."""
    _print_header("TEST 3: FILE VIEW MODE")
    try:
        case_text = _build_case_text(file_path=file_path)
        if not case_text:
            raise ValueError("Extracted case text is empty.")

        summary = generate_summary(case_text=case_text)
        print("\n[SUMMARY]")
        print(summary)

        structured_report = generate_structured_report(case_text=case_text)
        print("\n[STRUCTURED REPORT]")
        print(json.dumps(structured_report, indent=2, ensure_ascii=True))

        keywords = extract_legal_keywords(case_text=case_text)
        print("\n[KEYWORDS]")
        print(keywords)

        print("[PASS] File view mode completed.")
        return True
    except Exception as exc:
        print(f"[FAIL] File view mode failed: {exc}")
        traceback.print_exc()
        return False


def main() -> None:
    """Run all standalone RAG module tests."""
    _ensure_test_env()
    sample_pdf_path = os.getenv("RAG_TEST_PDF_PATH", DEFAULT_SAMPLE_PDF_PATH)
    ollama_base_url = os.getenv("RAG_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL)
    metadata: dict[str, Any] = {
        "case_id": "TEST-SECTION-138-001",
        "source": "local_test",
        "act": "Negotiable Instruments Act",
        "section": "138",
    }

    if not Path(sample_pdf_path).exists():
        print(f"[WARN] Sample PDF path not found: {sample_pdf_path}")
        print("Set RAG_TEST_PDF_PATH to a valid local PDF before running full tests.")
        print("RAG MODULE TEST COMPLETED")
        return

    if not _ensure_ollama_server(ollama_base_url):
        print(f"[FAIL] Ollama server is not reachable at {ollama_base_url}")
        print("Start Ollama and ensure models are available:")
        print("1. ollama serve")
        print("2. ollama pull llama3")
        print("3. ollama pull nomic-embed-text")
        print("RAG MODULE TEST COMPLETED")
        return

    indexing_ok = test_indexing_mode(file_path=sample_pdf_path, metadata=metadata)
    query_ok = test_query_mode()
    file_view_ok = test_file_view_mode(file_path=sample_pdf_path)

    if indexing_ok and query_ok and file_view_ok:
        print("\nRAG MODULE TEST COMPLETED SUCCESSFULLY")
    else:
        print("\nRAG MODULE TEST COMPLETED WITH FAILURES")


if __name__ == "__main__":
    main()
