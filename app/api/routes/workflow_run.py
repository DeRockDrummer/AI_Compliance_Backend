from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

# ⭐ Your real workflow engine
from app.core.workflow_agent_engine import run_workflow_triggers

router = APIRouter(prefix="/workflows", tags=["Workflow Execution"])


@router.post("/{workflow_id}/run")
def run_workflow_now(workflow_id: int, db: Session = Depends(get_db)):
    """
    Run ALL workflow steps (full execution).
    This triggers all agents in order and updates step statuses.
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Log start
    db.add(AuditLog(
        action="workflow_run_started",
        resource_type="workflow",
        resource_id=workflow_id,
        user_id=1,
        details=f"Full workflow execution started"
    ))
    db.commit()

    # ⭐ Run your actual workflow engine
    run_workflow_triggers(db, workflow_id, user_id=1)

    # Collect updated step statuses
    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_id == workflow_id)
        .order_by(WorkflowStep.order.asc())
        .all()
    )

    step_results = [
        {
            "step_id": step.id,
            "step_name": step.name,
            "status": step.status
        }
        for step in steps
    ]

    # Determine workflow status
    incomplete = any(step.status != "completed" for step in steps)

    if not incomplete:
        workflow.status = "completed"
        db.commit()

        db.add(AuditLog(
            action="workflow_completed",
            resource_type="workflow",
            resource_id=workflow_id,
            user_id=1,
            details="Workflow fully completed"
        ))
        db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_status": workflow.status,
        "steps": step_results
    }
