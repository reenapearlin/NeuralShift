import os
import shutil
from datetime import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.utils.file_parser import extract_text_from_pdf
from app.models.casefile import CaseFile


# Safe base path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_FOLDER = os.path.join(BASE_DIR, "storage")


def save_uploaded_file(file: UploadFile, db: Session):
    """
    Save uploaded file, extract text, and store metadata in DB.
    """

    # Allow only PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed.")

    # Auto create storage folder
    os.makedirs(STORAGE_FOLDER, exist_ok=True)

    # Unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(STORAGE_FOLDER, safe_filename)

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract text
        extracted_text = extract_text_from_pdf(file_path)

        # Create DB entry
        new_case = CaseFile(
            filename=safe_filename,
            file_path=file_path,
            extracted_text=extracted_text,
            status="PENDING"
        )

        db.add(new_case)
        db.commit()
        db.refresh(new_case)

        return {
            "case_id": new_case.id,
            "filename": new_case.filename,
            "status": new_case.status
        }

    except Exception:
        raise HTTPException(status_code=500, detail="File upload failed.")