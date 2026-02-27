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
