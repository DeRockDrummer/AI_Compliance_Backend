from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.audit_log import AuditLog
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.onboarding import OnboardingSession
from app.db.models.extracted_data import ExtractedData

from app.core.roles import require_role
from app.core.auth import get_current_user
from app.core.audit import log_audit

router = APIRouter(
    prefix="/agent/system",
    tags=["System Maintenance Agent"],
    dependencies=[Depends(require_role("admin"))],  # later: add 'system_agent' role
)

# ============================================================
# RUN DIAGNOSTICS
# ============================================================

@router.get(
    "/diagnostics",
    status_code=status.HTTP_200_OK,
)
def run_diagnostics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Log agent run
    log_audit(
        db,
        user_id=current_user.id,
        action="system_diagnostics_run",
        resource_type="system",
        resource_id=None,
        details="System diagnostics executed by maintenance agent",
    )

    # Example checks (we’ll expand these later)
    onboarding_count = db.query(OnboardingSession).count()
    workflow_count = db.query(Workflow).count()
    step_count = db.query(WorkflowStep).count()
    extracted_count = db.query(ExtractedData).count()
    audit_count = db.query(AuditLog).count()

    return {
        "status": "ok",
        "summary": {
            "onboarding_sessions": onboarding_count,
            "workflows": workflow_count,
            "workflow_steps": step_count,
            "extracted_records": extracted_count,
            "audit_logs": audit_count,
        },
    }

# ============================================================
# RUN REPAIR (SAFE AUTO-FIXES)
# ============================================================

@router.post(
    "/repair",
    status_code=status.HTTP_200_OK,
)
def run_repair(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Log agent run
    log_audit(
        db,
        user_id=current_user.id,
        action="system_repair_run",
        resource_type="system",
        resource_id=None,
        details="System repair executed by maintenance agent",
    )

    repairs = []

    # Example: fix onboarding sessions stuck in 'uploading' with completed docs
    stuck_sessions = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.status == "uploading")
        .all()
    )

    for session in stuck_sessions:
        docs = (
            db.query(ExtractedData)
            .filter(ExtractedData.onboarding_session_id == session.id)
            .all()
        )

        if docs:
            session.status = "completed"
            repairs.append(
                f"Session {session.id} status set to 'completed' (had extracted data)."
            )

    db.commit()

    return {
        "status": "ok",
        "repairs_applied": repairs,
    }

# ============================================================
# UPDATE AGENT CONFIG / PROMPTS (PLACEHOLDER)
# ============================================================

@router.post(
    "/update",
    status_code=status.HTTP_200_OK,
)
def update_agent_config(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    log_audit(
        db,
        user_id=current_user.id,
        action="system_agent_update",
        resource_type="system",
        resource_id=None,
        details="System maintenance agent configuration updated",
    )

    # Placeholder: later we’ll store prompt/config in DB
    return {
        "status": "ok",
        "message": "System maintenance agent configuration update endpoint is wired.",
    }
