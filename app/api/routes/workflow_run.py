from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog

# Import your agents
from app.agents.business_agent import BusinessAgent
from app.agents.email_agent import EmailAgent
from app.agents.reporting_agent import ReportingAgent

router = APIRouter(prefix="/admin/workflows", tags=["Admin Workflows"])


# Agent registry for dynamic loading
AGENT_REGISTRY = {
    "business": BusinessAgent(),
    "email": EmailAgent(),
    "reporting": ReportingAgent(),
}


@router.post("/run/{workflow_id}")
def run_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """
    Execute a workflow step-by-step using agent/action metadata.
    """

    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    steps = (
        db.query(WorkflowStep)
        .filter(WorkflowStep.workflow_id == workflow_id)
        .order_by(WorkflowStep.order.asc())
        .all()
    )

    if not steps:
        raise HTTPException(status_code=400, detail="Workflow has no steps")

    results = []

    for step in steps:
        step.status = "in_progress"
        db.commit()

        agent_name = step.agent
        action_name = step.action

        # Validate agent/action
        if not agent_name or not action_name:
            step.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Step {step.id} missing agent/action fields"
            )

        agent = AGENT_REGISTRY.get(agent_name)
        if not agent:
            step.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Agent '{agent_name}' not found"
            )

        action = getattr(agent, action_name, None)
        if not action:
            step.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=400,
                detail=f"Action '{action_name}' not found on agent '{agent_name}'"
            )

        # Execute agent action
        try:
            output = action(
                instructions=step.instructions,
                metadata=step.metadata
            )

            step.status = "completed"
            db.commit()

            results.append({
                "step_id": step.id,
                "title": step.title,
                "agent": agent_name,
                "action": action_name,
                "output": output
            })

            # Log execution
            db.add(AuditLog(
                action="workflow_step_executed",
                resource_type="workflow_step",
                resource_id=step.id,
                user_id=1,
                details=f"Executed {agent_name}.{action_name} with metadata {step.metadata}"
            ))
            db.commit()

        except Exception as e:
            step.status = "failed"
            db.commit()

            db.add(AuditLog(
                action="workflow_step_failed",
                resource_type="workflow_step",
                resource_id=step.id,
                user_id=1,
                details=str(e)
            ))
            db.commit()

            raise HTTPException(
                status_code=500,
                detail=f"Step {step.id} failed: {str(e)}"
            )

    workflow.status = "completed"
    db.commit()

    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "results": results
    }
