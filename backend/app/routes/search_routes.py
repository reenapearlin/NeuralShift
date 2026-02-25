"""Route layer for retrieval search and case-view generation endpoints."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.search_service import get_case_view, search_cases

try:
    from app.core import dependencies as core_dependencies
except Exception:
    core_dependencies = None


router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    """Structured input payload used for retrieval-only search listing."""

    user_id: Optional[int] = Field(default=None)
    cheque_amount: Optional[float] = Field(default=None)
    notice_period: Optional[int] = Field(default=None)
    dishonor_reason: Optional[str] = Field(default=None)
    nature_of_debt: Optional[str] = Field(default=None)
    court: Optional[str] = Field(default=None)
    year: Optional[int] = Field(default=None)
    bench: Optional[str] = Field(default=None)
    file_upload_flag: Optional[bool] = Field(default=None)


class SearchResultsResponse(BaseModel):
    """Structured JSON response for search listing results."""

    query: str
    count: int
    results: list[Dict[str, Any]]


class CaseViewResponse(BaseModel):
    """Structured JSON response for single-case generated analysis."""

    summary: str
    structured_report: Dict[str, Any]
    pdf_path: Optional[str] = None


def _missing_dependency(name: str) -> Callable[[], Any]:
    """Return a fallback dependency that raises an explicit server error."""

    def _raiser() -> Any:
        raise HTTPException(status_code=500, detail=f"Missing dependency provider: {name}")

    return _raiser


def _resolve_dependency(name: str) -> Callable[..., Any]:
    """Resolve dependency providers dynamically from app.core.dependencies."""
    if core_dependencies is None:
        return _missing_dependency(name)

    provider = getattr(core_dependencies, name, None)
    if callable(provider):
        return provider

    return _missing_dependency(name)


get_db = _resolve_dependency("get_db")
get_retriever = _resolve_dependency("get_retriever")
get_summary_chain = _resolve_dependency("get_summary_chain")
get_structured_report_chain = _resolve_dependency("get_structured_report_chain")


@router.post("", response_model=SearchResultsResponse)
def search_cases_route(
    payload: SearchRequest,
    limit: int = Query(default=10, ge=1, le=50),
    db: Any = Depends(get_db),
    retriever: Any = Depends(get_retriever),
) -> Dict[str, Any]:
    """Run retrieval-only search: metadata filter first, then vector retriever."""
    try:
        return search_cases(
            db=db,
            retriever=retriever,
            search_input=payload.model_dump(exclude_none=True),
            user_id=payload.user_id,
            limit=limit,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.get("/cases/{case_id}", response_model=CaseViewResponse)
def case_view_route(
    case_id: int,
    db: Any = Depends(get_db),
    summary_chain: Any = Depends(get_summary_chain),
    structured_report_chain: Any = Depends(get_structured_report_chain),
) -> Dict[str, Any]:
    """Run case-view generation flow: full-case fetch + summary/report chains."""
    try:
        return get_case_view(
            db=db,
            case_id=case_id,
            summary_chain=summary_chain,
            structured_report_chain=structured_report_chain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Case view failed: {exc}") from exc
