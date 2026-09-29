from typing import List, Optional
from pydantic import BaseModel

# ============================================================
# WORKFLOW STEP SCHEMAS
# ============================================================

class WorkflowStepBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: str

class WorkflowStepResponse(WorkflowStepBase):
    id: int
    order: int
    workflow_id: int

    class Config:
        from_attributes = True  # pydantic v2 replacement for orm_mode

class WorkflowStepUpdate(BaseModel):
    status: str

class WorkflowStepCreate(BaseModel):   # ⭐ NEW
    workflow_id: int
    name: str
    description: Optional[str] = None
    order: int

# ============================================================
# WORKFLOW SCHEMAS
# ============================================================

class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None

class WorkflowCreate(WorkflowBase):
    pass

class WorkflowResponse(WorkflowBase):
    id: int
    steps: List[WorkflowStepResponse] = []

    class Config:
        from_attributes = True
