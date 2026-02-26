import os
from datetime import datetime
from reportlab.lib.units import inch
from fastapi import HTTPException
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.orm import Session

from app.models.casefile import CaseFile
from app.models.enums import CaseStatus
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


def generate_pdf_report(case_id: int, db: Session) -> dict[str, str]:

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

    return {"report_file": file_name, "download_path": f"/reports/{file_name}"}
