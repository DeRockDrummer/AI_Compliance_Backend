from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
import hashlib
import secrets

from app.core.config import settings

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

bearer_scheme = HTTPBearer(auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ============================================================
# ACCESS TOKEN CREATION
# ============================================================

def create_access_token(data: dict):
    """
    Creates a JWT access token with:
    - sub (user_id, as string)
    - role (e.g. 'admin', 'superadmin')
    - exp (expiration)
    - iat (issued at)
    """
    to_encode = data.copy()

    # Ensure sub is always a string
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    # Ensure role is present; default to 'admin' if missing
    if "role" not in to_encode or to_encode["role"] is None:
        to_encode["role"] = "admin"

    to_encode["iat"] = datetime.utcnow()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============================================================
# REFRESH TOKEN UTILITIES
# ============================================================

def generate_refresh_token():
    return secrets.token_urlsafe(64)

def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def refresh_token_expiry():
    return datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

# ============================================================
# ACCESS TOKEN DECODING (STRICT)
# ============================================================

def decode_access_token(token: str):
    """
    Full decode with strict error raising.
    Used by login, refresh, and protected routes.
    """
    try:
        jwt.get_unverified_header(token)
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired or invalid"
        )

# ============================================================
# LIGHTWEIGHT VERIFY (USED BY get_current_user / roles)
# ============================================================

def verify_access_token(token: str):
    """
    Lightweight verification used by get_current_user() and role checks.
    Returns payload dict or None.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

# ============================================================
# TOKEN EXTRACTION FROM HEADER
# ============================================================

def get_token(credentials=Depends(bearer_scheme)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token"
        )
    return credentials.credentials
