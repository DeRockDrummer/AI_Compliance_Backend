from app.agents.business_agent import BusinessAgent
from app.agents.email_agent import EmailAgent
from app.agents.reporting_agent import ReportingAgent

"""
Agent Registry
Maps agent names (strings) to instantiated agent classes.
Used by the workflow runner for dynamic agent/action execution.
"""

AGENT_REGISTRY = {
    "business": BusinessAgent(),
    "email": EmailAgent(),
    "reporting": ReportingAgent(),
}
