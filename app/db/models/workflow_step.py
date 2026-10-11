from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class WorkflowStep(Base):
    __tablename__ = "workflow_steps"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)

    # Indexed for faster workflow queries
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, index=True)

    # Basic step metadata (existing)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # NEW FIELDS FOR OPTION B (full agent instructions + metadata)
    title = Column(String, nullable=True)                # Human-readable step title
    instructions = Column(Text, nullable=True)           # Agent instructions
    agent = Column(String, nullable=True)                # e.g. "business", "email", "reporting"
    action = Column(String, nullable=True)               # e.g. "leadgen", "outreach", "followup"
    metadata = Column(JSONB, nullable=True)              # Arbitrary JSON parameters

    # Status must match analytics + frontend expectations
    status = Column(String, nullable=False, default="pending")

    # Ordering within workflow
    order = Column(Integer, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to Workflow
    workflow = relationship("Workflow", back_populates="steps")

    def __repr__(self):
        return f"<WorkflowStep id={self.id} name={self.name} order={self.order}>"
