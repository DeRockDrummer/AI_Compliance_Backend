from fastapi import APIRouter, Depends

# ⭐ FIXED IMPORT — backend.app → app
from app.core.security import verify_token

router = APIRouter()

@router.get("/")
def dashboard_home(user=Depends(verify_token)):
    return {
        "message": "Dashboard access granted",
        "user": dict(user)
    }
