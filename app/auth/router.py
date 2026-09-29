from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.auth.hashing import hash_password, verify_password
from app.schemas.user import UserCreate, LoginRequest
from app.db.models.user import User
from app.db.session import get_db
from app.auth.tokens import create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================
# REGISTER
# ============================
@router.post("/register")
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}


# ============================
# LOGIN  ⭐ REQUIRED FOR COOKIES
# ============================
@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token({"sub": user.email})

    # CRITICAL: localhost-safe cookie settings
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,          # MUST be False on localhost
        samesite="lax",        # MUST be lax on localhost
        max_age=3600,
        path="/"
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,
        path="/"
    )

    return {"message": "Login successful"}
