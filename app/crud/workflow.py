from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep

# ============================================================
# CREATE WORKFLOW
# ============================================================

def create_workflow(db: Session, payload):
    workflow = Workflow(
        name=payload.name,
        description=payload.description,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow

# ============================================================
# UPDATE WORKFLOW
# ============================================================

def update_workflow(db: Session, workflow_id: int, payload):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        return None

    workflow.name = payload.name
    workflow.description = payload.description
    workflow.updated_at = datetime.utcnow()

    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow

# ============================================================
# LIST WORKFLOWS
# ============================================================

def get_workflows(db: Session):
    return (
        db.query(Workflow)
        .options(joinedload(Workflow.steps))
        .all()
    )

# ============================================================
# GET WORKFLOW (EAGER LOAD STEPS)
# ============================================================

def get_workflow(db: Session, workflow_id: int):
    return (
        db.query(Workflow)
        .options(joinedload(Workflow.steps))
        .filter(Workflow.id == workflow_id)
        .first()
    )

# ============================================================
# CREATE WORKFLOW STEP
# ============================================================

def create_step(db: Session, workflow_id: int, payload):
    step = WorkflowStep(
        workflow_id=workflow_id,
        name=payload.name,
        description=payload.description,
        status="pending",
        order=payload.order,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(step)
    db.commit()
    db.refresh(step)
    return step

# ============================================================
# UPDATE STEP STATUS
# ============================================================

def update_step_status(db: Session, step_id: int, payload):
    step = db.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
    if not step:
        return None

    step.status = payload.status
    step.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(step)
    return step

# ============================================================
# REORDER STEPS
# ============================================================

def reorder_steps(db: Session, workflow_id: int, new_order: list[int]):
    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_id == workflow_id)
        .order_by(WorkflowStep.order)
        .all()
    )

    if len(steps) != len(new_order):
        return None

    for step, new_pos in zip(steps, new_order):
        step.order = new_pos
        step.updated_at = datetime.utcnow()

    db.commit()
    return steps

# ============================================================
# DELETE WORKFLOW
# ============================================================

def delete_workflow(db: Session, workflow_id: int):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        return False

    db.delete(workflow)
    db.commit()
    return True
