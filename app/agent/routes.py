from fastapi import APIRouter, Depends
from pydantic import BaseModel

# ⭐ FIXED IMPORT — backend.app → app
from app.core.security import verify_token

router = APIRouter()

class AgentRequest(BaseModel):
    prompt: str

@router.post("/run")
def run_agent(payload: AgentRequest, user=Depends(verify_token)):
    # Example agent logic — replace with your real implementation
    return {
        "message": "Agent executed",
        "input": payload.prompt,
        "user": dict(user)
    }
