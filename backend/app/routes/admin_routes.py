from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.config.settings import get_settings
from app.core.dependencies import require_admin
from app.models.casefile import CaseFile
from app.models.enums import CaseStatus
from app.models.user import User

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
