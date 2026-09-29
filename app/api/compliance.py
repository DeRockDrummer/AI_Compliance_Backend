from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.core.security import get_token, verify_access_token   # ⭐ FIXED
from app.core.roles import require_role, require_roles
from app.core.audit import log_audit

router = APIRouter(prefix="/compliance", tags=["Compliance"])

# ============================================================
# BASIC AUTHENTICATED ROUTE (ANY USER)
# ============================================================

def require_user_any(token: str = Depends(get_token), db: Session = Depends(get_db)):
    # ⭐ REPLACED strict decode_access_token → verify_access_token
    payload = verify_access_token(token)

    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.disabled:
        raise HTTPException(status_code=403, detail="User account disabled")

    return user


@router.get("/status")
def compliance_status(current_user: User = Depends(require_user_any), db: Session = Depends(get_db)):
    log_audit(
        db,
        user_id=current_user.id,
        action="compliance_status_view",
        resource_type="compliance",
        resource_id=None,
        resource_owner_id=current_user.id,
        details=f"Compliance status viewed by {current_user.email}",
    )

    return {
        "message": "Compliance system operational",
        "user": current_user.email,
        "role": current_user.role,
        "timestamp": datetime.utcnow().isoformat(),
    }

# ============================================================
# ADMIN‑ONLY ROUTE
# ============================================================

@router.get("/admin/dashboard")
def admin_dashboard(current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    log_audit(
        db,
        user_id=current_user.id,
        action="compliance_admin_dashboard",
        resource_type="compliance",
        resource_id=None,
        resource_owner_id=current_user.id,
        details=f"Admin compliance dashboard accessed by {current_user.email}",
    )

    return {
        "message": "Admin compliance dashboard access granted",
        "user": current_user.email,
        "role": current_user.role,
        "timestamp": datetime.utcnow().isoformat(),
    }

# ============================================================
# USER‑ONLY ROUTE
# ============================================================

@router.get("/user/summary")
def user_summary(current_user: User = Depends(require_role("user")), db: Session = Depends(get_db)):
    log_audit(
        db,
        user_id=current_user.id,
        action="compliance_user_summary",
        resource_type="compliance",
        resource_id=None,
        resource_owner_id=current_user.id,
        details=f"User compliance summary accessed by {current_user.email}",
    )

    return {
        "message": "User compliance summary access granted",
        "user": current_user.email,
        "role": current_user.role,
        "timestamp": datetime.utcnow().isoformat(),
    }
