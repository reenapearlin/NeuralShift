from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
import shutil

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.models.casefile import CaseFile
from app.models.metadata import CaseMetadata
from app.models.enums import CaseStatus
from app.utils.file_parser import extract_text_from_pdf


def _safe_filename(filename: str) -> str:
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower() or ".pdf"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
    if not cleaned:
        cleaned = "casefile"
    return f"{cleaned}{suffix}"


def save_uploaded_file(file: UploadFile, db: Session, uploaded_by: int) -> dict[str, str | int]:
    """Save uploaded PDF and create casefile record with relative file path."""

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")

    settings = get_settings()
    storage_dir = Path(settings.CASEFILES_ROOT_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_filename(file.filename)
    target = storage_dir / safe_name

    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d%H%M%S")
        target = storage_dir / f"{target.stem}_{stamp}{target.suffix}"

    try:
        with target.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        relative_path = f"casefiles/{target.name}"
        case_title = Path(file.filename).stem.replace("_", " ").strip()

        extracted_text = extract_text_from_pdf(str(target))

        new_case = CaseFile(
            case_title=case_title,
            filename=target.name,
            file_path=relative_path,
            extracted_text=extracted_text or None,
            status=CaseStatus.PENDING,
            uploaded_by=uploaded_by,
        )

        db.add(new_case)
        db.commit()
        db.refresh(new_case)

        metadata_rows = [
            CaseMetadata(casefile_id=new_case.id, meta_key="file_path", meta_value=relative_path),
            CaseMetadata(casefile_id=new_case.id, meta_key="filename", meta_value=target.name),
            CaseMetadata(casefile_id=new_case.id, meta_key="status", meta_value=new_case.status.value),
            CaseMetadata(casefile_id=new_case.id, meta_key="uploaded_by", meta_value=str(uploaded_by)),
            CaseMetadata(
                casefile_id=new_case.id,
                meta_key="text_chars",
                meta_value=str(len(extracted_text or "")),
            ),
        ]
        db.add_all(metadata_rows)
        db.commit()

        return {
            "case_id": new_case.id,
            "case_title": new_case.case_title,
            "file_path": new_case.file_path,
            "status": new_case.status.value,
        }
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="File upload failed.") from exc
