# backend/app/db/models/extracted_data.py

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base

class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(Integer, primary_key=True, index=True)

    # ⭐ Correct foreign key — extraction belongs to a document
    document_id = Column(Integer, ForeignKey("onboarding_documents.id"), nullable=False, index=True)

    # ⭐ Raw text extracted from the document
    raw_text = Column(Text, nullable=False)

    # ⭐ JSON blob of extracted structured data
    extracted_json = Column(Text, nullable=False)

    # ⭐ Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # ⭐ Relationship back to document
    document = relationship("OnboardingDocument", back_populates="extracted_data")

    def __repr__(self):
        return f"<ExtractedData id={self.id} document_id={self.document_id}>"
