from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Who the action was performed ON (optional)
    resource_owner_id = Column(Integer, nullable=True, index=True)

    # Action metadata
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True)

    # Human-readable or JSON details
    details = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship back to User
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog id={self.id} action={self.action} resource_type={self.resource_type}>"
