from sqlalchemy.orm import Session

from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.core.audit import log_audit

# Agents
from app.agents.compliance_agent import ComplianceAgent
from app.agents.business_agent import BusinessAgent
from app.agents.reporting_agent import ReportingAgent
from app.agents.email_agent import EmailAgent

# Maintenance Agent
from app.agents.maintenance_agent import MaintenanceAgent


def run_workflow_triggers(
    db: Session,
    workflow_id: int,
    user_id: int,
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        return

    # Mark workflow as in progress
    workflow.status = "in_progress"
    db.commit()

    steps = db.query(WorkflowStep).filter(
        WorkflowStep.workflow_id == workflow_id
    ).order_by(WorkflowStep.order).all()

    for step in steps:
        step_name_lower = step.name.lower()

        try:
            if "verify current status" in step_name_lower:
                _trigger_compliance_agent(db, user_id, workflow, step, "verify_status")

            elif "renewal" in step_name_lower:
                _trigger_business_agent(db, user_id, workflow, step, "check_renewal")

            elif "report" in step_name_lower:
                _trigger_reporting_agent(db, user_id, workflow, step, "generate_report")

            elif "email" in step_name_lower or "notify" in step_name_lower:
                _trigger_email_agent(db, user_id, workflow, step, "send_email")

            else:
                _trigger_generic_agent(db, user_id, workflow, step, "generic_step")

        except Exception as e:
            # Mark step failed
            step.status = "failed"
            db.commit()

            log_audit(
                db,
                user_id,
                "workflow_step_failed",
                "workflow_step",
                step.id,
                f"Step '{step.name}' failed: {str(e)}"
            )

            # Automatic healing
            MaintenanceAgent.auto(db, workflow, user_id)

            # Mark workflow as needing attention
            workflow.status = "needs_attention"
            db.commit()

            return  # stop further execution

    # After all steps processed, check completion
    _update_workflow_completion_status(db, workflow, user_id)


def _update_workflow_completion_status(db: Session, workflow: Workflow, user_id: int):
    """
    Marks workflow as completed if all steps are completed.
    Marks workflow as failed if any step is failed.
    """

    steps = db.query(WorkflowStep).filter(
        WorkflowStep.workflow_id == workflow.id
    ).all()

    if any(step.status == "failed" for step in steps):
        workflow.status = "failed"
        db.commit()

        log_audit(
            db,
            user_id,
            "workflow_marked_failed",
            "workflow",
            workflow.id,
            "Workflow marked as failed due to step failure."
        )
        return

    if all(step.status == "completed" for step in steps):
        workflow.status = "completed"
        db.commit()

        log_audit(
            db,
            user_id,
            "workflow_completed",
            "workflow",
            workflow.id,
            "Workflow completed successfully."
        )
        return

    # Otherwise still in progress
    workflow.status = "in_progress"
    db.commit()


def _trigger_compliance_agent(db, user_id, workflow, step, reason):
    log_audit(
        db, user_id,
        "agent_triggered_compliance",
        "workflow_step",
        step.id,
        f"Compliance agent trigger for workflow '{workflow.name}', step '{step.name}', reason='{reason}'"
    )
    ComplianceAgent(db, user_id).run(workflow, step)


def _trigger_business_agent(db, user_id, workflow, step, reason):
    log_audit(
        db, user_id,
        "agent_triggered_business",
        "workflow_step",
        step.id,
        f"Business agent trigger for workflow '{workflow.name}', step '{step.name}', reason='{reason}'"
    )
    BusinessAgent(db, user_id).run(workflow, step)


def _trigger_reporting_agent(db, user_id, workflow, step, reason):
    log_audit(
        db, user_id,
        "agent_triggered_reporting",
        "workflow_step",
        step.id,
        f"Reporting agent trigger for workflow '{workflow.name}', step '{step.name}', reason='{reason}'"
    )
    ReportingAgent(db, user_id).run(workflow, step)


def _trigger_email_agent(db, user_id, workflow, step, reason):
    log_audit(
        db, user_id,
        "agent_triggered_email",
        "workflow_step",
        step.id,
        f"Email agent trigger for workflow '{workflow.name}', step '{step.name}', reason='{reason}'"
    )
    EmailAgent(db, user_id).run(workflow, step)


def _trigger_generic_agent(db, user_id, workflow, step, reason):
    log_audit(
        db, user_id,
        "agent_triggered_generic",
        "workflow_step",
        step.id,
        f"Generic agent trigger for workflow '{workflow.name}', step '{step.name}', reason='{reason}'"
    )
