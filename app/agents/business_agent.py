from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.core.audit import log_audit


class BusinessAgent:
    """
    Business Agent
    - Handles renewal requirements
    - Executes business logic
    - Updates workflow steps
    - Logs all actions
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def run(self, workflow: Workflow, step: WorkflowStep):
        """
        Main business agent entry point.
        """

        # Simulated business logic
        business_result = self._process_renewal_requirements(workflow, step)

        # Mark step as completed
        step.status = "completed"
        step.updated_at = datetime.utcnow()
        self.db.add(step)
        self.db.commit()

        # Log business result
        log_audit(
            self.db,
            user_id=self.user_id,
            action="business_agent_completed",
            resource_type="workflow_step",
            resource_id=step.id,
            details=f"Business agent completed step '{step.name}' with result: {business_result}",
        )

        return business_result

    def _process_renewal_requirements(self, workflow: Workflow, step: WorkflowStep):
        """
        Placeholder business logic.
        Later: renewal rules, deadlines, client tasks, etc.
        """

        return {
            "workflow": workflow.name,
            "step": step.name,
            "renewal_required": True,
            "status": "renewal_checked",
            "timestamp": datetime.utcnow().isoformat(),
        }
