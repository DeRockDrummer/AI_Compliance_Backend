from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

router = APIRouter(prefix="/workflows", tags=["Workflow Pause/Resume"])


@router.post("/{workflow_id}/pause")
def pause_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """
    Pause a workflow.
    - Sets workflow.status = 'paused'
    - Prevents further execution
    - Logs pause event
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status in ["completed", "cancelled"]:
        return {
            "workflow_id": workflow_id,
            "status": workflow.status,
            "message": f"Workflow already {workflow.status}. Cannot pause."
        }

    if workflow.status == "paused":
        return {
            "workflow_id": workflow_id,
            "status": workflow.status,
            "message": "Workflow already paused."
        }

    workflow.status = "paused"
    db.commit()

    db.add(AuditLog(
        action="workflow_paused",
        resource_type="workflow",
        resource_id=workflow_id,
        user_id=1,
        details="Workflow paused by admin"
    ))
    db.commit()

    return {
        "workflow_id": workflow_id,
        "status": workflow.status,
        "message": "Workflow successfully paused."
    }


@router.post("/{workflow_id}/resume")
def resume_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """
    Resume a paused workflow.
    - Sets workflow.status = 'in_progress'
    - Allows execution to continue
    - Logs resume event
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if workflow.status != "paused":
        return {
            "workflow_id": workflow_id,
            "status": workflow.status,
            "message": "Workflow is not paused. Cannot resume."
        }

    workflow.status = "in_progress"
    db.commit()

    db.add(AuditLog(
        action="workflow_resumed",
        resource_type="workflow",
        resource_id=workflow_id,
        user_id=1,
        details="Workflow resumed by admin"
    ))
    db.commit()

    return {
        "workflow_id": workflow_id,
        "status": workflow.status,
        "message": "Workflow successfully resumed."
    }
