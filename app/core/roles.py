from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.security import verify_access_token, get_token   # ⭐ FIXED
from app.db.session import get_db
from app.db.models.user import User
from app.core.audit import log_audit

# ============================================================
# REQUIRE EXACT ROLE
# ============================================================

def require_role(required_role: str):
    def wrapper(token: str = Depends(get_token), db: Session = Depends(get_db)):
        # ⭐ FIXED — replaced strict decode_access_token
        payload = verify_access_token(token)

        if payload is None or "sub" not in payload or "role" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token"
            )

        user_id = int(payload["sub"])
        role = payload["role"]

        # Role mismatch
        if role != required_role:
            log_audit(
                db,
                user_id=user_id,
                action="role_denied",
                resource_type="auth",
                resource_id=user_id,
                details=f"Required role '{required_role}', but user has '{role}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient role"
            )

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account disabled"
            )

        # Update last-seen timestamp
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()

        # Audit success
        log_audit(
            db,
            user_id=user.id,
            action="role_validated",
            resource_type="auth",
            resource_id=user.id,
            details=f"User authorized with role '{role}'"
        )

        return user

    return wrapper

# ============================================================
# REQUIRE ANY OF MULTIPLE ROLES
# ============================================================

def require_roles(*roles):
    def wrapper(token: str = Depends(get_token), db: Session = Depends(get_db)):
        # ⭐ FIXED — replaced strict decode_access_token
        payload = verify_access_token(token)

        if payload is None or "sub" not in payload or "role" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token"
            )

        user_id = int(payload["sub"])
        role = payload["role"]

        # Role mismatch
        if role not in roles:
            log_audit(
                db,
                user_id=user_id,
                action="role_denied",
                resource_type="auth",
                resource_id=user_id,
                details=f"Required roles {roles}, but user has '{role}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient role"
            )

        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account disabled"
            )

        # Update last-seen timestamp
        user.updated_at = datetime.utcnow()
        db.add(user)
        db.commit()

        # Audit success
        log_audit(
            db,
            user_id=user.id,
            action="role_validated",
            resource_type="auth",
            resource_id=user.id,
            details=f"User authorized with role '{role}'"
        )

        return user

    return wrapper
