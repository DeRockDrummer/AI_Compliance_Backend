from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import sqlite3

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

def get_db():
    conn = sqlite3.connect("test.db")
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/register")
def register_user(data: RegisterRequest):
    conn = get_db()
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT * FROM users WHERE email = ?", (data.email,))
    existing = cursor.fetchone()

    if existing:
        raise HTTPException(status_code=400, detail="User already exists.")

    # Hash password
    hashed_pw = pwd_context.hash(data.password)

    # Insert new user with trial start date
    cursor.execute(
        "INSERT INTO users (email, password, trial_start) VALUES (?, ?, DATE('now'))",
        (data.email, hashed_pw)
    )
    conn.commit()

    return {"message": "Registration successful"}
