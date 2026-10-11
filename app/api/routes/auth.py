from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken

from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate, UserResponse

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    generate_refresh_token,
    hash_refresh_token,
    refresh_token_expiry,
)

from app.core.roles import require_roles

router = APIRouter(tags=["Authentication"])

COOKIE_PATH = "/"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days

# ============================================================
# SHARED DEPENDENCY — CURRENT USER (COOKIE + HEADER)
# ============================================================

async def get_current_user_cookie(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    auth_header = request.headers.get("Authorization")
    token = None

    # Bearer header
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]

    # Refresh cookie fallback
    if not token:
        raw_refresh = request.cookies.get("refresh_token")
        if raw_refresh:
            hashed = hash_refresh_token(raw_refresh)

            result = await db.execute(
                select(RefreshToken).where(
                    RefreshToken.token_hash == hashed,
                    RefreshToken.revoked == False
                )
            )
            rt = result.scalar_one_or_none()

            if rt and rt.expires_at > datetime.utcnow():
                result = await db.execute(
                    select(User).where(User.id == rt.user_id)
                )
                user = result.scalar_one_or_none()

                token = create_access_token({"sub": user.id, "role": user.role})

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = verify_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = int(payload["sub"])

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.disabled:
        raise HTTPException(status_code=403, detail="User account disabled")

    return user

# ============================================================
# REGISTER
# ============================================================

@router.post("/register", response_model=UserResponse)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(payload.password)
    role = payload.role or "admin"

    new_user = User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role=role,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token({"sub": new_user.id, "role": new_user.role})

    raw_refresh = generate_refresh_token()
    hashed = hash_refresh_token(raw_refresh)
    expires_at = refresh_token_expiry()

    rt = RefreshToken(
        user_id=new_user.id,
        token_hash=hashed,
        expires_at=expires_at
    )

    db.add(rt)
    await db.commit()

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        access_token=access_token
    )

# ============================================================
# LOGIN — COOKIE VERSION
# ============================================================

@router.post("/login")
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.id, "role": user.role})

    raw_refresh = generate_refresh_token()
    hashed = hash_refresh_token(raw_refresh)
    expires_at = refresh_token_expiry()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hashed,
        expires_at=expires_at
    )

    db.add(rt)
    await db.commit()

    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        path=COOKIE_PATH,
        max_age=COOKIE_MAX_AGE
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
    }

# ============================================================
# REFRESH — COOKIE VERSION
# ============================================================

@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_refresh = request.cookies.get("refresh_token")

    if not raw_refresh:
        raise HTTPException(status_code=401, detail="Unauthorized")

    hashed = hash_refresh_token(raw_refresh)

    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
    rt = result.scalar_one_or_none()

    if not rt or rt.revoked or rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Unauthorized")

    result = await db.execute(select(User).where(User.id == rt.user_id))
    user = result.scalar_one_or_none()

    # Revoke old token
    rt.revoked = True
    db.add(rt)
    await db.commit()

    # Create new refresh token
    new_raw = generate_refresh_token()
    new_hashed = hash_refresh_token(new_raw)
    new_expires = refresh_token_expiry()

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hashed,
        expires_at=new_expires
    )

    db.add(new_rt)
    await db.commit()

    access_token = create_access_token({"sub": user.id, "role": user.role})

    response.set_cookie(
        key="refresh_token",
        value=new_raw,
        httponly=True,
        secure=False,
        samesite="lax",
        path=COOKIE_PATH,
        max_age=COOKIE_MAX_AGE
    )

    return {"access_token": access_token, "role": user.role}

# ============================================================
# LOGOUT — COOKIE VERSION
# ============================================================

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    raw_refresh = request.cookies.get("refresh_token")

    if raw_refresh:
        hashed = hash_refresh_token(raw_refresh)

        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed))
        rt = result.scalar_one_or_none()

        if rt:
            rt.revoked = True
            db.add(rt)
            await db.commit()

    response.delete_cookie(key="refresh_token", path=COOKIE_PATH)

    return {"detail": "Logged out"}

# ============================================================
# GET CURRENT USER (FOR FRONTEND /auth/me)
# ============================================================

@router.get("/auth/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    user = await get_current_user_cookie(request, db)

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "disabled": user.disabled,
    }

# ============================================================
# ROLE-PROTECTED EXAMPLES
# ============================================================

@router.get("/admin/dashboard")
async def admin_dashboard(current_user = Depends(require_roles("admin", "superadmin"))):
    return {
        "message": "Admin or Superadmin dashboard access granted",
        "user": current_user.email,
        "role": current_user.role
    }

@router.get("/manager/reports")
async def manager_reports(current_user = Depends(require_roles("admin", "manager", "superadmin"))):
    return {
        "message": "Manager/Admin/Superadmin access granted",
        "user": current_user.email,
        "role": current_user.role
    }

# ============================================================
# ADMIN — CREATE NEW ADMIN USER
# ============================================================

@router.post("/admin/create", dependencies=[Depends(require_roles("admin", "superadmin"))])
async def create_admin(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = hash_password(payload.password)

    new_admin = User(
        email=payload.email,
        hashed_password=hashed_pw,
        full_name=payload.full_name,
        role="admin"
    )

    db.add(new_admin)
    await db.commit()
    await db.refresh(new_admin)

    return {
        "id": new_admin.id,
        "email": new_admin.email,
        "full_name": new_admin.full_name,
        "role": new_admin.role
    }
