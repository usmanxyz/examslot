import uuid

from app.schemas.common import RequestModel, ResponseModel, UtcInstant


class BranchOption(ResponseModel):
    id: uuid.UUID
    code: str
    name: str
    city: str
    address: str
    contact_phone: str
    eligible: bool
    reason: str | None


class BranchOptionsOut(ResponseModel):
    can_select: bool
    current_branch_id: uuid.UUID | None
    items: list[BranchOption]


class BranchSelect(RequestModel):
    branch_id: uuid.UUID


class BranchSummary(ResponseModel):
    id: uuid.UUID
    code: str
    name: str
    city: str
    address: str
    contact_phone: str


class BranchSelectionOut(ResponseModel):
    branch: BranchSummary
    branch_selected_at: UtcInstant
    used_approval: bool
