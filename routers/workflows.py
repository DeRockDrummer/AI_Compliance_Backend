from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowStep(BaseModel):
    id: int
    title: str
    description: str
    status: str  # "pending", "in_progress", "completed"


class Workflow(BaseModel):
    id: int
    name: str
    description: str
    steps: List[WorkflowStep]


# In-memory placeholder store for now
WORKFLOWS_DB = [
    Workflow(
        id=1,
        name="GDPR Readiness",
        description="Prepare organization for GDPR compliance.",
        steps=[
            WorkflowStep(id=1, title="Data Inventory", description="Identify all personal data.", status="pending"),
            WorkflowStep(id=2, title="Legal Basis Review", description="Review lawful bases.", status="pending"),
        ],
    )
]


@router.get("/", response_model=List[Workflow])
async def list_workflows():
    return WORKFLOWS_DB


@router.get("/{workflow_id}", response_model=Workflow)
async def get_workflow(workflow_id: int):
    for wf in WORKFLOWS_DB:
        if wf.id == workflow_id:
            return wf
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")


class StepUpdate(BaseModel):
    status: str  # "pending", "in_progress", "completed"


@router.patch("/{workflow_id}/steps/{step_id}", response_model=Workflow)
async def update_step_status(workflow_id: int, step_id: int, payload: StepUpdate):
    for wf in WORKFLOWS_DB:
        if wf.id == workflow_id:
            for step in wf.steps:
                if step.id == step_id:
                    step.status = payload.status
                    return wf
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step or workflow not found")
