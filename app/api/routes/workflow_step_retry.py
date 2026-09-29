from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

# Your real workflow engine
from app.core.workflow_agent_engine import run_workflow_triggers

router = APIRouter(prefix="/workflows", tags=["Workflow Step Retry"])


@router.post("/{workflow_id}/steps/{step_id}/retry")
def retry_single_step(workflow_id: int, step_id: int, db: Session = Depends(get_db)):
    """
    Retry a single workflow step.
    - Only retries the specified step
    - Works for failed or pending steps
    - Logs retry event
    - Uses your existing workflow engine
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    step = (
        db.query(WorkflowStep)
        .filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.id == step_id
        )
        .first()
    )

    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    if workflow.status in ["cancelled"]:
        raise HTTPException(status_code=400, detail="Workflow is cancelled and cannot be retried")

    if workflow.status == "paused":
        raise HTTPException(status_code=400, detail="Workflow is paused. Resume before retrying steps.")

    if step.status == "completed":
        return {
            "workflow_id": workflow_id,
            "step_id": step_id,
            "status": step.status,
            "message": "Step already completed. Nothing to retry."
        }

    # Log retry start
    db.add(AuditLog(
        action="workflow_step_retry_started",
        resource_type="workflow_step",
        resource_id=step_id,
        user_id=1,
        details=f"Retrying step '{step.name}' in workflow {workflow_id}"
    ))
    db.commit()

    # ⭐ Force this step into pending state before retry
    step.status = "pending"
    db.commit()

    # ⭐ Run your workflow engine — it will process only pending/failed steps
    run_workflow_triggers(db, workflow_id, user_id=1)

    # Refresh step status
    db.refresh(step)

    # Log retry completion
    db.add(AuditLog(
        action="workflow_step_retry_completed",
        resource_type="workflow_step",
        resource_id=step_id,
        user_id=1,
        details=f"Step '{step.name}' retry completed with status '{step.status}'"
    ))
    db.commit()

    return {
        "workflow_id": workflow_id,
        "step_id": step_id,
        "step_name": step.name,
        "new_status": step.status,
        "message": "Single step retry completed."
    }
