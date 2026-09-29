from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.core.audit import log_audit


def auto_create_workflows(db: Session, user_id: int, extracted_items: list):
    """
    Creates workflows + steps automatically based on extracted compliance items.
    Called by extraction endpoint.
    """

    created_workflows = []

    for item in extracted_items:
        workflow_name = f"{item['type'].capitalize()} Compliance - {item['name']}"

        # Create workflow
        workflow = Workflow(
            name=workflow_name,
            description=f"Auto-created workflow for {item['type']} '{item['name']}'",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        log_audit(
            db,
            user_id=user_id,
            action="workflow_auto_created",
            resource_type="workflow",
           resource_id=workflow.id,
            details=f"Auto-created workflow for {item['type'].capitalize()} '{item['name']}'",
        )

        # ⭐ NEW — include Email Notification step
        step_names = [
            "Verify current status",
            "Check renewal requirements",
            "Generate compliance report",
            "Send email notification",
        ]

        for order, step_name in enumerate(step_names, start=1):
            step = WorkflowStep(
                workflow_id=workflow.id,
                name=step_name,
                order=order,
                status="pending",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(step)
            db.commit()

        created_workflows.append(workflow)

    return created_workflows
