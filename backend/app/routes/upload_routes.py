from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.upload_service import save_uploaded_file

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = save_uploaded_file(file=file, db=db, uploaded_by=current_user.id)
    return {
        "message": "File uploaded successfully",
        "data": result,
    }
