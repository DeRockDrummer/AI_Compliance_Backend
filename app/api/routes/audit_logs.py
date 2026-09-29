from fastapi import APIRouter, Depends, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import asyncio

from app.db.session import get_db
from app.db.models.audit_log import AuditLog
from app.core.roles import require_roles
from app.core.auth import get_current_user
from app.core.audit import log_audit

router = APIRouter(tags=["Audit Logs"])

# ============================================================
# LIST AUDIT LOGS — ADMIN + SUPERADMIN
# ============================================================

@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("admin", "superadmin"))],
)
def list_audit_logs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),

    # Optional filters
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),

    # Search filter
    search: Optional[str] = Query(None),

    # Date range filtering
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),

    # Pagination
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    # Audit: admin viewed logs
    log_audit(
        db,
        user_id=current_user.id,
        action="audit_logs_view",
        resource_type="audit_log",
        resource_id=None,
        details="Viewed audit logs",
    )

    query = db.query(AuditLog)

    # Filters
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if action is not None:
        query = query.filter(AuditLog.action == action)

    if resource_type is not None:
        query = query.filter(AuditLog.resource_type == resource_type)

    # Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            AuditLog.details.ilike(search_term) |
            AuditLog.action.ilike(search_term)
        )

    # Date range
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.created_at >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.created_at <= end_dt)
        except ValueError:
            pass

    # Order newest first
    query = query.order_by(AuditLog.created_at.desc())

    # Pagination
    total = query.count()
    logs = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }

# ============================================================
# REAL-TIME WEBSOCKET STREAMING
# ============================================================

@router.websocket("/stream")
async def audit_log_stream(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            db = next(get_db())
            latest = (
                db.query(AuditLog)
                .order_by(AuditLog.created_at.desc())
                .first()
            )

            if latest:
                await websocket.send_json({
                    "id": latest.id,
                    "user_id": latest.user_id,
                    "action": latest.action,
                    "resource_type": latest.resource_type,
                    "resource_id": latest.resource_id,
                    "details": latest.details,
                    "created_at": latest.created_at.isoformat(),
                })

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
