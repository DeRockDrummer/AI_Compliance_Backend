from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.db.session import get_db
from app.db.models.onboarding import OnboardingSession
from app.db.models.onboarding_document import OnboardingDocument
from app.core.auth import get_current_user
from app.core.roles import require_roles, require_role
from app.core.audit import log_audit

router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============================================================
# START ONBOARDING (USER + ADMIN)
# ============================================================

@router.post(
    "/start",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_roles("user", "admin"))],
)
def start_onboarding(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    existing = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.user_id == current_user.id)
        .first()
    )

    if existing:
        log_audit(
            db,
            user_id=current_user.id,
            action="onboarding_start_attempt",
            resource_type="onboarding_session",
            resource_id=existing.id,
            resource_owner_id=current_user.id,
            details="Attempted to start onboarding but session already exists",
        )
        return {
            "onboarding": {
                "session_id": existing.id,
                "status": existing.status,
                "created_at": existing.created_at.isoformat(),
                "updated_at": existing.updated_at.isoformat(),
            },
            "message": "Onboarding already started",
        }

    session = OnboardingSession(
        user_id=current_user.id,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    log_audit(
        db,
        user_id=current_user.id,
        action="onboarding_started",
        resource_type="onboarding_session",
        resource_id=session.id,
        resource_owner_id=current_user.id,
        details="New onboarding session created",
    )

    return {
        "onboarding": {
            "session_id": session.id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        },
        "message": "Onboarding started",
    }

# ============================================================
# GET ONBOARDING STATUS (USER + ADMIN)
# ============================================================

@router.get(
    "/status",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("user", "admin"))],
)
def onboarding_status(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No onboarding session found"
        )

    log_audit(
        db,
        user_id=current_user.id,
        action="onboarding_status_view",
        resource_type="onboarding_session",
        resource_id=session.id,
        resource_owner_id=current_user.id,
        details="Viewed onboarding status",
    )

    return {
        "onboarding": {
            "session_id": session.id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        }
    }

# ============================================================
# LIST USER DOCUMENTS (USER + ADMIN)
# ============================================================

@router.get(
    "/documents",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("user", "admin"))],
)
def list_documents(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding session not found"
        )

    docs = (
        db.query(OnboardingDocument)
        .filter(OnboardingDocument.session_id == session.id)
        .all()
    )

    log_audit(
        db,
        user_id=current_user.id,
        action="onboarding_documents_list",
        resource_type="onboarding_document",
        resource_owner_id=current_user.id,
        details=f"Listed {len(docs)} onboarding documents",
    )

    return [
        {
            "id": d.id,
            "filename": d.filename,
            "filepath": d.filepath,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
        for d in docs
    ]

# ============================================================
# DOWNLOAD DOCUMENT (USER + ADMIN)
# ============================================================

@router.get(
    "/document/{document_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("user", "admin"))],
)
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = (
        db.query(OnboardingDocument)
        .filter(
            OnboardingDocument.id == document_id,
            OnboardingDocument.user_id == current_user.id,
        )
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if not os.path.exists(doc.filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file missing on disk"
        )

    log_audit(
        db,
        user_id=current_user.id,
        action="onboarding_document_download",
        resource_type="onboarding_document",
        resource_id=doc.id,
        resource_owner_id=current_user.id,
        details=f"Downloaded onboarding document '{doc.filename}'",
    )

    return FileResponse(
        doc.filepath,
        filename=doc.filename,
        media_type="application/octet-stream",
    )

# ============================================================
# DELETE DOCUMENT (USER + ADMIN)
# ============================================================

@router.delete(
    "/document/{document_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("user", "admin"))],
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    doc = (
        db.query(OnboardingDocument)
        .filter(
            OnboardingDocument.id == document_id,
            OnboardingDocument.user_id == current_user.id,
        )
        .first()
    )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Remove file from disk
    if os.path.exists(doc.filepath):
        try:
            os.remove(doc.filepath)
        except Exception:
            # If file removal fails, still remove DB record but log it
            log_audit(
                db,
                user_id=current_user.id,
                action="onboarding_document_file_delete_failed",
                resource_type="onboarding_document",
                resource_id=doc.id,
                resource_owner_id=current_user.id,
                details=f"Failed to delete file for document '{doc.filename}'",
            )

    # Remove DB record
    session = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.id == doc.session_id)
        .first()
    )

    db.delete(doc)
    db.commit()

    # Update session status if needed
    if session:
        remaining_docs = (
            db.query(OnboardingDocument)
            .filter(OnboardingDocument.session_id == session.id)
            .count()
        )
        session.status = "pending" if remaining_docs == 0 else "uploading"
        session.updated_at = datetime.utcnow()
        db.add(session)
        db.commit()

    log_audit(
        db,
        user_id=current_user.id,
        action="onboarding_document_deleted",
        resource_type="onboarding_document",
        resource_id=document_id,
        resource_owner_id=current_user.id,
        details=f"Deleted onboarding document '{doc.filename}'",
    )

    return {"message": "Document deleted"}

# ============================================================
# COMPLETE ONBOARDING (USER + ADMIN)
# ============================================================

@router.post(
    "/complete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_roles("user", "admin"))],
)
def complete_onboarding(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.user_id == current_user.id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding session not found"
        )

    # Optional: require at least one document before completion
    docs_count = (
        db.query(OnboardingDocument)
        .filter(OnboardingDocument.session_id == session.id)
        .count()
    )

    if docs_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete onboarding without documents"
        )

    session.status = "completed"
    session.updated_at = datetime.utcnow()

    db.add(session)
    db.commit()
    db.refresh(session)

    log_audit(
        db,
        user_id=current_user.id,
        action="onboarding_completed",
        resource_type="onboarding_session",
        resource_id=session.id,
        resource_owner_id=current_user.id,
        details=f"Onboarding completed by {current_user.email}",
    )

    # 🔗 Hook point for workflows / extraction:
    # - create workflow steps
    # - enqueue extraction jobs
    # - update compliance scores

    return {
        "message": "Onboarding completed",
        "onboarding": {
            "session_id": session.id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        },
    }

# ============================================================
# ADMIN: LIST ALL ONBOARDING SESSIONS
# ============================================================

@router.get(
    "/admin/sessions",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def admin_list_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    sessions = db.query(OnboardingSession).all()

    log_audit(
        db,
        user_id=current_user.id,
        action="admin_onboarding_sessions_list",
        resource_type="onboarding_session",
        resource_owner_id=current_user.id,
        details=f"Admin listed {len(sessions)} onboarding sessions",
    )

    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "status": s.status,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]

# ============================================================
# ADMIN: VIEW USER ONBOARDING + DOCUMENTS
# ============================================================

@router.get(
    "/admin/user/{user_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin"))],
)
def admin_view_user_onboarding(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = (
        db.query(OnboardingSession)
        .filter(OnboardingSession.user_id == user_id)
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding session not found for user"
        )

    docs = (
        db.query(OnboardingDocument)
        .filter(OnboardingDocument.session_id == session.id)
        .all()
    )

    log_audit(
        db,
        user_id=current_user.id,
        action="admin_onboarding_user_view",
        resource_type="onboarding_session",
        resource_id=session.id,
        resource_owner_id=user_id,
        details=f"Admin viewed onboarding for user_id={user_id}",
    )

    return {
        "session": {
            "id": session.id,
            "user_id": session.user_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
        },
        "documents": [
            {
                "id": d.id,
                "filename": d.filename,
                "filepath": d.filepath,
                "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
            for d in docs
        ],
    }
