from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

router = APIRouter(prefix="/workflows", tags=["Workflow Cancel"])


@router.post("/{workflow_id}/cancel")
def cancel_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """
    Cancel a workflow.
    - Marks workflow.status = "cancelled"
    - Marks all non-completed steps as "cancelled"
    - Logs cancellation event
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # If already completed or cancelled, do nothing
    if workflow.status in ["completed", "cancelled"]:
        return {
            "workflow_id": workflow_id,
            "status": workflow.status,
            "message": f"Workflow already {workflow.status}."
        }

    # Cancel workflow
    workflow.status = "cancelled"
    db.commit()

    # Cancel all non-completed steps
    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_id == workflow_id)
        .all()
    )

    cancelled_steps = []

    for step in steps:
        if step.status != "completed":
            step.status = "cancelled"
            db.commit()
            cancelled_steps.append(step.id)

    # Log cancellation
    db.add(AuditLog(
        action="workflow_cancelled",
        resource_type="workflow",
        resource_id=workflow_id,
        user_id=1,
        details=f"Workflow cancelled. Steps cancelled: {cancelled_steps}"
    ))
    db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_status": workflow.status,
        "cancelled_steps": cancelled_steps,
        "message": "Workflow successfully cancelled."
    }
