from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models.user import User

# ============================================================
# GET USER BY ID
# ============================================================

def get_user_by_id(db: Session, user_id: int):
    return (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

# ============================================================
# GET USER BY EMAIL
# ============================================================

def get_user_by_email(db: Session, email: str):
    return (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

# ============================================================
# LIST USERS (OPTIONAL FILTERS)
# ============================================================

def list_users(db: Session, role: str | None = None, disabled: bool | None = None):
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)

    if disabled is not None:
        query = query.filter(User.disabled == disabled)

    return query.all()

# ============================================================
# UPDATE USER
# ============================================================

def update_user(db: Session, user_id: int, payload):
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    if payload.email:
        user.email = payload.email

    if payload.full_name:
        user.full_name = payload.full_name

    if payload.role:
        user.role = payload.role

    if payload.disabled is not None:
        user.disabled = payload.disabled

    user.updated_at = datetime.utcnow()

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ============================================================
# DISABLE USER
# ============================================================

def disable_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    user.disabled = True
    user.updated_at = datetime.utcnow()

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# ============================================================
# DELETE USER (FULL CASCADE)
# ============================================================

def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True
