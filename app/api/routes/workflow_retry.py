from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

# ⭐ Correct step executor
from app.core.workflow_agent_engine import run_workflow_triggers

router = APIRouter(prefix="/workflows", tags=["Workflow Retry"])


@router.post("/{workflow_id}/retry")
def retry_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """
    Retry failed + pending workflow steps.
    Completed steps are skipped.
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Fetch steps that need retry
    steps_to_retry = (
        db.query(WorkflowStep)
        .filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.status.in_(["failed", "pending"])
        )
        .order_by(WorkflowStep.order.asc())
        .all()
    )

    if not steps_to_retry:
        return {
            "workflow_id": workflow_id,
            "message": "No failed or pending steps to retry.",
            "status": workflow.status
        }

    retry_results = []

    # Log retry start
    db.add(AuditLog(
        action="workflow_retry_started",
        resource_type="workflow",
        resource_id=workflow_id,
        user_id=1,
        details=f"Retrying {len(steps_to_retry)} steps"
    ))
    db.commit()

    # ⭐ Run your actual workflow engine
    run_workflow_triggers(db, workflow_id, user_id=1)

    # Collect updated statuses
    for step in steps_to_retry:
        retry_results.append({
            "step_id": step.id,
            "step_name": step.name,
            "new_status": step.status
        })

    # Update workflow status if all steps completed
    remaining = (
        db.query(WorkflowStep)
        .filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.status != "completed"
        )
        .count()
    )

    if remaining == 0:
        workflow.status = "completed"
        db.commit()

        db.add(AuditLog(
            action="workflow_completed",
            resource_type="workflow",
            resource_id=workflow_id,
            user_id=1,
            details="Workflow completed after retry."
        ))
        db.commit()

    return {
        "workflow_id": workflow_id,
        "workflow_status": workflow.status,
        "retry_count": len(retry_results),
        "results": retry_results
    }
