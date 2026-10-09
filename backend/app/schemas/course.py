import uuid
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import ListQuery, RequestModel, ResponseModel, UtcInstant, normalized
from app.utils.normalize import normalize_code, normalize_name

CourseCode = Annotated[
    str, normalized(normalize_code), Field(pattern=r"^[A-Z0-9][A-Z0-9-]{1,11}$")
]
Title = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=150)]
Department = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=100)]
CreditHours = Annotated[int, Field(ge=1, le=6)]
Status = Literal["active", "inactive"]


class CourseCreate(RequestModel):
    code: CourseCode
    title: Title
    credit_hours: CreditHours
    department: Department
    status: Status = "active"


class CourseUpdate(RequestModel):
    code: CourseCode | None = None
    title: Title | None = None
    credit_hours: CreditHours | None = None
    department: Department | None = None
    status: Status | None = None


class CourseOut(ResponseModel):
    id: uuid.UUID
    code: str
    title: str
    credit_hours: int
    department: str
    status: str
    assigned_count: int
    slot_count: int
    created_at: UtcInstant
    updated_at: UtcInstant


class CourseListQuery(ListQuery):
    status: Status | None = None
    department: str | None = Field(default=None, min_length=1, max_length=100)
    sort: Literal["code", "title", "department", "created_at"] = "code"
    order: Literal["asc", "desc"] = "asc"
