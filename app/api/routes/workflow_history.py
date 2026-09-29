from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.audit_log import AuditLog

router = APIRouter(prefix="/workflows", tags=["Workflow History"])


@router.get("/{workflow_id}/history")
def workflow_history(workflow_id: int, db: Session = Depends(get_db)):
    """
    Returns full workflow history based on AuditLog entries.
    Uses:
    - resource_type = "workflow"
    - resource_id = workflow_id
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.resource_type == "workflow",
            AuditLog.resource_id == workflow_id
        )
        .order_by(AuditLog.created_at.asc())
        .all()
    )

    history = []

    for log in logs:
        history.append({
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "timestamp": log.created_at.isoformat(),
            "user_id": log.user_id,
            "resource_owner_id": log.resource_owner_id
        })

    return {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "status": workflow.status,
        "created_at": workflow.created_at,
        "updated_at": workflow.updated_at,
        "history": history
    }
