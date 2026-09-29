from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.core.roles import require_role
from app.core.auth import get_current_user
from app.core.audit import log_audit

router = APIRouter(tags=["Admin"])

# ============================================================
# REMOVE OLD /admin/dashboard ROUTE
# ============================================================

# (No dashboard route here anymore — new dashboard lives in admin_dashboard.py)

# ============================================================
# ADMIN USER INFO (still useful)
# ============================================================

@router.get(
    "/info",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def admin_info(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        log_audit(
            db,
            user_id=current_user.id,
            action="admin_info_view",
            resource_type="admin_info",
            resource_id=None,
            details=f"Admin '{current_user.email}' viewed admin info",
        )

        return {
            "admin": {
                "id": current_user.id,
                "email": current_user.email,
                "role": current_user.role,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load admin info: {str(e)}"
        )
