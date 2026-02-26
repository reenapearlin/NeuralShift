from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth_schema import TokenResponse, UserLoginRequest, UserSignupRequest


class AuthService:
    @staticmethod
    def register_user(db: Session, payload: UserSignupRequest) -> User:
        existing_user = db.query(User).filter(User.email == payload.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role=UserRole.LAWYER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )
        return user

    @staticmethod
    def login_user(db: Session, payload: UserLoginRequest) -> TokenResponse:
        user = AuthService.authenticate_user(db, payload.email, payload.password)
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        return TokenResponse(access_token=access_token)
