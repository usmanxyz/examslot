import uuid
from datetime import date as DateValue
from typing import Literal

from pydantic import Field

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


class CourseLabel(ResponseModel):
    id: uuid.UUID
    code: str
    title: str
    credit_hours: int


class PlannerSlotOut(ResponseModel):
    id: uuid.UUID
    date: DateValue
    day: str
    start_time: str
    end_time: str | None
    end_time_set: bool
    starts_at: UtcInstant
    ends_at: UtcInstant
    seats_left: int


class PlannerCourseOut(ResponseModel):
    course: CourseLabel
    selected_slot_id: uuid.UUID | None
    fixed: bool
    slots: list[PlannerSlotOut]


class PlannerOut(ResponseModel):
    state: Literal["assignment_incomplete", "branch_required", "planning", "saved", "reopened"]
    timezone: str
    default_exam_minutes: int
    saved_at: UtcInstant | None
    courses: list[PlannerCourseOut]


class DateSheetEntryIn(RequestModel):
    course_id: uuid.UUID
    slot_id: uuid.UUID


class DateSheetSave(RequestModel):
    entries: list[DateSheetEntryIn] = Field(min_length=1, max_length=6)


class StudentLabel(ResponseModel):
    full_name: str
    registration_no: str
    program: str
    semester: int
    session: str


class DateSheetBranch(ResponseModel):
    code: str
    name: str
    city: str
    address: str


class DateSheetEntryOut(ResponseModel):
    course_code: str
    course_title: str
    credit_hours: int
    date: DateValue
    day: str
    start_time: str
    end_time: str | None
    starts_at: UtcInstant
    ends_at: UtcInstant
    end_time_set: bool


class DateSheetOut(ResponseModel):
    saved_at: UtcInstant
    generated_at: UtcInstant
    student: StudentLabel
    branch: DateSheetBranch
    entries: list[DateSheetEntryOut]
