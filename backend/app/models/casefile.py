from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.config.database import Base


class CaseFile(Base):
    __tablename__ = "case_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    extracted_text = Column(Text)
    status = Column(String, default="PENDING")
    created_at = Column(DateTime, default=datetime.utcnow)