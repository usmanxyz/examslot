import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import Conflict, NotFound, Unprocessable
from app.models.branch import Branch
from app.models.change_request import ChangeRequest
from app.models.course import Course
from app.models.course_assignment import CourseAssignment
from app.models.date_sheet_entry import DateSheetEntry
from app.models.exam_slot import ExamSlot
from app.models.student import Student
from app.schemas.planner import DateSheetSave
from app.services.student_service import lock_student
from app.utils.overlap import overlaps
from app.utils.timeutil import clock_time, day_name, format_date, to_local_date

MINIMUM_COURSES = 4
MAXIMUM_COURSES = 6


def read_planner(session: Session, settings: Settings, student: Student) -> dict:
    assigned = _assigned_courses(session, student.id)
    reopened = _unused_approval(session, student.id) is not None
    base = {
        "timezone": settings.APP_TIMEZONE,
        "default_exam_minutes": settings.DEFAULT_EXAM_MINUTES,
        "saved_at": student.date_sheet_saved_at,
        "courses": [],
    }
    if len(assigned) < MINIMUM_COURSES:
        return {**base, "state": "assignment_incomplete"}
    if student.branch_id is None:
        return {**base, "state": "branch_required"}
    saved = student.date_sheet_saved_at is not None
    state = ("reopened" if reopened else "saved") if saved else "planning"

    chosen = _chosen_slot_ids(session, student.id)
    now = datetime.now(UTC)
    courses = []
    for course in assigned:
        selected_slot_id = chosen.get(course.id)
        fixed = False
        if state == "saved":
            slots = _slots_by_id(session, [selected_slot_id]) if selected_slot_id else []
        else:
            slots = _choosable_slots(session, student, course.id, selected_slot_id, now)
            if state == "reopened" and selected_slot_id is not None:
                saved = next((slot for slot in slots if slot.id == selected_slot_id), None)
                fixed = saved is not None and saved.starts_at <= now
                if fixed:
                    slots = [saved]
        courses.append(
            {
                "course": course,
                "selected_slot_id": selected_slot_id,
                "fixed": fixed,
                "slots": [
                    _planner_slot(session, settings, slot, student.branch_id, student.id)
                    for slot in slots
                ],
            }
        )
    return {**base, "state": state, "courses": courses}


def save_date_sheet(
    session: Session, settings: Settings, student_id: uuid.UUID, data: DateSheetSave
) -> dict:
    student = lock_student(session, student_id)
    if student.branch_id is None:
        raise Conflict("BRANCH_NOT_SELECTED")

    assigned = {course.id for course in _assigned_courses(session, student_id)}
    if not MINIMUM_COURSES <= len(assigned) <= MAXIMUM_COURSES:
        raise Conflict("ASSIGNMENT_INCOMPLETE")

    approval = None
    if student.date_sheet_saved_at is not None:
        approval = _lock_unused_approval(session, student_id)
        if approval is None:
            raise Conflict("DATE_SHEET_LOCKED")

    requested = {entry.course_id: entry.slot_id for entry in data.entries}
    if len(requested) != len(data.entries):
        raise Unprocessable(
            "VALIDATION_ERROR",
            details={"fields": [{"field": "entries", "message": "List each course once."}]},
        )
    if set(requested) != assigned:
        raise Unprocessable("DATE_SHEET_INCOMPLETE")

    slots = _lock_slots(session, sorted(requested.values(), key=str))
    if len(slots) != len(set(requested.values())):
        raise Conflict("SLOT_UNAVAILABLE")

    now = datetime.now(UTC)
    existing = _chosen_slot_ids(session, student_id)
    for course_id, slot_id in requested.items():
        slot = slots[slot_id]
        if slot.course_id != course_id:
            raise Conflict("SLOT_UNAVAILABLE")
        unchanged = existing.get(course_id) == slot_id
        if not unchanged and slot.starts_at <= now:
            raise Conflict("SLOT_UNAVAILABLE")
        previous = existing.get(course_id)
        if previous is not None and previous != slot_id:
            previous_slot = session.get(ExamSlot, previous)
            if previous_slot.starts_at <= now:
                raise Conflict("SLOT_UNAVAILABLE")

    _check_clashes(session, settings, requested, slots)
    _check_seats(session, requested, slots, existing, student)

    session.execute(
        DateSheetEntry.__table__.delete().where(DateSheetEntry.student_id == student_id)
    )
    session.flush()
    for course_id, slot_id in requested.items():
        slot = slots[slot_id]
        session.add(
            DateSheetEntry(
                student_id=student_id,
                course_id=course_id,
                slot_id=slot_id,
                branch_id=student.branch_id,
                period=Range(slot.starts_at, slot.ends_at, bounds="[)"),
            )
        )
    student.date_sheet_saved_at = now
    student.updated_at = now
    if approval is not None:
        approval.used_at = now
    session.commit()
    return read_date_sheet(session, settings, student_id)


def read_date_sheet(session: Session, settings: Settings, student_id: uuid.UUID) -> dict:
    student = session.get(Student, student_id)
    if student is None:
        raise NotFound("NOT_FOUND")
    if student.date_sheet_saved_at is None:
        raise NotFound("DATE_SHEET_NOT_SAVED")
    branch = session.get(Branch, student.branch_id)
    timezone = settings.APP_TIMEZONE
    rows = session.execute(
        select(Course, ExamSlot)
        .join(DateSheetEntry, DateSheetEntry.course_id == Course.id)
        .join(ExamSlot, ExamSlot.id == DateSheetEntry.slot_id)
        .where(DateSheetEntry.student_id == student_id)
        .order_by(ExamSlot.starts_at)
    ).all()
    return {
        "saved_at": student.date_sheet_saved_at,
        "generated_at": datetime.now(UTC),
        "student": student,
        "branch": branch,
        "entries": [
            {
                "course_code": course.code,
                "course_title": course.title,
                "credit_hours": course.credit_hours,
                "date": to_local_date(slot.starts_at, timezone),
                "day": day_name(slot.starts_at, timezone),
                "start_time": clock_time(slot.starts_at, timezone),
                "end_time": clock_time(slot.ends_at, timezone) if slot.end_time_set else None,
                "starts_at": slot.starts_at,
                "ends_at": slot.ends_at,
                "end_time_set": slot.end_time_set,
            }
            for course, slot in rows
        ],
    }


def _assigned_courses(session: Session, student_id: uuid.UUID) -> list[Course]:
    return list(
        session.scalars(
            select(Course)
            .join(CourseAssignment, CourseAssignment.course_id == Course.id)
            .where(CourseAssignment.student_id == student_id)
            .order_by(Course.code)
        )
    )


def _chosen_slot_ids(session: Session, student_id: uuid.UUID) -> dict[uuid.UUID, uuid.UUID]:
    return dict(
        session.execute(
            select(DateSheetEntry.course_id, DateSheetEntry.slot_id).where(
                DateSheetEntry.student_id == student_id
            )
        ).all()
    )


def _unused_approval(session: Session, student_id: uuid.UUID) -> ChangeRequest | None:
    return session.scalar(_approval_statement(student_id))


def _lock_unused_approval(session: Session, student_id: uuid.UUID) -> ChangeRequest | None:
    return session.scalar(
        _approval_statement(student_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )


def _approval_statement(student_id: uuid.UUID):
    return select(ChangeRequest).where(
        ChangeRequest.student_id == student_id,
        ChangeRequest.type == "date_sheet_change",
        ChangeRequest.status == "approved",
        ChangeRequest.used_at.is_(None),
    )


def _lock_slots(session: Session, slot_ids: list[uuid.UUID]) -> dict[uuid.UUID, ExamSlot]:
    slots = session.scalars(
        select(ExamSlot)
        .where(ExamSlot.id.in_(slot_ids))
        .order_by(ExamSlot.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).all()
    return {slot.id: slot for slot in slots}


def _slots_by_id(session: Session, slot_ids: list[uuid.UUID]) -> list[ExamSlot]:
    return list(
        session.scalars(
            select(ExamSlot).where(ExamSlot.id.in_(slot_ids)).order_by(ExamSlot.starts_at)
        )
    )


def _choosable_slots(
    session: Session,
    student: Student,
    course_id: uuid.UUID,
    selected_slot_id: uuid.UUID | None,
    now: datetime,
) -> list[ExamSlot]:
    taken = _taken_by_slot(session, course_id, student.branch_id, student.id)
    slots = session.scalars(
        select(ExamSlot).where(ExamSlot.course_id == course_id).order_by(ExamSlot.starts_at)
    ).all()
    return [
        slot
        for slot in slots
        if slot.id == selected_slot_id
        or (slot.starts_at > now and taken.get(slot.id, 0) < slot.seats_per_branch)
    ]


def _taken_by_slot(
    session: Session, course_id: uuid.UUID, branch_id: uuid.UUID, student_id: uuid.UUID
) -> dict[uuid.UUID, int]:
    rows = session.execute(
        select(DateSheetEntry.slot_id, func.count())
        .join(ExamSlot, ExamSlot.id == DateSheetEntry.slot_id)
        .where(
            ExamSlot.course_id == course_id,
            DateSheetEntry.branch_id == branch_id,
            DateSheetEntry.student_id != student_id,
        )
        .group_by(DateSheetEntry.slot_id)
    ).all()
    return dict(rows)


def _planner_slot(
    session: Session,
    settings: Settings,
    slot: ExamSlot,
    branch_id: uuid.UUID,
    student_id: uuid.UUID,
) -> dict:
    timezone = settings.APP_TIMEZONE
    taken = session.scalar(
        select(func.count())
        .select_from(DateSheetEntry)
        .where(
            DateSheetEntry.slot_id == slot.id,
            DateSheetEntry.branch_id == branch_id,
            DateSheetEntry.student_id != student_id,
        )
    )
    return {
        "id": slot.id,
        "date": to_local_date(slot.starts_at, timezone),
        "day": day_name(slot.starts_at, timezone),
        "start_time": clock_time(slot.starts_at, timezone),
        "end_time": clock_time(slot.ends_at, timezone) if slot.end_time_set else None,
        "end_time_set": slot.end_time_set,
        "starts_at": slot.starts_at,
        "ends_at": slot.ends_at,
        "seats_left": slot.seats_per_branch - taken,
    }


def _check_clashes(
    session: Session,
    settings: Settings,
    requested: dict[uuid.UUID, uuid.UUID],
    slots: dict[uuid.UUID, ExamSlot],
) -> None:
    codes = dict(
        session.execute(
            select(Course.id, Course.code).where(Course.id.in_(requested))
        ).all()
    )
    ordered = sorted(requested.items(), key=lambda pair: slots[pair[1]].starts_at)
    for (first_course, first_slot), (second_course, second_slot) in zip(
        ordered, ordered[1:], strict=False
    ):
        first = slots[first_slot]
        second = slots[second_slot]
        if overlaps(first.starts_at, first.ends_at, second.starts_at, second.ends_at):
            raise Conflict(
                "SLOT_CONFLICT",
                message=(
                    f"{codes[first_course]} and {codes[second_course]} overlap on"
                    f" {format_date(first.starts_at, settings.APP_TIMEZONE)}."
                    " Choose a different time for one of them."
                ),
                details={
                    "courses": [
                        {
                            "course_id": str(first_course),
                            "code": codes[first_course],
                            "starts_at": first.starts_at.isoformat(),
                        },
                        {
                            "course_id": str(second_course),
                            "code": codes[second_course],
                            "starts_at": second.starts_at.isoformat(),
                        },
                    ]
                },
            )


def _check_seats(
    session: Session,
    requested: dict[uuid.UUID, uuid.UUID],
    slots: dict[uuid.UUID, ExamSlot],
    existing: dict[uuid.UUID, uuid.UUID],
    student: Student,
) -> None:
    new_slot_ids = [
        slot_id for course_id, slot_id in requested.items() if existing.get(course_id) != slot_id
    ]
    if not new_slot_ids:
        return
    rows = session.execute(
        select(DateSheetEntry.slot_id, func.count())
        .where(
            DateSheetEntry.slot_id.in_(new_slot_ids),
            DateSheetEntry.branch_id == student.branch_id,
            DateSheetEntry.student_id != student.id,
        )
        .group_by(DateSheetEntry.slot_id)
    ).all()
    taken = dict(rows)
    codes = dict(
        session.execute(
            select(Course.id, Course.code).where(Course.id.in_(requested))
        ).all()
    )
    for course_id, slot_id in requested.items():
        if slot_id not in new_slot_ids:
            continue
        slot = slots[slot_id]
        if taken.get(slot_id, 0) >= slot.seats_per_branch:
            raise Conflict(
                "SLOT_FULL",
                message=(
                    f"The last seat for {codes[course_id]} was just taken."
                    " Choose another time."
                ),
            )
