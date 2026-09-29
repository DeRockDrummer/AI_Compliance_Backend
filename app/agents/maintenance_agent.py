from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.core.audit import log_audit

# Correct agent imports — use .run(), not nonexistent functions
from app.agents.compliance_agent import ComplianceAgent
from app.agents.business_agent import BusinessAgent
from app.agents.reporting_agent import ReportingAgent
from app.agents.email_agent import EmailAgent


class MaintenanceAgent:

    @staticmethod
    def run(db: Session, workflow_id: int, user_id: int):
        """
        Manual override: run maintenance on a specific workflow.
        """

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            return {"error": "Workflow not found"}

        results = MaintenanceAgent._heal_workflow(db, workflow, user_id)

        log_audit(
            db,
            user_id,
            "maintenance_run",
            "workflow",
            workflow_id,
            details={"results": results}
        )

        return results


    @staticmethod
    def auto(db: Session, workflow: Workflow, user_id: int):
        """
        Automatic healing: triggered when a workflow step fails.
        """

        results = MaintenanceAgent._heal_workflow(db, workflow, user_id)

        log_audit(
            db,
            user_id,
            "maintenance_auto",
            "workflow",
            workflow.id,
            details={"results": results}
        )

        return results


    @staticmethod
    def _heal_workflow(db: Session, workflow: Workflow, user_id: int):
        """
        Core healing logic — re-run any incomplete or failed steps.
        """

        steps = db.query(WorkflowStep).filter(
            WorkflowStep.workflow_id == workflow.id
        ).order_by(WorkflowStep.order.asc()).all()

        results = []

        for step in steps:
            if step.status in ("completed", "skipped"):
                continue

            # Determine which agent should run
            if "verify current status" in step.name.lower():
                result = ComplianceAgent(db, user_id).run(workflow, step)

            elif "renewal" in step.name.lower():
                result = BusinessAgent(db, user_id).run(workflow, step)

            elif "report" in step.name.lower():
                result = ReportingAgent(db, user_id).run(workflow, step)

            elif "email" in step.name.lower() or "notify" in step.name.lower():
                result = EmailAgent(db, user_id).run(workflow, step)

            else:
                result = {"status": "unknown_step"}

            results.append({
                "step": step.name,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })

        return results
