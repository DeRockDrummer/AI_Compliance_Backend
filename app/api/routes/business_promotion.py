from fastapi import APIRouter, Depends
from app.agents.business_agent import BusinessAgent
from app.agents.email_agent import EmailAgent
from app.agents.reporting_agent import ReportingAgent
from app.core.auth import get_current_user
from app.core.audit import log_event

router = APIRouter(
    prefix="/agent/business",
    tags=["Business Promotion Agents"]
)

@router.post("/promote")
async def run_business_promotion(user=Depends(get_current_user)):
    agent = BusinessAgent()
    result = agent.run_promotion()
    log_event(user.id, "run_promotion", "business_agent", details=result)
    return {"status": "success", "result": result}

@router.post("/outreach")
async def run_outreach_campaign(user=Depends(get_current_user)):
    agent = EmailAgent()
    result = agent.run_outreach()
    log_event(user.id, "run_outreach", "email_agent", details=result)
    return {"status": "success", "result": result}

@router.post("/leadgen")
async def run_lead_generation(user=Depends(get_current_user)):
    agent = BusinessAgent()
    result = agent.generate_leads()
    log_event(user.id, "generate_leads", "business_agent", details=result)
    return {"status": "success", "result": result}

@router.post("/followup")
async def run_follow_up(user=Depends(get_current_user)):
    agent = EmailAgent()
    result = agent.run_followup()
    log_event(user.id, "run_followup", "email_agent", details=result)
    return {"status": "success", "result": result}
