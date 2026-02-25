from fastapi import APIRouter, Depends

from app.core.dependencies import require_admin
from app.models.user import User


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/protected")
def admin_protected_route(current_user: User = Depends(require_admin)) -> dict[str, str]:
    return {"message": f"Welcome admin {current_user.full_name}"}
