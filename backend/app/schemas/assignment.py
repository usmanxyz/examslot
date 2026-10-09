import uuid
from typing import Literal

from pydantic import Field

from app.schemas.common import ListQuery, RequestModel, ResponseModel

AssignmentStatus = Literal["incomplete", "complete", "locked"]


class AssignedCourseOut(ResponseModel):
    id: uuid.UUID
    code: str
    title: str
    credit_hours: int
    status: str
    has_entry: bool


class CourseLabel(ResponseModel):
    id: uuid.UUID
    code: str


class StudentLabel(ResponseModel):
    id: uuid.UUID
    full_name: str
    registration_no: str
    program: str


class AssignmentListItem(ResponseModel):
    student: StudentLabel
    course_count: int
    courses: list[CourseLabel]
    status: AssignmentStatus


class StudentAssignmentsOut(ResponseModel):
    status: AssignmentStatus
    editable: bool
    courses: list[AssignedCourseOut]


class AssignmentsUpdate(RequestModel):
    course_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


class AssignmentListQuery(ListQuery):
    status: AssignmentStatus | None = None
    sort: Literal["full_name", "registration_no", "course_count"] = "full_name"
    order: Literal["asc", "desc"] = "asc"
