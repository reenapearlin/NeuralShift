from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.schemas.auth_schema import (
    TokenResponse,
    UserLoginRequest,
    UserResponse,
    UserSignupRequest,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: UserSignupRequest, db: Session = Depends(get_db)) -> UserResponse:
    return AuthService.register_user(db, payload)


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return AuthService.login_user(db, payload)


@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def token_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    # OAuth2 password flow uses `username`; we treat it as email.
    payload = UserLoginRequest(email=form_data.username, password=form_data.password)
    return AuthService.login_user(db, payload)
