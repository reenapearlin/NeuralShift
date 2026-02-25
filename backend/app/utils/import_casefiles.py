import argparse
import shutil
from pathlib import Path
import re

from sqlalchemy.orm import Session

from app.config.database import SessionLocal
from app.config.settings import get_settings
from app.models import casefile, logs, metadata, report, user  # noqa: F401
from app.models.casefile import CaseFile
from app.models.enums import CaseStatus
from app.models.user import User


def slugify_filename(filename: str) -> str:
    stem = Path(filename).stem
    suffix = Path(filename).suffix.lower() or ".pdf"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._")
    if not cleaned:
        cleaned = "casefile"
    return f"{cleaned}{suffix}"


def resolve_uploader(db: Session, user_email: str) -> User:
    uploader = db.query(User).filter(User.email == user_email).first()
    if not uploader:
        raise ValueError(f"Uploader user not found for email: {user_email}")
    return uploader


def import_casefiles(source_dir: Path, uploader_email: str) -> None:
    settings = get_settings()
    storage_dir = Path(settings.CASEFILES_ROOT_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)

    if not source_dir.exists() or not source_dir.is_dir():
        raise ValueError(f"Source directory not found: {source_dir}")

    db: Session = SessionLocal()
    try:
        uploader = resolve_uploader(db, uploader_email)

        imported = 0
        skipped = 0
        copied = 0

        for src in sorted(source_dir.glob("*.pdf")):
            safe_name = slugify_filename(src.name)
            target = storage_dir / safe_name

            # Avoid filename collisions by appending numeric suffix.
            if target.exists() and target.stat().st_size != src.stat().st_size:
                base = target.stem
                suffix = target.suffix
                idx = 1
                while True:
                    candidate = storage_dir / f"{base}_{idx}{suffix}"
                    if not candidate.exists():
                        target = candidate
                        break
                    idx += 1

            relative_path = f"casefiles/{target.name}"

            exists = db.query(CaseFile).filter(CaseFile.file_path == relative_path).first()
            if exists:
                skipped += 1
                continue

            if not target.exists():
                shutil.copy2(src, target)
                copied += 1

            case_title = src.stem.replace("_", " ").strip()
            record = CaseFile(
                case_title=case_title,
                file_path=relative_path,
                status=CaseStatus.PENDING,
                uploaded_by=uploader.id,
            )
            db.add(record)
            imported += 1

        db.commit()
        print(f"SOURCE_DIR={source_dir}")
        print(f"STORAGE_DIR={storage_dir}")
        print(f"IMPORTED={imported}")
        print(f"COPIED={copied}")
        print(f"SKIPPED={skipped}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import local PDF casefiles into DB.")
    parser.add_argument(
        "--source-dir",
        required=True,
        help="Directory that contains source PDF case files",
    )
    parser.add_argument(
        "--uploaded-by-email",
        default="admin@neuralshift.ai",
        help="Existing user email to set as uploaded_by",
    )
    args = parser.parse_args()

    import_casefiles(Path(args.source_dir), args.uploaded_by_email)


if __name__ == "__main__":
    main()
