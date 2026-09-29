from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)

    # MUST MATCH auth.py
    token_hash = Column(String, unique=True, nullable=False, index=True)

    # Indexed for faster session queries
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # MUST MATCH auth.py
    expires_at = Column(DateTime, nullable=False, index=True)

    revoked = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="refresh_tokens")

    def __repr__(self):
        return f"<RefreshToken id={self.id} user_id={self.user_id} revoked={self.revoked}>"
