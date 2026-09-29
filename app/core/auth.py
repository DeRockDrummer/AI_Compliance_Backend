from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.crud.user import get_user_by_id
from app.core.security import verify_access_token
from app.core.audit import log_audit

# HTTP Bearer token extractor
bearer_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """
    Universal authentication dependency.
    - Extracts Bearer token
    - Verifies JWT signature + expiration
    - Loads user from DB
    - Ensures user is active
    - Updates last-seen timestamp
    - Logs successful authentication
    """

    # Extract token
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials

    # Verify JWT
    payload = verify_access_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )

    # Load user
    user_id = int(payload["sub"])
    user = get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account disabled",
        )

    # Update last-seen timestamp
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()

    # Audit successful authentication
    log_audit(
        db,
        user_id=user.id,
        action="auth_validated",
        resource_type="user",
        resource_id=user.id,
        details=f"User {user.email} authenticated successfully",
    )

    return user
