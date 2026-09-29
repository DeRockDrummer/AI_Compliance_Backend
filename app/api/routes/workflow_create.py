from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

router = APIRouter(prefix="/admin/workflows", tags=["Admin Workflows"])


@router.post("/create")
def create_workflow(payload: dict, db: Session = Depends(get_db)):
    """
    Create a workflow manually for testing.
    Payload example:
    {
        "name": "Test Workflow",
        "steps": ["Step A", "Step B", "Step C"]
    }
    """

    name = payload.get("name")
    steps = payload.get("steps", [])

    if not name:
        raise HTTPException(status_code=400, detail="Workflow name is required")

    # Create workflow (NO description field)
    workflow = Workflow(
        name=name,
        status="in_progress"
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    # Create steps
    created_steps = []
    for idx, step_name in enumerate(steps, start=1):
        step = WorkflowStep(
            name=step_name,
            status="pending",
            order=idx,
            workflow_id=workflow.id
        )
        db.add(step)
        db.commit()
        db.refresh(step)
        created_steps.append(step.id)

    # Log creation
    db.add(AuditLog(
        action="workflow_created",
        resource_type="workflow",
        resource_id=workflow.id,
        user_id=1,
        details=f"Workflow created with steps: {created_steps}"
    ))
    db.commit()

    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "steps": created_steps,
        "message": "Workflow successfully created."
    }
