"""Precedent search orchestration using scraper cache + embedding ranking."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import math
import re
from threading import Lock
from typing import Any, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.scraped_case import ScrapedCase
from app.rag.rag_chain import extract_legal_keywords, generate_structured_report, generate_summary
from app.rag.embeddings import get_embedding_model
from app.services.precedent_scraper import get_or_scrape, scrape_case, search_case_links

_PRECEDENT_VIEW_CACHE: dict[str, tuple[datetime, dict[str, Any]]] = {}
_PRECEDENT_VIEW_CACHE_LOCK = Lock()


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _mean_vector(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    length = len(vectors[0])
    totals = [0.0] * length
    for vec in vectors:
        if len(vec) != length:
            continue
        for idx, value in enumerate(vec):
            totals[idx] += value
    count = max(len(vectors), 1)
    return [value / count for value in totals]


def _chunk_text(content: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_text((content or "").strip())
    return [chunk for chunk in chunks if chunk.strip()]


def _build_snippet(text: str, max_len: int) -> str:
    cleaned = " ".join((text or "").split())
    return cleaned[:max_len]


def _extract_precedent_keywords(text: str, limit: int = 6) -> list[str]:
    normalized = (text or "").lower()
    patterns = [
        r"section\s+\d+[a-z]?",
        r"negotiable instruments act",
        r"section\s+138",
        r"dishonou?r(?:ed|)",
        r"cheque(?:\s+bounce)?",
        r"statutory notice",
        r"legally enforceable debt",
        r"presumption",
        r"limitation(?:\s+period)?",
        r"burden of proof",
    ]
    seen: set[str] = set()
    found: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, normalized, flags=re.IGNORECASE):
            term = re.sub(r"\s+", " ", match).strip()
            if not term:
                continue
            key = term.lower()
            if key in seen:
                continue
            seen.add(key)
            found.append(term.title())
            if len(found) >= limit:
                return found
    return found


def _fallback_queries(query: str) -> list[str]:
    base = (query or "").strip()
    if not base:
        return ["section 138 cheque bounce"]

    queries: list[str] = [base]
    simplified = re.sub(
        r"\b(compliant|non-compliant|within limitation|time barred|all courts|all jurisdictions|all rankings)\b",
        " ",
        base,
        flags=re.IGNORECASE,
    )
    simplified = re.sub(r"\s+", " ", simplified).strip()
    if simplified and simplified.lower() != base.lower():
        queries.append(simplified)

    if "section 138" not in simplified.lower():
        queries.append(f"section 138 {simplified}".strip())
    queries.append("section 138 cheque bounce")

    deduped: list[str] = []
    seen: set[str] = set()
    for item in queries:
        key = item.lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _fallback_summary(text: str) -> str:
    compact = " ".join((text or "").split())
    if not compact:
        return "Facts: Not Specified\nLegal Issue: Not Specified\nCourt Reasoning: Not Specified\nFinal Judgment: Not Specified"
    head = compact[:900]
    return (
        f"Facts: {head[:260]}\n"
        f"Legal Issue: {head[260:460] or 'Not Specified'}\n"
        f"Court Reasoning: {head[460:680] or 'Not Specified'}\n"
        f"Final Judgment: {head[680:900] or 'Not Specified'}"
    )


def _fallback_report(case_title: str, text: str) -> dict[str, Any]:
    sections = sorted(set(re.findall(r"section\s+\d+[a-z]?", text, flags=re.IGNORECASE)))
    if not sections:
        sections = ["Not Specified"]
    principles = _extract_precedent_keywords(text, limit=8) or ["Not Specified"]
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


def _minimal_precedent_payload(url: str, title: str = "Web Precedent") -> dict[str, Any]:
    summary = (
        "Facts: Live precedent page is being fetched.\n"
        "Legal Issue: Not Specified\n"
        "Court Reasoning: Not Specified\n"
        "Final Judgment: Not Specified"
    )
    report = _fallback_report(title, "")
    return {
        "case_title": title,
        "summary": summary,
        "structured_report": report,
        "pdf_path": url,
        "key_points": ["Not Specified"],
        "highlighted_keywords": ["Not Specified"],
        "source_url": url,
    }


def _ensure_case_embedding(raw_text: str, existing: Optional[list[float]], embedding_model: Any) -> list[float]:
    if existing:
        return [float(x) for x in existing]
    chunks = _chunk_text(raw_text)
    if not chunks:
        return []
    # Cap chunk embedding count so one slow page does not block the whole search.
    chunk_vectors = embedding_model.embed_documents(chunks[:6])
    return _mean_vector(chunk_vectors)


def _generation_context(text: str, max_chars: int) -> str:
    compact = " ".join((text or "").split())
    return compact[:max_chars]


def _derive_pdf_path(source_url: str, scraped_pdf_url: Optional[str]) -> str:
    if scraped_pdf_url:
        return scraped_pdf_url
    if "/doc/" in (source_url or ""):
        return f"{source_url.rstrip('/')}/?type=pdf"
    return source_url


def _get_cached_precedent_view(url: str) -> Optional[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    with _PRECEDENT_VIEW_CACHE_LOCK:
        cached = _PRECEDENT_VIEW_CACHE.get(url)
        if cached is None:
            return None
        expires_at, payload = cached
        if expires_at <= now:
            _PRECEDENT_VIEW_CACHE.pop(url, None)
            return None
        return payload


def _set_cached_precedent_view(url: str, payload: dict[str, Any]) -> None:
    settings = get_settings()
    ttl_seconds = max(int(settings.PRECEDENT_VIEW_CACHE_SECONDS), 1)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    with _PRECEDENT_VIEW_CACHE_LOCK:
        _PRECEDENT_VIEW_CACHE[url] = (expires_at, payload)


def _generate_view_outputs(text_for_generation: str) -> tuple[Optional[str], Optional[dict[str, Any]], Optional[list[str]]]:
    def _safe_summary() -> Optional[str]:
        try:
            return generate_summary(text_for_generation)
        except Exception:
            return None

    def _safe_report() -> Optional[dict[str, Any]]:
        try:
            value = generate_structured_report(text_for_generation)
            return value if isinstance(value, dict) else None
        except Exception:
            return None

    def _safe_keywords() -> Optional[list[str]]:
        try:
            value = extract_legal_keywords(text_for_generation)
            return value if isinstance(value, list) else None
        except Exception:
            return None

    with ThreadPoolExecutor(max_workers=3) as executor:
        summary_future = executor.submit(_safe_summary)
        report_future = executor.submit(_safe_report)
        keywords_future = executor.submit(_safe_keywords)
        return (
            summary_future.result(),
            report_future.result(),
            keywords_future.result(),
        )


def search_precedents(db: Session, query: str, top_n: Optional[int] = None) -> dict[str, Any]:
    """Search, scrape/cache, embed, and rank precedents for a legal query."""
    settings = get_settings()
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return {"query": "", "results": []}

    top_limit = top_n or settings.PRECEDENT_SEARCH_TOP_N
    links: list[str] = []
    for candidate_query in _fallback_queries(cleaned_query):
        links = search_case_links(candidate_query)
        if links:
            break
    if not links:
        return {"query": cleaned_query, "results": []}

    embedding_model = get_embedding_model()
    query_vector = embedding_model.embed_query(cleaned_query)

    ranked: list[dict[str, Any]] = []
    max_urls_to_process = max(top_limit * 2, top_limit)
    for url in links[:max_urls_to_process]:
        try:
            row = get_or_scrape(url=url, db=db)
            case_vector = _ensure_case_embedding(
                raw_text=row.raw_text,
                existing=row.embeddings,
                embedding_model=embedding_model,
            )
            if case_vector and row.embeddings != case_vector:
                row.embeddings = case_vector
                db.commit()
            score = _cosine_similarity(query_vector, case_vector)
            ranked.append(
                {
                    "title": row.title or "Untitled Precedent",
                    "url": row.url,
                    "snippet": _build_snippet(row.raw_text, settings.PRECEDENT_SNIPPET_CHARS),
                    "score": round(float(score), 6),
                    "keywords": _extract_precedent_keywords(row.raw_text),
                }
            )
        except Exception:
            # Skip unreachable/invalid URLs and continue ranking viable results.
            continue

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {"query": cleaned_query, "results": ranked[:top_limit]}


def get_precedent_view(db: Session, url: str) -> dict[str, Any]:
    """Generate full precedent view payload with RAG summary/report/keywords."""
    cleaned_url = (url or "").strip()
    if not cleaned_url:
        return {
            "case_title": "Not Specified",
            "summary": "",
            "structured_report": {},
            "pdf_path": None,
            "key_points": ["Not Specified"],
            "highlighted_keywords": ["Not Specified"],
            "source_url": "",
        }

    cached_payload = _get_cached_precedent_view(cleaned_url)
    if cached_payload is not None:
        return cached_payload

    row = db.query(ScrapedCase).filter(ScrapedCase.url == cleaned_url).first()
    scraped_page = None
    should_scrape = row is None or not (row.raw_text or "").strip()
    if should_scrape:
        try:
            scraped_page = scrape_case(cleaned_url)
        except Exception:
            scraped_page = None

    if row is None and scraped_page is None:
        try:
            row = get_or_scrape(url=cleaned_url, db=db)
        except Exception:
            return _minimal_precedent_payload(cleaned_url)
    elif row is None and scraped_page is not None:
        row = ScrapedCase(
            url=scraped_page.url,
            title=scraped_page.title,
            raw_text=scraped_page.raw_text,
            embeddings=None,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    elif row is not None and scraped_page is not None:
        if (scraped_page.raw_text or "").strip():
            row.raw_text = scraped_page.raw_text
        if (scraped_page.title or "").strip():
            row.title = scraped_page.title
        db.commit()
        db.refresh(row)

    case_text = ((scraped_page.pdf_text if scraped_page else None) or row.raw_text or "").strip()

    if not case_text:
        return _minimal_precedent_payload(row.url, row.title or "Web Precedent")

    settings = get_settings()
    reduced_text = _generation_context(case_text, settings.PRECEDENT_VIEW_MAX_CONTEXT_CHARS)
    summary, structured_report, keywords = _generate_view_outputs(reduced_text)

    if not isinstance(summary, str) or not summary.strip():
        summary = _fallback_summary(case_text)
    if not isinstance(structured_report, dict):
        structured_report = _fallback_report(row.title or "Not Specified", case_text)

    if not isinstance(keywords, list) or not keywords:
        keywords = ["Not Specified"]

    case_title = row.title or structured_report.get("case_title") or "Not Specified"
    highlighted_keywords = keywords[:8]
    payload = {
        "case_title": case_title,
        "summary": summary,
        "structured_report": structured_report,
        "pdf_path": _derive_pdf_path(row.url, scraped_page.pdf_url if scraped_page else None),
        "key_points": highlighted_keywords,
        "highlighted_keywords": highlighted_keywords,
        "source_url": row.url,
    }
    _set_cached_precedent_view(cleaned_url, payload)
    return payload
