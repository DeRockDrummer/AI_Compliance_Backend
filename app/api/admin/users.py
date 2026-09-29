from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.core.roles import require_role
from app.core.audit import log_audit

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])

# ============================================================
# LIST USERS (with optional filters)
# ============================================================

@router.get("/", dependencies=[Depends(require_role("admin"))])
def list_users(
    role: str | None = None,
    disabled: bool | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if disabled is not None:
        query = query.filter(User.disabled == disabled)

    users = query.all()

    # Audit
    log_audit(
        db,
        user_id=None,
        action="admin_list_users",
        resource_type="user",
        details=f"Listed {len(users)} users"
    )

    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "disabled": u.disabled,
            "created_at": u.created_at,
            "updated_at": u.updated_at,
        }
        for u in users
    ]

# ============================================================
# UPDATE USER (role, disabled, full_name)
# ============================================================

@router.patch("/{user_id}", dependencies=[Depends(require_role("admin"))])
def update_user(user_id: int, payload: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    before = {
        "role": user.role,
        "disabled": user.disabled,
        "full_name": user.full_name,
    }

    if "role" in payload:
        user.role = payload["role"]

    if "disabled" in payload:
        user.disabled = payload["disabled"]

    if "full_name" in payload:
        user.full_name = payload["full_name"]

    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Audit
    log_audit(
        db,
        user_id=None,
        action="admin_update_user",
        resource_type="user",
        resource_id=user.id,
        resource_owner_id=user.id,
        details={
            "before": before,
            "after": {
                "role": user.role,
                "disabled": user.disabled,
                "full_name": user.full_name,
            }
        }
    )

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "disabled": user.disabled,
        "updated_at": user.updated_at,
    }

# ============================================================
# DELETE USER (full cascade)
# ============================================================

@router.delete("/{user_id}", dependencies=[Depends(require_role("admin"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    # Audit
    log_audit(
        db,
        user_id=None,
        action="admin_delete_user",
        resource_type="user",
        resource_id=user_id,
        resource_owner_id=user_id,
        details=f"User {user.email} deleted"
    )

    return {"detail": "User deleted"}
