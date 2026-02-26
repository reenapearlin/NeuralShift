import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.casefile import CaseFile
from app.rag.rag_chain import generate_case_report


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = os.path.join(BASE_DIR, "reports")


def generate_pdf_report(case_id: int, db: Session):

    case = db.query(CaseFile).filter(CaseFile.id == case_id).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if case.status != "APPROVED":
        raise HTTPException(status_code=400, detail="Case not approved yet")

    # 🔥 Get AI generated report
    ai_output = generate_case_report(case.extracted_text)

    os.makedirs(REPORT_FOLDER, exist_ok=True)

    file_name = f"report_case_{case_id}.pdf"
    file_path = os.path.join(REPORT_FOLDER, file_name)

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>Case Report</b>", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph(f"<b>Case ID:</b> {case.id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Filename:</b> {case.filename}", styles["Normal"]))
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

    return {
        "report_file": file_name,
        "download_path": f"/reports/{file_name}"
    }