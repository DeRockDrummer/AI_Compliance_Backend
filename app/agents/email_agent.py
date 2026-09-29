from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.core.audit import log_audit


class EmailAgent:
    """
    Email Outreach Agent
    - Sends compliance emails, reminders, follow-ups
    - Updates workflow steps
    - Logs all actions
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id

    def run(self, workflow: Workflow, step: WorkflowStep):
        """
        Main email agent entry point.
        """

        # Simulated email logic
        email_result = self._send_email(workflow, step)

        # Mark step as completed
        step.status = "completed"
        step.updated_at = datetime.utcnow()
        self.db.add(step)
        self.db.commit()

        # Log email result
        log_audit(
            self.db,
            user_id=self.user_id,
            action="email_agent_completed",
            resource_type="workflow_step",
           resource_id=step.id,
            details=f"Email agent completed step '{step.name}' with result: {email_result}",
        )

        return email_result

    def _send_email(self, workflow: Workflow, step: WorkflowStep):
        """
        Placeholder email logic.
        Later: SMTP, SendGrid, SES, templates, attachments.
        """

        return {
            "workflow": workflow.name,
            "step": step.name,
            "email_sent": True,
            "status": "email_dispatched",
            "timestamp": datetime.utcnow().isoformat(),
        }
