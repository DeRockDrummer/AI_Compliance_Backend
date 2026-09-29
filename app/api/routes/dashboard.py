from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep

from app.core.security import (
    verify_access_token,
    create_access_token,
    hash_refresh_token
)
from app.core.roles import require_role
from app.core.auth import get_current_user
from app.core.audit import log_audit

router = APIRouter(tags=["Dashboard"])

# ============================================================
# USER DASHBOARD (ADMIN ONLY)
# ============================================================

@router.get(
    "/user",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def get_user_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            raw_refresh = request.cookies.get("refresh_token")
            if raw_refresh:
                hashed = hash_refresh_token(raw_refresh)
                rt = db.query(RefreshToken).filter(
                    RefreshToken.token_hash == hashed,
                    RefreshToken.revoked == False
                ).first()

                if rt and rt.expires_at > datetime.utcnow():
                    token = create_access_token(
                        {"sub": rt.user_id, "role": current_user.role}
                    )

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized"
            )

        payload = verify_access_token(token)
        if payload is None or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token"
            )

        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        log_audit(
            db,
            user_id=current_user.id,
            action="dashboard_view",
            resource_type="dashboard",
            resource_id=None,
            resource_owner_id=user.id,
            details=f"Dashboard accessed by admin '{current_user.email}'",
        )

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "disabled": user.disabled,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            },
            "compliance": {
                "status": "Good standing",
                "workflow_progress": "25%",
            },
            "tasks": [
                "Review policy updates",
                "Complete training module"
            ],
            "notifications": [
                "New compliance update available"
            ],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )


# ============================================================
# WORKFLOW DASHBOARD (ADMIN ONLY)
# ============================================================

@router.get(
    "/workflows",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def workflow_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Workflow Dashboard:
    - Status counts
    - Workflow summaries
    - Step breakdowns
    """

    workflows = db.query(Workflow).all()

    status_counts = {
        "completed": 0,
        "in_progress": 0,
        "failed": 0,
        "needs_attention": 0,
        "total": len(workflows),
    }

    workflow_summaries = []

    for wf in workflows:
        if wf.status in status_counts:
            status_counts[wf.status] += 1

        steps = db.query(WorkflowStep).filter(
            WorkflowStep.workflow_id == wf.id
        ).order_by(WorkflowStep.order.asc()).all()

        step_summaries = [
            {
                "id": step.id,
                "name": step.name,
                "order": step.order,
                "status": step.status,
                "updated_at": step.updated_at,
            }
            for step in steps
        ]

        workflow_summaries.append({
            "id": wf.id,
            "name": wf.name,
            "status": wf.status,
            "created_at": wf.created_at,
            "updated_at": wf.updated_at,
            "step_count": len(steps),
            "steps": step_summaries,
        })

    log_audit(
        db,
        user_id=current_user.id,
        action="workflow_dashboard_view",
        resource_type="dashboard",
        resource_id=None,
        details="Workflow dashboard accessed"
    )

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "status_counts": status_counts,
        "workflows": workflow_summaries,
    }
