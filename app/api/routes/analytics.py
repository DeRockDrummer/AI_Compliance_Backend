from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.core.roles import require_role
from app.core.auth import get_current_user
from app.core.audit import log_audit

router = APIRouter(tags=["Analytics"])

# ============================================================
# WORKFLOW ANALYTICS (ADMIN ONLY)
# ============================================================

@router.get(
    "/workflows",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def workflow_analytics(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    workflows = db.query(Workflow).all()

    # Audit log for analytics access
    log_audit(
        db,
        user_id=current_user.id,
        action="analytics_view",
        resource_type="workflow_analytics",
        resource_id=None,
        details="Viewed workflow analytics",
    )

    results = []

    for wf in workflows:
        # Efficient SQL counts instead of Python loops
        total_steps = db.query(func.count(WorkflowStep.id)).filter(
            WorkflowStep.workflow_id == wf.id
        ).scalar()

        completed_steps = db.query(func.count(WorkflowStep.id)).filter(
            WorkflowStep.workflow_id == wf.id,
            WorkflowStep.status == "completed"
        ).scalar()

        in_progress_steps = db.query(func.count(WorkflowStep.id)).filter(
            WorkflowStep.workflow_id == wf.id,
            WorkflowStep.status == "in_progress"
        ).scalar()

        pending_steps = db.query(func.count(WorkflowStep.id)).filter(
            WorkflowStep.workflow_id == wf.id,
            WorkflowStep.status == "pending"
        ).scalar()

        results.append({
            "workflow_id": wf.id,
            "workflow_name": wf.name,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "in_progress_steps": in_progress_steps,
            "pending_steps": pending_steps,
            "completion_rate": (
                round((completed_steps / total_steps) * 100, 2)
                if total_steps > 0 else 0.0
            ),
        })

    return {
        "count": len(results),
        "workflows": results,
    }
