"""Service-layer logic for search and case-view flows in the LEGAL 138 AI system."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Mapping, Optional

from sqlalchemy import text

from app.config.settings import get_settings
from app.rag.rag_chain import extract_legal_keywords
from app.utils.file_parser import append_file_context_to_query
from app.utils.file_parser import extract_text_from_pdf
from app.utils.logger import log_search_event
from app.utils.metadata_filter import fetch_metadata_filtered_cases, get_case_table_config, quote_ident


def build_structured_legal_query(search_input: Mapping[str, Any]) -> str:
    """Build a structured legal query string from search form fields."""
    parts: List[str] = ["Section 138 NI Act"]

    cheque_amount = search_input.get("cheque_amount")
    notice_period = search_input.get("notice_period")
    dishonor_reason = search_input.get("dishonor_reason")
    nature_of_debt = search_input.get("nature_of_debt")
    court = search_input.get("court")
    year = search_input.get("year")
    bench = search_input.get("bench")
    file_upload_flag = search_input.get("file_upload_flag")

    if cheque_amount is not None:
        parts.append(f"cheque amount: {cheque_amount}")
    if notice_period is not None:
        parts.append(f"notice period: {notice_period} days")
    if dishonor_reason:
        parts.append(f"dishonor reason: {dishonor_reason}")
    if nature_of_debt:
        parts.append(f"nature of debt: {nature_of_debt}")
    if court:
        parts.append(f"court: {court}")
    if year is not None:
        parts.append(f"year: {year}")
    if bench:
        parts.append(f"bench: {bench}")
    if file_upload_flag is not None:
        parts.append(f"file upload context: {'yes' if file_upload_flag else 'no'}")

    base_query = " | ".join(parts)
    return append_file_context_to_query(base_query=base_query, search_input=search_input)


def _extract_case_id(document: Any) -> Optional[Any]:
    """Extract case identifier from retriever document metadata."""
    metadata = getattr(document, "metadata", {}) or {}
    for key in ("case_id", "id", "casefile_id"):
        if key in metadata and metadata[key] is not None:
            return metadata[key]
    return None


def _extract_document_text(document: Any) -> str:
    """Extract text content from a retriever document instance."""
    for attr in ("page_content", "content", "text"):
        value = getattr(document, attr, None)
        if value:
            return str(value)
    return ""


def _call_retriever(retriever: Any, query: str, k: int) -> List[Any]:
    """Call retriever through common invocation interfaces."""
    if retriever is None:
        return []

    if hasattr(retriever, "get_relevant_documents"):
        return retriever.get_relevant_documents(query, k=k)

    if hasattr(retriever, "invoke"):
        try:
            return retriever.invoke({"query": query, "k": k})
        except TypeError:
            return retriever.invoke(query)

    if callable(retriever):
        try:
            return retriever(query=query, k=k)
        except TypeError:
            return retriever(query)

    raise RuntimeError("Retriever dependency does not expose a supported interface.")


def _call_chain(chain: Any, payload: Mapping[str, Any]) -> Any:
    """Call an LLM chain through common invocation interfaces."""
    if chain is None:
        return None

    if hasattr(chain, "invoke"):
        return chain.invoke(payload)

    if hasattr(chain, "run"):
        return chain.run(payload)

    if callable(chain):
        return chain(payload)

    raise RuntimeError("Chain dependency does not expose a supported interface.")


def _parse_chain_output(value: Any) -> Any:
    """Normalize chain output into JSON-compatible objects."""
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed
        except json.JSONDecodeError:
            return value.strip()

    if hasattr(value, "dict"):
        return value.dict()

    if hasattr(value, "model_dump"):
        return value.model_dump()

    return str(value)


def _invoke_with_timeout(func: Any, timeout_seconds: int = 20) -> Any:
    """Run a callable with timeout and return None on timeout/failure."""
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func)
            return future.result(timeout=timeout_seconds)
    except (FutureTimeoutError, Exception):
        return None


def _fallback_summary_from_text(text_value: str) -> str:
    text = " ".join((text_value or "").split())
    if not text:
        return (
            "Facts: Not Specified\n"
            "Legal Issue: Not Specified\n"
            "Court Reasoning: Not Specified\n"
            "Final Judgment: Not Specified"
        )
    head = text[:1200]
    return (
        f"Facts: {head[:320]}\n"
        f"Legal Issue: {head[320:600] or 'Not Specified'}\n"
        f"Court Reasoning: {head[600:900] or 'Not Specified'}\n"
        f"Final Judgment: {head[900:1200] or 'Not Specified'}"
    )


def _fallback_structured_report(text_value: str, case_title: str) -> Dict[str, Any]:
    text = " ".join((text_value or "").split())
    sections = sorted(set(re.findall(r"section\s+\d+[a-z]?", text, flags=re.IGNORECASE)))
    if not sections:
        sections = ["Not Specified"]

    principles = sorted(
        set(
            match.title()
            for match in re.findall(
                r"(legally enforceable debt|dishonou?r of cheque|statutory notice|presumption|burden of proof|limitation(?: period)?)",
                text,
                flags=re.IGNORECASE,
            )
        )
    )
    if not principles:
        principles = ["Not Specified"]

    return {
        "case_title": case_title or "Not Specified",
        "court": "Not Specified",
        "legal_issue": "Not Specified",
        "relevant_sections": sections,
        "limitation_analysis": "Not Specified",
        "penalty": "Not Specified",
        "judgement": "Not Specified",
        "key_principles": principles,
    }


def _fallback_keywords(text_value: str, limit: int = 12) -> List[str]:
    text = (text_value or "").lower()
    patterns = [
        r"section\s+\d+[a-z]?",
        r"negotiable instruments act",
        r"dishonou?r(?:ed|)",
        r"cheque(?:\s+bounce)?",
        r"statutory notice",
        r"legally enforceable debt",
        r"presumption",
        r"limitation(?: period)?",
        r"burden of proof",
    ]
    seen: set[str] = set()
    items: List[str] = []
    for pattern in patterns:
        for hit in re.findall(pattern, text, flags=re.IGNORECASE):
            term = re.sub(r"\s+", " ", hit).strip()
            key = term.lower()
            if not term or key in seen:
                continue
            seen.add(key)
            items.append(term.title())
            if len(items) >= limit:
                return items
    return items


def search_cases(
    db: Any,
    retriever: Any,
    search_input: Mapping[str, Any],
    user_id: Optional[int] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Run retrieval-only case search with metadata filtering before FAISS calls."""
    structured_query = build_structured_legal_query(search_input)
    metadata_rows = fetch_metadata_filtered_cases(db=db, search_input=search_input, limit=max(limit * 20, 50))

    row_map: Dict[str, Dict[str, Any]] = {str(row["case_id"]): row for row in metadata_rows if row.get("case_id") is not None}
    allowed_ids = set(row_map.keys())

    documents = _call_retriever(retriever=retriever, query=structured_query, k=max(limit * 4, 20))

    results: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    for doc in documents:
        case_id = _extract_case_id(doc)
        if case_id is None:
            continue

        case_id_key = str(case_id)
        if allowed_ids and case_id_key not in allowed_ids:
            continue
        if case_id_key in seen_ids:
            continue

        row = row_map.get(case_id_key, {})
        doc_text = _extract_document_text(doc)

        results.append(
            {
                "case_id": case_id,
                "case_title": row.get("case_title") or (getattr(doc, "metadata", {}) or {}).get("case_title"),
                "court": row.get("court") or (getattr(doc, "metadata", {}) or {}).get("court"),
                "year": row.get("year") or (getattr(doc, "metadata", {}) or {}).get("year"),
                "short_snippet": row.get("short_snippet") or doc_text[:300],
            }
        )
        seen_ids.add(case_id_key)

        if len(results) >= limit:
            break

    if not results:
        for row in metadata_rows[:limit]:
            results.append(
                {
                    "case_id": row.get("case_id"),
                    "case_title": row.get("case_title"),
                    "court": row.get("court"),
                    "year": row.get("year"),
                    "short_snippet": (row.get("short_snippet") or row.get("full_text") or "")[:300],
                }
            )

    retrieved_ids = [item.get("case_id") for item in results if item.get("case_id") is not None]
    log_search_event(db=db, user_id=user_id, query=structured_query, retrieved_case_ids=retrieved_ids)

    return {
        "query": structured_query,
        "results": results,
        "count": len(results),
    }


def get_case_view(
    db: Any,
    case_id: Any,
    summary_chain: Any,
    structured_report_chain: Any,
) -> Dict[str, Any]:
    """Fetch full case and generate summary/report for case-view phase."""
    case_cfg = get_case_table_config(db)

    select_fields = [
        f"c.{quote_ident(case_cfg['id_col'])} AS case_id",
        (
            f"c.{quote_ident(case_cfg['title_col'])} AS case_title"
            if case_cfg.get("title_col")
            else "NULL AS case_title"
        ),
        (
            f"c.{quote_ident(case_cfg['text_col'])} AS full_text"
            if case_cfg.get("text_col")
            else "NULL AS full_text"
        ),
        (
            f"c.{quote_ident(case_cfg['snippet_col'])} AS short_snippet"
            if case_cfg.get("snippet_col")
            else "NULL AS short_snippet"
        ),
        (
            f"c.{quote_ident(case_cfg['pdf_col'])} AS pdf_path"
            if case_cfg.get("pdf_col")
            else "NULL AS pdf_path"
        ),
    ]

    sql = (
        f"SELECT {', '.join(select_fields)} "
        f"FROM {quote_ident(case_cfg['table'])} c "
        f"WHERE c.{quote_ident(case_cfg['id_col'])} = :case_id "
        f"LIMIT 1"
    )
    row = db.execute(text(sql), {"case_id": case_id}).mappings().first()

    if not row:
        raise ValueError(f"Case not found for case_id={case_id}")

    pdf_path = row.get("pdf_path")
    case_title = row.get("case_title") or ""
    if not case_title and pdf_path:
        case_title = Path(str(pdf_path)).stem.replace("_", " ").strip()
    if not case_title:
        case_title = "Not Specified"

    case_text = row.get("full_text") or row.get("short_snippet") or ""
    if not case_text and pdf_path:
        resolved_pdf_path = str(pdf_path)
        if not Path(resolved_pdf_path).is_absolute():
            settings = get_settings()
            resolved_pdf_path = str(Path(settings.CASEFILES_ROOT_DIR).parent / resolved_pdf_path)
        case_text = extract_text_from_pdf(resolved_pdf_path)

    payload = {
        "case_id": row.get("case_id"),
        "case_title": case_title,
        "case_text": case_text[:8000] if case_text else "",
    }

    summary_raw = _invoke_with_timeout(lambda: _call_chain(summary_chain, payload), timeout_seconds=25)
    report_raw = _invoke_with_timeout(
        lambda: _call_chain(structured_report_chain, payload),
        timeout_seconds=30,
    )

    summary = _parse_chain_output(summary_raw)
    report = _parse_chain_output(report_raw)

    if isinstance(summary, dict):
        summary = json.dumps(summary)
    if summary is None or not str(summary).strip():
        summary = _fallback_summary_from_text(case_text)

    if not isinstance(report, dict):
        report = _fallback_structured_report(case_text, case_title)

    key_points: List[str] = []
    report_key_principles = report.get("key_principles") if isinstance(report, dict) else None
    if isinstance(report_key_principles, list):
        key_points = [str(item).strip() for item in report_key_principles if str(item).strip()]
    if not key_points and case_text.strip():
        keyword_result = _invoke_with_timeout(
            lambda: extract_legal_keywords(case_text[:8000]),
            timeout_seconds=20,
        )
        if isinstance(keyword_result, list):
            key_points = [str(item).strip() for item in keyword_result if str(item).strip()][:12]
    if not key_points:
        key_points = _fallback_keywords(case_text)
    if not key_points:
        key_points = ["Not Specified"]

    return {
        "case_title": case_title,
        "summary": summary,
        "structured_report": report,
        "pdf_path": pdf_path,
        "key_points": key_points,
    }
