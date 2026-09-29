from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.audit import AuditLog
from app.core.roles import require_role

router = APIRouter(
    prefix="/admin/roles",
    tags=["Role Diagnostics"],
    dependencies=[Depends(require_role("superadmin"))],
)

VALID_ROLES = {"superadmin", "admin", "manager", "user"}


@router.get("/diagnostics")
def role_diagnostics(db: Session = Depends(get_db)):
    users = db.query(User).all()
    logs = (
        db.query(AuditLog)
        .filter(
            AuditLog.action.in_(
                ["user_role_changed", "role_change_blocked", "user_delete_blocked"]
            )
        )
        .order_by(AuditLog.timestamp.desc())
        .all()
    )

    findings = {
        "orphaned_users": [],
        "invalid_roles": [],
        "deprecated_roles": [],
        "missing_role_logs": [],
        "privilege_escalation_attempts": [],
        "hierarchy_violations": [],
    }

    # Users + roles
    for u in users:
        if not u.role:
            findings["orphaned_users"].append(
                {"id": u.id, "email": u.email, "reason": "No role assigned"}
            )
        elif u.role not in VALID_ROLES:
            findings["invalid_roles"].append(
                {"id": u.id, "email": u.email, "role": u.role}
            )

    # Privilege escalation + hierarchy
    for log in logs:
        if log.action == "role_change_blocked":
            findings["privilege_escalation_attempts"].append(
                {
                    "id": log.id,
                    "timestamp": log.timestamp.isoformat(),
                    "details": log.details,
                    "user_id": log.user_id,
                }
            )
        elif log.action == "user_role_changed":
            details = (log.details or "").lower()
            if "superadmin" in details and "changed role from" in details:
                # Any superadmin role change is high‑sensitivity
                findings["hierarchy_violations"].append(
                    {
                        "id": log.id,
                        "timestamp": log.timestamp.isoformat(),
                        "details": log.details,
                        "user_id": log.user_id,
                    }
                )

    return {
        "summary": {
            "total_users": len(users),
            "total_role_logs": len(logs),
            "orphaned_users": len(findings["orphaned_users"]),
            "invalid_roles": len(findings["invalid_roles"]),
            "deprecated_roles": len(findings["deprecated_roles"]),
            "missing_role_logs": len(findings["missing_role_logs"]),
            "privilege_escalation_attempts": len(
                findings["privilege_escalation_attempts"]
            ),
            "hierarchy_violations": len(findings["hierarchy_violations"]),
        },
        "findings": findings,
    }
