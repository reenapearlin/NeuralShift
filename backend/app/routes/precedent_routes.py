"""API routes for dynamic web-scraped precedent search."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.precedent_scraper import fetch_pdf_bytes
from app.services.precedent_service import get_precedent_view, search_precedents


router = APIRouter(prefix="/precedents", tags=["Precedents"])

try:  # pragma: no cover - optional runtime dependency
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None


class PrecedentResult(BaseModel):
    title: str
    url: str
    snippet: str
    score: float
    keywords: list[str] = Field(default_factory=list)


class PrecedentSearchResponse(BaseModel):
    query: str
    results: list[PrecedentResult] = Field(default_factory=list)


class PrecedentViewResponse(BaseModel):
    case_title: str
    summary: str
    structured_report: dict[str, Any]
    pdf_path: Optional[str] = None
    key_points: list[str] = Field(default_factory=list)
    highlighted_keywords: list[str] = Field(default_factory=list)
    source_url: Optional[str] = None


@router.get("/search", response_model=PrecedentSearchResponse)
def search_precedents_route(
    q: str = Query(..., min_length=2, description="Legal precedent search query."),
    top_n: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return search_precedents(db=db, query=q, top_n=top_n)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Precedent search failed: {exc}") from exc


@router.get("/view", response_model=PrecedentViewResponse)
def view_precedent_route(
    url: str = Query(..., min_length=8),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    try:
        return get_precedent_view(db=db, url=url)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Precedent view failed: {exc}") from exc


@router.get("/preview")
def preview_precedent_pdf_route(
    url: str = Query(..., min_length=8),
) -> Response:
    try:
        resolved_url, pdf_bytes = fetch_pdf_bytes(url=url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Precedent preview failed: {exc}") from exc

    filename = (resolved_url.split("/")[-1] or "precedent.pdf").split("?")[0]
    if not filename.lower().endswith(".pdf"):
        filename = f"{filename}.pdf"
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": "private, max-age=300",
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


def _normalize_keyword(value: str) -> str:
    return " ".join((value or "").split()).strip()


def _keyword_variants(keyword: str) -> list[str]:
    cleaned = _normalize_keyword(keyword)
    if not cleaned:
        return []

    variants: list[str] = [cleaned]
    import re

    for pattern in (
        r"\bSection\s+\d+[A-Za-z0-9()/-]*",
        r"\bArticle\s+\d+[A-Za-z0-9()/-]*",
        r"\bChapter\s+[IVXLC]+\b",
    ):
        for hit in re.findall(pattern, cleaned, flags=re.IGNORECASE):
            term = _normalize_keyword(hit)
            if term:
                variants.append(term)

    seen: set[str] = set()
    deduped: list[str] = []
    for item in variants:
        key = item.lower()
        if len(item) < 3 or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _highlight_pdf_bytes(pdf_bytes: bytes, keywords: list[str]) -> tuple[bytes, int]:
    if not keywords or fitz is None:
        return pdf_bytes, 1

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return pdf_bytes, 1

    max_hits_per_term = 30
    highlight_colors = [
        (1.0, 0.95, 0.35),  # yellow
        (0.65, 0.90, 1.0),  # blue
        (0.75, 1.0, 0.75),  # green
        (1.0, 0.80, 0.80),  # red
    ]

    first_match_page = 1
    found_first_match = False
    try:
        for idx, keyword in enumerate(keywords):
            variants = _keyword_variants(keyword)
            if not variants:
                continue
            color = highlight_colors[idx % len(highlight_colors)]

            for page in doc:
                total_hits = 0
                for variant in variants:
                    if total_hits >= max_hits_per_term:
                        break
                    try:
                        quads = page.search_for(variant, quads=True)
                    except Exception:
                        quads = []
                    if quads and not found_first_match:
                        first_match_page = int(page.number) + 1
                        found_first_match = True
                    for quad in quads:
                        annot = page.add_highlight_annot(quad)
                        if annot is None:
                            continue
                        annot.set_colors(stroke=color)
                        annot.set_opacity(0.35)
                        annot.update()
                        total_hits += 1
                        if total_hits >= max_hits_per_term:
                            break
        return doc.tobytes(), first_match_page
    except Exception:
        return pdf_bytes, 1
    finally:
        doc.close()


@router.get("/preview/highlight")
def preview_highlighted_precedent_pdf_route(
    url: str = Query(..., min_length=8),
    keywords: list[str] = Query(default_factory=list),
) -> Response:
    try:
        resolved_url, pdf_bytes = fetch_pdf_bytes(url=url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Precedent highlighted preview failed: {exc}") from exc

    cleaned_keywords = [_normalize_keyword(value) for value in keywords if _normalize_keyword(value)]
    highlighted_pdf, first_match_page = _highlight_pdf_bytes(
        pdf_bytes=pdf_bytes,
        keywords=cleaned_keywords[:12],
    )

    filename = (resolved_url.split("/")[-1] or "precedent.pdf").split("?")[0]
    if not filename.lower().endswith(".pdf"):
        filename = f"{filename}.pdf"
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "Cache-Control": "private, max-age=120",
        "X-First-Match-Page": str(max(first_match_page, 1)),
    }
    return Response(content=highlighted_pdf, media_type="application/pdf", headers=headers)
