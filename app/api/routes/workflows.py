from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowStepUpdate,
    WorkflowStepResponse,
    WorkflowStepCreate,
)
from app.crud.workflow import (
    create_workflow,
    get_workflows,
    get_workflow,
    update_step_status,
    delete_workflow,
)
from app.core.roles import require_role
from app.core.auth import get_current_user
from app.core.audit import log_audit
from app.db.models.workflow_step import WorkflowStep

router = APIRouter(tags=["Workflows"])

# ============================================================
# CREATE WORKFLOW (ADMIN ONLY)
# ============================================================

@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create(payload: WorkflowCreate, db: Session = Depends(get_db)):
    workflow = create_workflow(db, payload)
    if not workflow:
        raise HTTPException(
            status_code=500,
            detail="Failed to create workflow"
        )
    return workflow

# ============================================================
# LIST WORKFLOWS (ADMIN ONLY)
# ============================================================

@router.get(
    "/",
    response_model=list[WorkflowResponse],
    dependencies=[Depends(require_role("admin"))],
)
def list_workflows(db: Session = Depends(get_db)):
    workflows = get_workflows(db)
    return workflows

# ============================================================
# GET WORKFLOW DETAIL (ADMIN ONLY)
# ============================================================

@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    dependencies=[Depends(require_role("admin"))],
)
def get(workflow_id: int, db: Session = Depends(get_db)):
    workflow = get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    return workflow

# ============================================================
# CREATE WORKFLOW STEP (ADMIN ONLY)
# ============================================================

@router.post(
    "/steps",
    response_model=WorkflowStepResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def create_step(
    payload: WorkflowStepCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Validate workflow exists
    workflow = get_workflow(db, payload.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    # Validate order
    existing_orders = {step.order for step in workflow.steps}
    if payload.order in existing_orders:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Step order {payload.order} already exists"
        )

    new_step = WorkflowStep(
        workflow_id=payload.workflow_id,
        name=payload.name,
        description=payload.description,
        status="pending",
        order=payload.order,
    )

    db.add(new_step)
    db.commit()
    db.refresh(new_step)

    # Audit log
    log_audit(
        db,
        user_id=current_user.id,
        action="workflow_step_created",
        resource_type="workflow_step",
        resource_id=new_step.id,
        details=f"Step '{new_step.name}' created in workflow '{workflow.name}' with order {new_step.order}",
    )

    return new_step

# ============================================================
# UPDATE STEP STATUS (ADMIN ONLY)
# ============================================================

@router.patch(
    "/steps/{step_id}",
    response_model=WorkflowStepResponse,
    dependencies=[Depends(require_role("admin"))],
)
def update_step(
    step_id: int,
    payload: WorkflowStepUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Validate status
    valid_statuses = {"pending", "in_progress", "completed"}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{payload.status}'"
        )

    step = update_step_status(db, step_id, payload)
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found"
        )

    # Audit log
    log_audit(
        db,
        user_id=current_user.id,
        action="workflow_step_update",
        resource_type="workflow_step",
        resource_id=step.id,
        details=f"Status changed to '{step.status}' for step '{step.name}'",
    )

    return step

# ============================================================
# DELETE WORKFLOW (ADMIN ONLY)
# ============================================================

@router.delete(
    "/{workflow_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def delete(workflow_id: int, db: Session = Depends(get_db)):
    ok = delete_workflow(db, workflow_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )

    return {"detail": "Workflow deleted successfully"}
