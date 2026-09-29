from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User
from app.core.roles import require_role
from app.schemas.user import UserCreate, UserResponse

# ⭐ Audit logging
from app.core.audit import log_audit

router = APIRouter(
    prefix="/admin/users",
    tags=["Users"],
    dependencies=[Depends(require_role("admin"))],
)

# ============================================================
# LIST USERS
# ============================================================

@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            access_token=""
        )
        for u in users
    ]

# ============================================================
# CREATE USER (with audit logging)
# ============================================================

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    from app.core.security import hash_password, create_access_token

    hashed_pw = hash_password(payload.password)

    new_user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role=payload.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # ⭐ AUDIT LOG — user created
    log_audit(
        db,
        user_id=current_user.id,
        action="user_created",
        resource_type="user",
        resource_id=new_user.id,
        details=f"Created user {new_user.email} with role {new_user.role}",
    )

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        access_token=create_access_token({"sub": new_user.id, "role": new_user.role}),
    )

# ============================================================
# UPDATE USER ROLE (with tightened audit logging)
# ============================================================

@router.patch("/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_role = user.role
    new_role = role

    # ============================================================
    # PRIVILEGE ESCALATION PROTECTION
    # ============================================================

    # Admin cannot modify superadmin
    if current_user.role == "admin" and user.role == "superadmin":
        log_audit(
            db,
            user_id=current_user.id,
            action="role_change_blocked",
            resource_type="user",
            resource_id=user.id,
            details=f"BLOCKED: Admin attempted to modify superadmin {user.email}",
        )
        raise HTTPException(status_code=403, detail="Admins cannot modify superadmin accounts")

    # Admin cannot assign superadmin role
    if current_user.role == "admin" and new_role == "superadmin":
        log_audit(
            db,
            user_id=current_user.id,
            action="role_change_blocked",
            resource_type="user",
            resource_id=user.id,
            details=f"BLOCKED: Admin attempted to assign superadmin role to {user.email}",
        )
        raise HTTPException(status_code=403, detail="Admins cannot assign superadmin role")

    # ============================================================
    # APPLY ROLE CHANGE
    # ============================================================

    user.role = new_role

    db.add(user)
    db.commit()
    db.refresh(user)

    # ============================================================
    # AUDIT LOG — role changed
    # ============================================================

    log_audit(
        db,
        user_id=current_user.id,
        action="user_role_changed",
        resource_type="user",
        resource_id=user.id,
        details=f"Changed role from {old_role} → {new_role} for user {user.email}",
    )

    from app.core.security import create_access_token

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        access_token=create_access_token({"sub": user.id, "role": user.role}),
    )

# ============================================================
# DELETE USER (with audit logging)
# ============================================================

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin"))
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Admin cannot delete superadmin
    if current_user.role == "admin" and user.role == "superadmin":
        log_audit(
            db,
            user_id=current_user.id,
            action="user_delete_blocked",
            resource_type="user",
            resource_id=user.id,
            details=f"BLOCKED: Admin attempted to delete superadmin {user.email}",
        )
        raise HTTPException(status_code=403, detail="Admins cannot delete superadmin accounts")

    email = user.email

    db.delete(user)
    db.commit()

    # ⭐ AUDIT LOG — user deleted
    log_audit(
        db,
        user_id=current_user.id,
        action="user_deleted",
        resource_type="user",
        resource_id=user_id,
        details=f"Deleted user {email}",
    )

    return
