from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.dependencies import require_admin
from app.models.casefile import CaseFile
from app.models.user import User
from app.rag.rag_chain import index_document

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/protected")
def admin_protected_route(current_user: User = Depends(require_admin)) -> dict[str, str]:
    return {"message": f"Welcome admin {current_user.full_name}"}


@router.put("/approve/{case_id}")
def approve_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if str(case.status) == "APPROVED":
        return {"message": "Case already approved"}

    case.status = "APPROVED"
    db.commit()

    index_document(
        file_path=case.file_path,
        metadata={"case_id": case.id, "filename": getattr(case, "filename", None)},
    )

    return {
        "message": "Case approved successfully",
        "case_id": case.id,
        "status": str(case.status),
    }


@router.put("/reject/{case_id}")
def reject_case(
    case_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = "REJECTED"
    db.commit()

    return {
        "message": "Case rejected successfully",
        "case_id": case.id,
        "status": str(case.status),
    }
