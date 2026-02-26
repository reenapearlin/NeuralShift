from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.models.casefile import CaseFile

# This function should exist from Member 3
from app.rag.rag_chain import ingest_document

router = APIRouter(prefix="/admin", tags=["Admin"])


# ✅ APPROVE CASE
@router.put("/approve/{case_id}")
def approve_case(case_id: int, db: Session = Depends(get_db)):

    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status == "APPROVED":
        return {"message": "Case already approved"}

    # Change status
    case.status = "APPROVED"
    db.commit()

    # 🔥 Trigger RAG ingestion (ONLY after approval)
    ingest_document(
        text=case.extracted_text,
        metadata={"case_id": case.id, "filename": case.filename}
    )

    return {
        "message": "Case approved successfully",
        "case_id": case.id,
        "status": case.status
    }


# ❌ REJECT CASE
@router.put("/reject/{case_id}")
def reject_case(case_id: int, db: Session = Depends(get_db)):

    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = "REJECTED"
    db.commit()

    return {
        "message": "Case rejected successfully",
        "case_id": case.id,
        "status": case.status
    }