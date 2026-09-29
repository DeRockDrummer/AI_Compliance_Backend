from sqlalchemy.orm import Session
from typing import Optional, Union
from datetime import datetime
import json

from app.db.models.audit_log import AuditLog


def log_audit(
    db: Session,
    user_id: Optional[int] = None,
    action: str = "",
    resource_type: str = "",
    resource_id: Optional[int] = None,
    resource_owner_id: Optional[int] = None,
    details: Optional[Union[str, dict]] = None,
):
    """
    Centralized audit logging helper.
    - Accepts positional or keyword arguments
    - Accepts dict or string details
    - Supports resource_owner_id
    - Never crashes the main request
    """

    try:
        # Convert dict → JSON
        if isinstance(details, dict):
            details = json.dumps(details)

        audit = AuditLog(
            user_id=user_id,
            resource_owner_id=resource_owner_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            updated_at=datetime.utcnow(),
        )

        db.add(audit)
        db.commit()
        db.refresh(audit)

        return audit

    except Exception as e:
        # NEVER break the main request
        print(f"[AUDIT ERROR] Failed to write audit log: {e}")
        return None
