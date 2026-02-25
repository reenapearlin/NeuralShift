from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.services.upload_service import save_uploaded_file
from app.config.database import get_db  # created by Member 2

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    result = save_uploaded_file(file, db)
    return {
        "message": "File uploaded successfully",
        "data": result
    }