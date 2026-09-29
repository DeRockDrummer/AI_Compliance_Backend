from sqlalchemy.orm import Session
from app.db.models.audit_log import AuditLog

# ============================================================
# LIST AUDIT LOGS (OPTIONAL FILTERS)
# ============================================================

def list_audit_logs(
    db: Session,
    user_id: int | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 200,
):
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if action:
        query = query.filter(AuditLog.action == action)

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    return query.limit(limit).all()

# ============================================================
# GET SINGLE AUDIT LOG
# ============================================================

def get_audit_log(db: Session, log_id: int):
    return db.query(AuditLog).filter(AuditLog.id == log_id).first()

# ============================================================
# COUNT AUDIT LOGS (FOR ANALYTICS)
# ============================================================

def count_audit_logs(db: Session):
    return db.query(AuditLog).count()
