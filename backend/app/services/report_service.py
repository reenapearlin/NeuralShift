import os
from datetime import datetime
from reportlab.lib.units import inch
from fastapi import HTTPException
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.orm import Session

from app.models.casefile import CaseFile
from app.models.enums import CaseStatus
from app.models.enums import UserRole
from app.models.report import Report
from app.models.user import User
from app.rag.rag_chain import generate_structured_report, generate_summary


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")


def _generate_case_report_payload(case_text: str) -> dict[str, str]:
    """Build report sections using current RAG functions."""
    summary = generate_summary(case_text)
    structured = generate_structured_report(case_text)

    legal_points = ", ".join(structured.get("key_principles", []) or ["Not Specified"])
    risk_analysis = structured.get("limitation_analysis", "Not Specified")
    if not risk_analysis or risk_analysis == "Not Specified":
        risk_analysis = (
            "Not Specified in source judgement. Review liability, notice timeline, "
            "and enforceable debt evidence."
        )

    return {
        "summary": summary,
        "legal_points": legal_points,
        "risk_analysis": str(risk_analysis),
    }


def _resolve_report_generator(case: CaseFile, db: Session) -> int:
    if case.reviewed_by:
        return int(case.reviewed_by)
    if case.uploaded_by:
        return int(case.uploaded_by)
    admin = db.query(User).filter(User.role == UserRole.ADMIN).order_by(User.id.asc()).first()
    if admin:
        return int(admin.id)
    any_user = db.query(User).order_by(User.id.asc()).first()
    if any_user:
        return int(any_user.id)
    raise HTTPException(status_code=400, detail="No user available to assign report generator.")


def generate_pdf_report(case_id: int, db: Session) -> dict[str, str | int]:

    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status != CaseStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Case not approved yet")

    ai_output = _generate_case_report_payload(case.extracted_text or "")

    os.makedirs(REPORT_FOLDER, exist_ok=True)

    file_name = f"report_case_{case_id}.pdf"
    file_path = os.path.join(REPORT_FOLDER, file_name)

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Case Report</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"<b>Case ID:</b> {case.id}", styles["Normal"]))
    elements.append(
        Paragraph(f"<b>Filename:</b> {case.filename or 'Not Specified'}", styles["Normal"])
    )
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("<b>Summary:</b>", styles["Heading2"]))
    elements.append(Paragraph(ai_output["summary"], styles["Normal"]))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("<b>Legal Points:</b>", styles["Heading2"]))
    elements.append(Paragraph(ai_output["legal_points"], styles["Normal"]))
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph("<b>Risk Analysis:</b>", styles["Heading2"]))
    elements.append(Paragraph(ai_output["risk_analysis"], styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(
        Paragraph(
            f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            styles["Normal"],
        )
    )

    doc.build(elements)

    report_row = Report(
        casefile_id=case.id,
        generated_by=_resolve_report_generator(case=case, db=db),
        title=f"Case Report #{case.id}",
        content=(
            f"Summary:\n{ai_output['summary']}\n\n"
            f"Legal Points:\n{ai_output['legal_points']}\n\n"
            f"Risk Analysis:\n{ai_output['risk_analysis']}"
        ),
    )
    db.add(report_row)
    db.commit()
    db.refresh(report_row)

    return {
        "report_id": report_row.id,
        "report_file": file_name,
        "download_path": f"/reports/{file_name}",
    }
