from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # ⭐ REQUIRED — workflow lifecycle status
    status = Column(String, default="in_progress")  
    # valid values:
    # "in_progress", "completed", "failed", "needs_attention"

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to steps
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan")

