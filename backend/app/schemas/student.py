import uuid
from datetime import date

from app.schemas.common import DecimalString, ResponseModel, UtcInstant


class BranchOut(ResponseModel):
    id: uuid.UUID
    code: str
    name: str
    city: str
    address: str
    contact_phone: str


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
    branch: BranchOut | None
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
