from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

# Correct import for your project
from app.db.session import get_db

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep

router = APIRouter(prefix="/workflows", tags=["workflows-public"])


def serialize_step(step: WorkflowStep) -> dict:
    return {
        "id": step.id,
        "name": step.name,
        "description": step.description,   # your WorkflowStep DOES have description
        "status": step.status,
        "order": step.order,
        "workflow_id": step.workflow_id,
    }


def serialize_workflow(wf: Workflow) -> dict:
    return {
        "id": wf.id,
        "name": wf.name,
        # ❌ REMOVED description — your Workflow model does not have it
        "steps": [serialize_step(s) for s in sorted(wf.steps, key=lambda x: x.order)],
    }


@router.get("/{workflow_id}")
def get_workflow_public(
    workflow_id: int,
    db: Session = Depends(get_db),
):
    """
    Public/user-facing workflow detail endpoint.
    Mirrors the shape used by /admin/workflows/{id} but without admin-only fields.
    """
    wf: Optional[Workflow] = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return serialize_workflow(wf)
