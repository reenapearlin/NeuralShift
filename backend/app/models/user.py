from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        default=UserRole.LAWYER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    uploaded_casefiles = relationship(
        "CaseFile",
        back_populates="uploaded_by_user",
        foreign_keys="CaseFile.uploaded_by",
        cascade="all, delete-orphan",
    )
    reviewed_casefiles = relationship(
        "CaseFile",
        back_populates="reviewed_by_user",
        foreign_keys="CaseFile.reviewed_by",
    )
    search_logs = relationship("SearchLog", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="generated_by_user", cascade="all, delete-orphan")
