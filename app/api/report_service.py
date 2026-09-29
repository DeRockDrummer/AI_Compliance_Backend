from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from datetime import datetime

from app.db.session import get_db
from app.core.roles import require_role
from app.core.audit import log_audit

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])

# ============================================================
# RESOLVED REPORT DIRECTORY
# ============================================================

REPORT_DIR = os.path.join(os.getcwd(), "reports")

def resolve_path(filename: str) -> str:
    return os.path.join(REPORT_DIR, filename)

# ============================================================
# PDF REPORT DOWNLOAD
# ============================================================

@router.get("/pdf", dependencies=[Depends(require_role("admin"))])
def download_pdf_report(db: Session = Depends(get_db)):
    pdf_path = resolve_path("compliance_report.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF report not found")

    # Audit
    log_audit(
        db,
        user_id=None,
        action="download_pdf_report",
        resource_type="report",
        resource_id=None,
        details=f"PDF report downloaded at {datetime.utcnow().isoformat()}",
    )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename="compliance_report.pdf"
    )

# ============================================================
# DOCX REPORT DOWNLOAD
# ============================================================

@router.get("/docx", dependencies=[Depends(require_role("admin"))])
def download_docx_report(db: Session = Depends(get_db)):
    docx_path = resolve_path("compliance_report.docx")

    if not os.path.exists(docx_path):
        raise HTTPException(status_code=404, detail="DOCX report not found")

    # Audit
    log_audit(
        db,
        user_id=None,
        action="download_docx_report",
        resource_type="report",
        resource_id=None,
        details=f"DOCX report downloaded at {datetime.utcnow().isoformat()}",
    )

    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="compliance_report.docx"
    )
