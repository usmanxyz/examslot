import uuid
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import ListQuery, RequestModel, ResponseModel, UtcInstant, normalized
from app.utils.normalize import normalize_name

RequestType = Literal["branch_change", "date_sheet_change"]
Reason = Annotated[str, normalized(normalize_name), Field(min_length=10, max_length=1000)]
Remark = Annotated[str, normalized(normalize_name), Field(min_length=1, max_length=500)]


class StudentLabel(ResponseModel):
    id: uuid.UUID
    full_name: str
    registration_no: str


class RequestCreate(RequestModel):
    type: RequestType
    reason: Reason


class DecisionIn(RequestModel):
    remark: Remark | None = None


class RequestOut(ResponseModel):
    id: uuid.UUID
    type: str
    reason: str
    status: str
    admin_remark: str | None
    created_at: UtcInstant
    decided_at: UtcInstant | None
    used_at: UtcInstant | None


class AdminRequestOut(RequestOut):
    student: StudentLabel


class StudentRequestListQuery(ListQuery):
    q: None = None


class AdminRequestListQuery(ListQuery):
    status: Literal["pending", "approved", "rejected"] | None = None
    type: RequestType | None = None
    sort: Literal["created_at"] = "created_at"
    order: Literal["asc", "desc"] = "desc"
