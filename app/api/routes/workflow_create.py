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
    Create a workflow with structured steps.

    Example payload:
    {
        "name": "Sales Outreach Workflow",
        "steps": [
            {
                "title": "Generate Lead List",
                "instructions": "Call /agent/business/leadgen",
                "agent": "business",
                "action": "leadgen",
                "order": 1,
                "metadata": {
                    "industry": "SaaS",
                    "limit": 25
                }
            }
        ]
    }
    """

    name = payload.get("name")
    steps = payload.get("steps", [])

    if not name:
        raise HTTPException(status_code=400, detail="Workflow name is required")

    if not steps:
        raise HTTPException(status_code=400, detail="At least one step is required")

    # Create workflow
    workflow = Workflow(
        name=name,
        status="in_progress"
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)

    created_steps = []

    for idx, step_payload in enumerate(steps, start=1):
        # Allow explicit order override, else use idx
        order = step_payload.get("order", idx)

        step = WorkflowStep(
            workflow_id=workflow.id,
            order=order,
            status="pending",

            # Basic fields
            name=step_payload.get("title") or step_payload.get("name") or f"Step {order}",
            description=step_payload.get("description"),

            # NEW Option B fields
            title=step_payload.get("title"),
            instructions=step_payload.get("instructions"),
            agent=step_payload.get("agent"),
            action=step_payload.get("action"),
            metadata=step_payload.get("metadata"),
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
        user_id=1,  # later: replace with current_user.id
        details=f"Workflow created with steps: {created_steps}"
    ))
    db.commit()

    return {
        "workflow_id": workflow.id,
        "name": workflow.name,
        "steps": created_steps,
        "message": "Workflow successfully created with structured steps."
    }
