# backend/app/db/models/onboarding.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class OnboardingSession(Base):
    __tablename__ = "onboarding_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # User who owns the onboarding session
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to User
    user = relationship("User", back_populates="onboarding_sessions")

    # ⭐ CRITICAL FIX — relationship to documents
    documents = relationship(
        "OnboardingDocument",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<OnboardingSession id={self.id} user_id={self.user_id} status={self.status}>"
