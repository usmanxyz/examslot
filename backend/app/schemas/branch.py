import uuid
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import ListQuery, RequestModel, ResponseModel, UtcInstant, normalized
from app.utils.normalize import normalize_code, normalize_name, normalize_phone

BranchCode = Annotated[
    str, normalized(normalize_code), Field(pattern=r"^[A-Z0-9][A-Z0-9-]{1,9}$")
]
BranchName = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=120)]
City = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=80)]
Address = Annotated[str, normalized(normalize_name), Field(min_length=5, max_length=255)]
ContactPhone = Annotated[
    str, normalized(normalize_phone), Field(pattern=r"^\+92[0-9]{9,10}$")
]
Status = Literal["active", "inactive"]


class BranchCreate(RequestModel):
    code: BranchCode
    name: BranchName
    city: City
    address: Address
    contact_phone: ContactPhone
    status: Status = "active"


class BranchUpdate(RequestModel):
    code: BranchCode | None = None
    name: BranchName | None = None
    city: City | None = None
    address: Address | None = None
    contact_phone: ContactPhone | None = None
    status: Status | None = None


class BranchOut(ResponseModel):
    id: uuid.UUID
    code: str
    name: str
    city: str
    address: str
    contact_phone: str
    status: str
    student_count: int
    created_at: UtcInstant
    updated_at: UtcInstant


class BranchListQuery(ListQuery):
    status: Status | None = None
    sort: Literal["code", "name", "city", "created_at"] = "code"
    order: Literal["asc", "desc"] = "asc"
