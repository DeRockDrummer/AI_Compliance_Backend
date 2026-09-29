from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

router = APIRouter(prefix="/workflows", tags=["Workflow Activity"])


@router.get("/{workflow_id}/activity")
def workflow_activity_feed(workflow_id: int, db: Session = Depends(get_db)):
    """
    Returns a detailed activity feed for all workflow steps.
    Includes:
    - step creation
    - agent triggers
    - step completion
    - step failure
    - auto-healing events
    - workflow-level events
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_id == workflow_id)
        .order_by(WorkflowStep.order.asc())
        .all()
    )

    # Build feed grouped by step
    feed = []

    for step in steps:
        step_logs = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type.in_(["workflow_step", "workflow"]),
                AuditLog.resource_id.in_([step.id, workflow_id])
            )
            .order_by(AuditLog.created_at.asc())
            .all()
        )

        feed.append({
            "step_id": step.id,
            "step_name": step.name,
            "status": step.status,
            "activity": [
                {
                    "log_id": log.id,
                    "action": log.action,
                    "details": log.details,
                    "timestamp": log.created_at.isoformat(),
                    "user_id": log.user_id
                }
                for log in step_logs
            ]
        })

    return {
        "workflow_id": workflow.id,
        "workflow_name": workflow.name,
        "status": workflow.status,
        "activity_feed": feed
    }
