from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    full_name = Column(String, nullable=True)

    # ⭐ UPGRADED ROLE SYSTEM
    # Valid roles: "admin", "superadmin"
    # Default is "admin" so new users have full dashboard access.
    role = Column(String, nullable=False, default="admin", index=True)

    disabled = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Onboarding sessions
    onboarding_sessions = relationship(
        "OnboardingSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Refresh tokens
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Documents uploaded by this user
    documents = relationship(
        "OnboardingDocument",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User id={self.id} email={self.email} role={self.role}>"
