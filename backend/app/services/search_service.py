"""Service-layer logic for search and case-view flows in the LEGAL 138 AI system."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, Optional

from sqlalchemy import text

from app.utils.file_parser import append_file_context_to_query
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

    case_text = row.get("full_text") or row.get("short_snippet") or ""
    payload = {
        "case_id": row.get("case_id"),
        "case_title": row.get("case_title"),
        "case_text": case_text,
    }

    summary_raw = _call_chain(summary_chain, payload)
    report_raw = _call_chain(structured_report_chain, payload)

    summary = _parse_chain_output(summary_raw)
    report = _parse_chain_output(report_raw)

    if isinstance(summary, dict):
        summary = json.dumps(summary)
    if summary is None:
        summary = ""

    if not isinstance(report, dict):
        report = {"report": report}

    return {
        "summary": summary,
        "structured_report": report,
        "pdf_path": row.get("pdf_path"),
    }
