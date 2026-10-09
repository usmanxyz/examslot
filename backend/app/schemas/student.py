import uuid
from datetime import date
from typing import Annotated, Literal

from pydantic import EmailStr, Field

from app.schemas.common import (
    DecimalString,
    ListQuery,
    RequestModel,
    ResponseModel,
    UtcInstant,
    normalized,
)
from app.utils.normalize import (
    normalize_cnic,
    normalize_code,
    normalize_email,
    normalize_mobile,
    normalize_name,
    normalize_phone,
)

Email = Annotated[EmailStr, normalized(normalize_email), Field(max_length=254)]
FullName = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=120)]
Mobile = Annotated[str, normalized(normalize_mobile), Field(pattern=r"^\+923[0-9]{9}$")]
AnyPhone = Annotated[str, normalized(normalize_phone), Field(pattern=r"^\+92[0-9]{9,10}$")]
Cnic = Annotated[str, normalized(normalize_cnic), Field(pattern=r"^[0-9]{13}$")]
RegistrationNo = Annotated[
    str, normalized(normalize_code), Field(pattern=r"^[A-Z0-9][A-Z0-9-]{3,29}$")
]
Address = Annotated[str, normalized(normalize_name), Field(min_length=5, max_length=255)]
Occupation = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=100)]
Program = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=120)]
Session = Annotated[str, normalized(normalize_name), Field(min_length=4, max_length=30)]
Qualification = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=120)]
Institute = Annotated[str, normalized(normalize_name), Field(min_length=2, max_length=150)]
Semester = Annotated[int, Field(ge=1, le=12)]
Gender = Literal["female", "male", "transgender", "prefer_not_to_say"]
ScoreType = Literal["percentage", "cgpa"]
Score = Annotated[DecimalString, Field(ge=0, le=100, decimal_places=2)]

EARLIEST_BIRTH_DATE = date(1940, 1, 1)
MINIMUM_AGE_YEARS = 14


class BranchSummary(ResponseModel):
    id: uuid.UUID
    code: str
    name: str
    city: str
    address: str
    contact_phone: str


class BranchLabel(ResponseModel):
    code: str
    name: str


class LatestLinkOut(ResponseModel):
    purpose: str
    delivery_status: str | None
    created_at: UtcInstant
    expires_at: UtcInstant
    used_at: UtcInstant | None


class StudentCreate(RequestModel):
    full_name: FullName
    email: Email
    phone: Mobile
    cnic: Cnic
    date_of_birth: date
    gender: Gender
    address: Address
    guardian_name: FullName
    guardian_cnic: Cnic
    guardian_occupation: Occupation
    guardian_phone: Mobile
    emergency_phone: AnyPhone
    registration_no: RegistrationNo
    program: Program
    semester: Semester
    session: Session
    previous_qualification: Qualification
    previous_institute: Institute
    previous_score_type: ScoreType
    previous_score: Score


class StudentUpdate(RequestModel):
    full_name: FullName | None = None
    email: Email | None = None
    phone: Mobile | None = None
    cnic: Cnic | None = None
    date_of_birth: date | None = None
    gender: Gender | None = None
    address: Address | None = None
    guardian_name: FullName | None = None
    guardian_cnic: Cnic | None = None
    guardian_occupation: Occupation | None = None
    guardian_phone: Mobile | None = None
    emergency_phone: AnyPhone | None = None
    registration_no: RegistrationNo | None = None
    program: Program | None = None
    semester: Semester | None = None
    session: Session | None = None
    previous_qualification: Qualification | None = None
    previous_institute: Institute | None = None
    previous_score_type: ScoreType | None = None
    previous_score: Score | None = None


class StudentDetailOut(ResponseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str
    cnic: str
    date_of_birth: date
    gender: str
    address: str
    has_photo: bool
    guardian_name: str
    guardian_cnic: str
    guardian_occupation: str
    guardian_phone: str
    emergency_phone: str
    registration_no: str
    program: str
    semester: int
    session: str
    previous_qualification: str
    previous_institute: str
    previous_score_type: str
    previous_score: DecimalString
    status: str
    account_status: str
    progress: str
    branch: BranchSummary | None
    branch_selected_at: UtcInstant | None
    date_sheet_saved_at: UtcInstant | None
    assigned_course_count: int
    can_change_branch: bool
    can_change_date_sheet: bool
    latest_link: LatestLinkOut | None
    last_login_at: UtcInstant | None
    created_at: UtcInstant
    updated_at: UtcInstant


class StudentListItem(ResponseModel):
    id: uuid.UUID
    full_name: str
    registration_no: str
    program: str
    semester: int
    account_status: str
    progress: str
    branch: BranchLabel | None
    assigned_course_count: int
    created_at: UtcInstant


class StudentListQuery(ListQuery):
    account_status: Literal["active", "invited", "inactive"] | None = None
    progress: Literal["assignment_incomplete", "branch_pending", "planning", "saved"] | None = None
    branch_id: uuid.UUID | None = None
    program: str | None = Field(default=None, min_length=1, max_length=120)
    sort: Literal["created_at", "full_name", "registration_no"] = "created_at"
    order: Literal["asc", "desc"] = "desc"


class SetupLinkOut(ResponseModel):
    latest_link: LatestLinkOut | None


class StudentProfileOut(ResponseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str
    cnic: str
    date_of_birth: date
    gender: str
    address: str
    has_photo: bool
    guardian_name: str
    guardian_cnic: str
    guardian_occupation: str
    guardian_phone: str
    emergency_phone: str
    registration_no: str
    program: str
    semester: int
    session: str
    previous_qualification: str
    previous_institute: str
    previous_score_type: str
    previous_score: DecimalString
    branch: BranchSummary | None
    branch_selected_at: UtcInstant | None
    progress: str
    assigned_course_count: int
    date_sheet_saved_at: UtcInstant | None
    can_change_branch: bool
    can_change_date_sheet: bool
    pending_request_types: list[str]


class AdminProfileOut(ResponseModel):
    id: uuid.UUID
    full_name: str
    email: str
