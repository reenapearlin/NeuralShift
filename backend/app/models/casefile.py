from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.database import Base
from app.models.enums import CaseStatus


class CaseFile(Base):
    __tablename__ = "casefiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_title: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status_enum"),
        default=CaseStatus.PENDING,
        nullable=False,
    )
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    uploaded_by_user = relationship(
        "User",
        back_populates="uploaded_casefiles",
        foreign_keys=[uploaded_by],
    )
    reviewed_by_user = relationship(
        "User",
        back_populates="reviewed_casefiles",
        foreign_keys=[reviewed_by],
    )
    metadata_entries = relationship(
        "CaseMetadata",
        back_populates="casefile",
        cascade="all, delete-orphan",
    )
    search_logs = relationship("SearchLog", back_populates="casefile")
    reports = relationship("Report", back_populates="casefile", cascade="all, delete-orphan")
