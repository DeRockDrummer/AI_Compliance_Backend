from fastapi import Depends
from app.auth.security import get_current_user

def require_user(current_user = Depends(get_current_user)):
    return current_user
