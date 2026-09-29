from pydantic import BaseModel, EmailStr


# ============================================================
# Base User Schema
# ============================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str


# ============================================================
# User Creation Schema
# ============================================================

class UserCreate(UserBase):
    password: str


# ============================================================
# User Login Schema
# ============================================================

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ============================================================
# User Response Schema (returned to client)
# ============================================================

class UserResponse(UserBase):
    id: int
    access_token: str | None = None

    class Config:
        from_attributes = True
