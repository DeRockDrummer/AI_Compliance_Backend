from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
import os
from datetime import datetime

from app.db.session import get_db
from app.db.models.onboarding import OnboardingSession
from app.db.models.onboarding_document import OnboardingDocument
from app.core.roles import require_roles
from app.core.auth import get_current_user
from app.core.audit import log_audit

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(
    tags=["Upload"]
)

# ============================================================
# UPLOAD DOCUMENT (USER + ADMIN)
# ============================================================

@router.post(
    "/document",
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Security(get_current_user),   # JWT already validated
):
    # REMOVE: require_roles("user", "admin")(current_user)

    session = db.query(OnboardingSession).filter(
        OnboardingSession.user_id == current_user.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No onboarding session found"
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file"
        )

    filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(await file.read())

    doc = OnboardingDocument(
        user_id=current_user.id,
        session_id=session.id,
        filename=file.filename,
        filepath=filepath,
        uploaded_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    session.status = "uploading"
    session.updated_at = datetime.utcnow()
    db.add(session)
    db.commit()

    log_audit(
        db,
        user_id=current_user.id,
        action="document_uploaded",
        resource_type="onboarding_document",
        resource_id=doc.id,
        details=f"Uploaded document '{file.filename}'",
    )

    return {
        "message": "Document uploaded successfully",
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "filepath": doc.filepath,
            "uploaded_at": doc.uploaded_at.isoformat(),
        },
        "session": {
            "id": session.id,
            "status": session.status,
            "updated_at": session.updated_at.isoformat(),
        },
    }

