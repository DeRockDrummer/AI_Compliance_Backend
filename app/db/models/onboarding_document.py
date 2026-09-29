# backend/app/db/models/onboarding_document.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class OnboardingDocument(Base):
    __tablename__ = "onboarding_documents"

    id = Column(Integer, primary_key=True, index=True)

    # ⭐ Ownership field
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    session_id = Column(Integer, ForeignKey("onboarding_sessions.id"), nullable=False, index=True)

    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("OnboardingSession", back_populates="documents")
    user = relationship("User")

    # ⭐ FIXED — Add missing relationship for extraction pipeline
    extracted_data = relationship(
        "ExtractedData",
        back_populates="document",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<OnboardingDocument id={self.id} filename={self.filename}>"
