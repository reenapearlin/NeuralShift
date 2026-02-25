from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.report_service import generate_pdf_report

router = APIRouter(prefix="/report", tags=["Report"])


@router.get("/{case_id}")
def create_report(case_id: int, db: Session = Depends(get_db)):
    result = generate_pdf_report(case_id, db)
    return {
        "message": "Report generated successfully",
        "data": result
    }