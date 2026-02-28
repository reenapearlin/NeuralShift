from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import get_settings
from app.core.dependencies import require_admin
from app.models.casefile import CaseFile
from app.models.enums import CaseStatus, UserRole
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/protected")
def admin_protected_route(current_user: User = Depends(require_admin)) -> dict[str, str]:
    return {"message": f"Welcome admin {current_user.full_name}"}


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    total_cases = db.query(func.count(CaseFile.id)).scalar() or 0
    pending_cases = db.query(func.count(CaseFile.id)).filter(CaseFile.status == CaseStatus.PENDING).scalar() or 0
    approved_cases = db.query(func.count(CaseFile.id)).filter(CaseFile.status == CaseStatus.APPROVED).scalar() or 0
    rejected_cases = db.query(func.count(CaseFile.id)).filter(CaseFile.status == CaseStatus.REJECTED).scalar() or 0
    total_lawyers = db.query(func.count(User.id)).filter(User.role == UserRole.LAWYER).scalar() or 0

    return {
        "total_lawyers": total_lawyers,
        "total_cases": total_cases,
        "pending_cases": pending_cases,
        "approved_cases": approved_cases,
        "rejected_cases": rejected_cases,
    }


@router.get("/cases")
def list_cases(
    status: Optional[CaseStatus] = Query(default=CaseStatus.PENDING),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = db.query(CaseFile)
    if status is not None:
        query = query.filter(CaseFile.status == status)

    rows = query.order_by(CaseFile.created_at.desc()).limit(100).all()
    return {
        "count": len(rows),
        "items": [
            {
                "id": row.id,
                "case_title": row.case_title,
                "file_path": row.file_path,
                "status": row.status.value,
                "uploaded_by": row.uploaded_by,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


@router.get("/lawyers")
def list_lawyers(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    rows = (
        db.query(User)
        .filter(User.role == UserRole.LAWYER)
        .order_by(User.created_at.desc())
        .limit(500)
        .all()
    )
    return {
        "count": len(rows),
        "items": [
            {
                "id": row.id,
                "full_name": row.full_name,
                "email": row.email,
                "is_active": bool(row.is_active),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ],
    }


@router.put("/approve/{case_id}")
def approve_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status == CaseStatus.APPROVED:
        return {"message": "Case already approved"}

    case.status = CaseStatus.APPROVED
    db.commit()

    indexed = False
    indexing_error = None
    try:
        from app.rag.rag_chain import index_document

        settings = get_settings()
        file_path = case.file_path
        if not Path(file_path).is_absolute():
            file_path = str(Path(settings.CASEFILES_ROOT_DIR).parent / file_path)

        index_document(file_path=file_path, metadata={"case_id": case.id})
        indexed = True
    except Exception as exc:  # Keep approval successful even if indexing deps are unavailable.
        indexing_error = str(exc)

    response = {
        "message": "Case approved successfully",
        "case_id": case.id,
        "status": case.status.value,
        "indexed": indexed,
    }
    if indexing_error:
        response["indexing_error"] = indexing_error
    return response


@router.put("/reject/{case_id}")
def reject_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = CaseStatus.REJECTED
    db.commit()

    return {
        "message": "Case rejected successfully",
        "case_id": case.id,
        "status": case.status.value,
    }
