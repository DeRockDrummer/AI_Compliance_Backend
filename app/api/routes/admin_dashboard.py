from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models.workflow import Workflow
from app.db.models.workflow_step import WorkflowStep
from app.db.models.audit_log import AuditLog
from app.db.models.onboarding import OnboardingSession
from app.db.models.onboarding_document import OnboardingDocument
from app.db.models.extracted_data import ExtractedData

router = APIRouter(prefix="/admin/dashboard", tags=["Admin Dashboard"])


@router.get("")
def admin_dashboard(db: Session = Depends(get_db)):
    """
    Full enterprise dashboard payload.
    """

    # ============================================================
    # WORKFLOW METRICS
    # ============================================================

    total_workflows = db.query(Workflow).count()
    completed_workflows = db.query(Workflow).filter(Workflow.status == "completed").count()
    in_progress_workflows = db.query(Workflow).filter(Workflow.status == "in_progress").count()
    paused_workflows = db.query(Workflow).filter(Workflow.status == "paused").count()
    cancelled_workflows = db.query(Workflow).filter(Workflow.status == "cancelled").count()

    # ============================================================
    # STEP METRICS
    # ============================================================

    total_steps = db.query(WorkflowStep).count()
    completed_steps = db.query(WorkflowStep).filter(WorkflowStep.status == "completed").count()
    pending_steps = db.query(WorkflowStep).filter(WorkflowStep.status == "pending").count()
    failed_steps = db.query(WorkflowStep).filter(WorkflowStep.status == "failed").count()

    # ============================================================
    # AGENT METRICS
    # ============================================================

    agent_trigger_counts = {
        "compliance_agent": db.query(AuditLog).filter(AuditLog.action == "agent_triggered_compliance").count(),
        "business_agent": db.query(AuditLog).filter(AuditLog.action == "agent_triggered_business").count(),
        "reporting_agent": db.query(AuditLog).filter(AuditLog.action == "agent_triggered_reporting").count(),
        "email_agent": db.query(AuditLog).filter(AuditLog.action == "agent_triggered_email").count(),
        "generic_agent": db.query(AuditLog).filter(AuditLog.action == "agent_triggered_generic").count(),
    }

    agent_completion_counts = {
        "compliance_agent": db.query(AuditLog).filter(AuditLog.action == "compliance_agent_completed").count(),
        "business_agent": db.query(AuditLog).filter(AuditLog.action == "business_agent_completed").count(),
        "reporting_agent": db.query(AuditLog).filter(AuditLog.action == "reporting_agent_completed").count(),
        "email_agent": db.query(AuditLog).filter(AuditLog.action == "email_agent_completed").count(),
    }

    # ============================================================
    # EXTRACTION METRICS
    # ============================================================

    total_extractions = db.query(ExtractedData).count()
    total_documents_uploaded = db.query(OnboardingDocument).count()

    # ============================================================
    # ONBOARDING METRICS
    # ============================================================

    total_onboarding_sessions = db.query(OnboardingSession).count()

    # ============================================================
    # ERROR METRICS
    # ============================================================

    error_logs = db.query(AuditLog).filter(AuditLog.action.like("%error%")).count()
    failed_agent_runs = db.query(AuditLog).filter(AuditLog.action.like("%agent_failed%")).count()

    # ============================================================
    # RECENT AUDIT LOGS (last 20)
    # ============================================================

    recent_logs = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
        .all()
    )

    recent_logs_serialized = [
        {
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "timestamp": log.created_at,
            "user_id": log.user_id,
        }
        for log in recent_logs
    ]

    # ============================================================
    # LAST 24 HOURS ACTIVITY
    # ============================================================

    since_24h = datetime.utcnow() - timedelta(hours=24)

    last_24h_activity = (
        db.query(AuditLog)
        .filter(AuditLog.created_at >= since_24h)
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    last_24h_serialized = [
        {
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "timestamp": log.created_at,
        }
        for log in last_24h_activity
    ]

    # ============================================================
    # LAST 7 DAYS WORKFLOW TRENDS
    # ============================================================

    since_7d = datetime.utcnow() - timedelta(days=7)

    last_7d_completed = (
        db.query(Workflow)
        .filter(Workflow.status == "completed", Workflow.updated_at >= since_7d)
        .count()
    )

    last_7d_created = (
        db.query(Workflow)
        .filter(Workflow.created_at >= since_7d)
        .count()
    )

    # ============================================================
    # SYSTEM HEALTH
    # ============================================================

    system_health = {
        "database_connected": True,
        "workflow_engine_operational": True,
        "agent_system_operational": True,
        "last_updated": datetime.utcnow(),
    }

    # ============================================================
    # FINAL PAYLOAD
    # ============================================================

    return {
        "workflows": {
            "total": total_workflows,
            "completed": completed_workflows,
            "in_progress": in_progress_workflows,
            "paused": paused_workflows,
            "cancelled": cancelled_workflows,
        },
        "steps": {
            "total": total_steps,
            "completed": completed_steps,
            "pending": pending_steps,
            "failed": failed_steps,
        },
        "agents": {
            "trigger_counts": agent_trigger_counts,
            "completion_counts": agent_completion_counts,
        },
        "extraction": {
            "total_extractions": total_extractions,
            "documents_uploaded": total_documents_uploaded,
        },
        "onboarding": {
            "total_sessions": total_onboarding_sessions,
        },
        "errors": {
            "error_logs": error_logs,
            "failed_agent_runs": failed_agent_runs,
        },
        "recent_logs": recent_logs_serialized,
        "last_24h_activity": last_24h_serialized,
        "last_7d_trends": {
            "completed_workflows": last_7d_completed,
            "created_workflows": last_7d_created,
        },
        "system_health": system_health,
    }
