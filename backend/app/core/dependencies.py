from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.security import verify_access_token
from app.models.enums import UserRole
from app.models.user import User
from app.rag.config import RAGConfigError
from app.rag.embeddings import get_embedding_model
from app.rag.rag_chain import generate_structured_report, generate_summary
from app.rag.vector_store import create_or_load_index

from functools import lru_cache
from typing import Any, Mapping


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = verify_access_token(token)
    user_id = payload.get("sub")

    try:
        parsed_user_id = int(user_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        ) from exc

    user = db.query(User).filter(User.id == parsed_user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


class _RetrieverAdapter:
    """Adapter that exposes retriever-like methods expected by search service."""

    def __init__(self, vector_store: Any) -> None:
        self._vector_store = vector_store

    def get_relevant_documents(self, query: str, k: int = 5) -> list[Any]:
        if self._vector_store is None:
            return []
        return self._vector_store.similarity_search(query, k=k)


class _SummaryChainAdapter:
    """Adapter that exposes invoke(payload) using RAG summary generator."""

    def invoke(self, payload: Mapping[str, Any]) -> str:
        case_text = str(payload.get("case_text", "")).strip()
        if not case_text:
            return ""
        return generate_summary(case_text)


class _StructuredReportChainAdapter:
    """Adapter that exposes invoke(payload) using RAG report generator."""

    def invoke(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        case_text = str(payload.get("case_text", "")).strip()
        if not case_text:
            return {
                "case_title": "Not Specified",
                "court": "Not Specified",
                "legal_issue": "Not Specified",
                "relevant_sections": ["Not Specified"],
                "limitation_analysis": "Not Specified",
                "penalty": "Not Specified",
                "judgement": "Not Specified",
                "key_principles": ["Not Specified"],
            }
        return generate_structured_report(case_text)


@lru_cache(maxsize=1)
def _get_cached_retriever_adapter() -> _RetrieverAdapter:
    """Build and cache retriever adapter from persisted FAISS index."""
    embedding_model = get_embedding_model()
    vector_store = create_or_load_index(embedding_model=embedding_model)
    return _RetrieverAdapter(vector_store=vector_store)


@lru_cache(maxsize=1)
def _get_cached_summary_chain() -> _SummaryChainAdapter:
    """Build and cache summary chain adapter."""
    return _SummaryChainAdapter()


@lru_cache(maxsize=1)
def _get_cached_structured_report_chain() -> _StructuredReportChainAdapter:
    """Build and cache structured report chain adapter."""
    return _StructuredReportChainAdapter()


def get_retriever() -> _RetrieverAdapter:
    try:
        return _get_cached_retriever_adapter()
    except RAGConfigError:
        # Degrade gracefully when FAISS index is missing/corrupted.
        return _RetrieverAdapter(vector_store=None)


def get_summary_chain() -> _SummaryChainAdapter:
    try:
        return _get_cached_summary_chain()
    except RAGConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Summary chain unavailable: {exc}",
        ) from exc


def get_structured_report_chain() -> _StructuredReportChainAdapter:
    try:
        return _get_cached_structured_report_chain()
    except RAGConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Structured report chain unavailable: {exc}",
        ) from exc
