from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json
import os
from datetime import datetime

from app.db.session import get_db
from app.db.models.onboarding_document import OnboardingDocument
from app.db.models.extracted_data import ExtractedData
from app.db.models.onboarding import OnboardingSession
from app.db.models.workflow_step import WorkflowStep
from app.core.roles import require_roles
from app.core.auth import get_current_user
from app.core.audit import log_audit

# ⭐ NEW — workflow auto‑creation service
from app.services.workflow_auto_creation import auto_create_workflows

# ⭐ Agent trigger engine
from app.core.workflow_agent_engine import run_workflow_triggers

router = APIRouter(
    prefix="/extract",
    tags=["AI Extraction"],
    dependencies=[Depends(require_roles("user", "admin"))]
)

# ============================================================
# AI MODEL CALL (placeholder)
# ============================================================

def ai_extract(text: str):
    return {
        "compliance_items": [
            {"type": "license", "name": "General Business License", "expires": "2027-01-01"},
            {"type": "insurance", "name": "Liability Insurance", "expires": "2026-12-01"}
        ],
        "raw_text_length": len(text)
    }

# ============================================================
# RUN EXTRACTION ON DOCUMENT
# ============================================================

@router.post("/{document_id}", status_code=status.HTTP_200_OK)
def extract_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    try:
        # Fetch document
        doc = db.query(OnboardingDocument).filter(
            OnboardingDocument.id == document_id
        ).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Ensure user owns the document OR is admin
        if current_user.role == "user" and doc.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to extract this document"
            )

        # Load file
        try:
            with open(doc.filepath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            text = "Binary file or unreadable content"

        # Run AI extraction
        extracted = ai_extract(text)

        # Save extracted data
        record = ExtractedData(
            document_id=document_id,
            raw_text=text,
            extracted_json=json.dumps(extracted),
            created_at=datetime.utcnow(),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        # Update onboarding session
        session = db.query(OnboardingSession).filter(
            OnboardingSession.id == doc.session_id
        ).first()

        if session:
            session.status = "extracting"
            session.updated_at = datetime.utcnow()
            db.add(session)
            db.commit()

        # ⭐ Auto-create workflows
        workflows_created = auto_create_workflows(
            db=db,
            user_id=current_user.id,
            extracted_items=extracted["compliance_items"],
        )

        # ⭐ Run agent triggers
        for wf in workflows_created:
            run_workflow_triggers(
                db=db,
                workflow_id=wf.id,
                user_id=current_user.id,
            )

        # Audit log
        log_audit(
            db,
            user_id=current_user.id,
            action="document_extracted",
            resource_type="onboarding_document",
            resource_id=document_id,
            details=f"AI extraction completed for document {doc.filename}",
        )

        # ⭐ FIXED — correct workflow step query
        workflows_response = []
        for wf in workflows_created:
            steps = db.query(WorkflowStep).filter(
                WorkflowStep.workflow_id == wf.id
            ).order_by(WorkflowStep.order).all()

            workflows_response.append({
                "workflow_id": wf.id,
                "name": wf.name,
                "steps": [s.name for s in steps]
            })

        return {
            "message": "Extraction complete",
            "record_id": record.id,
            "extracted": extracted,
            "document": {
                "id": doc.id,
                "filename": doc.filename,
                "session_id": doc.session_id,
            },
            "session_status": session.status if session else None,
            "workflows_created": workflows_response,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )
