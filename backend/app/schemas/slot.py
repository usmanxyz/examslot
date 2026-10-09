import uuid
from datetime import date as DateValue
from datetime import time as TimeValue
from typing import Annotated, Literal

from pydantic import Field

from app.schemas.common import ListQuery, RequestModel, ResponseModel, UtcInstant

Seats = Annotated[int, Field(ge=1, le=1000)]


class CourseLabel(ResponseModel):
    id: uuid.UUID
    code: str
    title: str


class BranchLabel(ResponseModel):
    id: uuid.UUID
    code: str
    name: str


class BranchSeatsOut(ResponseModel):
    branch: BranchLabel
    taken: int
    left: int


class SlotCreate(RequestModel):
    course_id: uuid.UUID
    date: DateValue
    start_time: TimeValue
    end_time: TimeValue | None = None
    seats_per_branch: Seats


class SlotUpdate(RequestModel):
    date: DateValue | None = None
    start_time: TimeValue | None = None
    end_time: TimeValue | None = None
    seats_per_branch: Seats | None = None


class SlotOut(ResponseModel):
    id: uuid.UUID
    course: CourseLabel
    date: DateValue
    day: str
    start_time: str
    end_time: str | None
    end_time_set: bool
    starts_at: UtcInstant
    ends_at: UtcInstant
    seats_per_branch: int
    chosen_count: int
    is_past: bool
    created_at: UtcInstant
    updated_at: UtcInstant


class SlotDetailOut(SlotOut):
    seats_by_branch: list[BranchSeatsOut]


class SlotListQuery(ListQuery):
    course_id: uuid.UUID | None = None
    date_from: DateValue | None = None
    date_to: DateValue | None = None
    when: Literal["upcoming", "past", "all"] = "upcoming"
    sort: Literal["starts_at", "course_code"] = "starts_at"
    order: Literal["asc", "desc"] = "asc"
