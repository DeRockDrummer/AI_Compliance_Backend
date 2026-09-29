from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.core.audit import log_audit


class ComplianceAgent:
    """
    Compliance Agent
    - Auto-checks expiration dates
    - Generates compliance status
    - Updates workflow steps
    - Logs all actions
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def run(self, workflow: Workflow, step: WorkflowStep):
        """
        Main compliance agent entry point.
        """

        # Simulated compliance check
        compliance_result = self._check_compliance_status(workflow, step)

        # Update step status
        step.status = "completed"
        step.updated_at = datetime.utcnow()
        self.db.add(step)
        self.db.commit()

        # Log compliance result
        log_audit(
            self.db,
            user_id=self.user_id,
            action="compliance_agent_completed",
            resource_type="workflow_step",
            resource_id=step.id,
            details=f"Compliance agent completed step '{step.name}' with result: {compliance_result}",
        )

        return compliance_result

    def _check_compliance_status(self, workflow: Workflow, step: WorkflowStep):
        """
        Placeholder logic for compliance checking.
        Later: parse extracted data, check expiration, validate documents.
        """

        # Simple simulated compliance output
        return {
            "workflow": workflow.name,
            "step": step.name,
            "status": "verified",
            "timestamp": datetime.utcnow().isoformat(),
        }
