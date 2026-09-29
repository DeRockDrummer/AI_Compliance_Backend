from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.core.security import get_token, verify_access_token   # ⭐ FIXED
from app.core.roles import require_role
from app.core.audit import log_audit

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])

# ============================================================
# BASIC AUTH (ADMIN ONLY)
# ============================================================

def require_admin_user(token: str = Depends(get_token), db: Session = Depends(get_db)):
    # ⭐ REPLACED strict decode_access_token → verify_access_token
    payload = verify_access_token(token)

    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")

    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: admin only")

    if user.disabled:
        raise HTTPException(status_code=403, detail="User account disabled")

    return user

# ============================================================
# REPORTS SUMMARY (ADMIN ONLY)
# ============================================================

@router.get("/summary", dependencies=[Depends(require_role("admin"))])
def reports_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_user)
):
    # Audit log
    log_audit(
        db,
        user_id=current_user.id,
        action="reports_summary_view",
        resource_type="report",
        resource_id=None,
        resource_owner_id=current_user.id,
        details=f"Admin '{current_user.email}' viewed reports summary",
    )

    return {
        "message": "Reports system operational",
        "admin": current_user.email,
        "role": current_user.role,
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "compliance_reports": "Available",
            "pdf_export": True,
            "docx_export": True,
            "audit_logs": "Integrated",
            "workflows": "Integrated",
            "onboarding": "Integrated",
            "extracted_data": "Integrated",
        }
    }
