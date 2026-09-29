from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.auth import get_current_user
from app.agents.maintenance_agent import MaintenanceAgent

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("/run/{workflow_id}")
def run_maintenance(
    workflow_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    return MaintenanceAgent.run(db, workflow_id, user.id)
