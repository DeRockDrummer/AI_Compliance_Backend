import sqlite3
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import hash_password, verify_password, create_access_token
from app.db.init_db import DB_PATH

router = APIRouter()

class RegisterPayload(BaseModel):
    email: str
    password: str

class LoginPayload(BaseModel):
    email: str
    password: str


@router.post("/register")
def register_user(payload: RegisterPayload):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (payload.email,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return {"detail": "Email already registered"}

    # Hash password
    hashed = hash_password(payload.password)

    # Insert new user
    cursor.execute(
        "INSERT INTO users (email, password) VALUES (?, ?)",
        (payload.email, hashed)
    )
    conn.commit()

    # Create token
    token = create_access_token(payload.email)
    conn.close()

    return {"access_token": token, "token_type": "bearer"}


@router.post("/login")
def login_user(payload: LoginPayload):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # ⭐ ensures dict-style access
    cursor = conn.cursor()

    # Look up user
    cursor.execute("SELECT * FROM users WHERE email = ?", (payload.email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"detail": "Invalid email or password"}

    # Correct column access
    stored_password = user["password"]

    # Verify password
    if not verify_password(payload.password, stored_password):
        conn.close()
        return {"detail": "Invalid email or password"}

    # Create token
    token = create_access_token(payload.email)
    conn.close()

    return {"access_token": token, "token_type": "bearer"}
