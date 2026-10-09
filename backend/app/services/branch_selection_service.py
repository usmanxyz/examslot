import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import Conflict, NotFound
from app.models.branch import Branch
from app.models.change_request import ChangeRequest
from app.models.course import Course
from app.models.date_sheet_entry import DateSheetEntry
from app.models.exam_slot import ExamSlot
from app.models.student import Student
from app.services.student_service import lock_student
from app.utils.timeutil import clock_time, format_date


def list_branches(session: Session, settings: Settings, student: Student) -> dict:
    approval = _unused_approval(session, student.id)
    can_select = student.branch_id is None or approval is not None
    chosen = _chosen_slots(session, student.id)
    branches = session.scalars(
        select(Branch).where(Branch.status == "active").order_by(Branch.code)
    ).all()
    items = []
    for branch in branches:
        reason = (
            None
            if branch.id == student.branch_id
            else _first_full_slot(session, settings, chosen, branch.id, student.id)
        )
        items.append(
            {
                "id": branch.id,
                "code": branch.code,
                "name": branch.name,
                "city": branch.city,
                "address": branch.address,
                "contact_phone": branch.contact_phone,
                "eligible": reason is None,
                "reason": reason,
            }
        )
    return {
        "can_select": can_select,
        "current_branch_id": student.branch_id,
        "items": items,
    }


def select_branch(
    session: Session, settings: Settings, student_id: uuid.UUID, branch_id: uuid.UUID
) -> dict:
    student = lock_student(session, student_id)
    approval = None
    if student.branch_id is not None:
        approval = _lock_unused_approval(session, student_id)
        if approval is None:
            raise Conflict("BRANCH_ALREADY_SELECTED")

    branch = session.get(Branch, branch_id)
    if branch is None:
        raise NotFound("NOT_FOUND")
    if branch.status != "active":
        raise Conflict("BRANCH_UNAVAILABLE")

    if branch_id != student.branch_id:
        chosen = _chosen_slots(session, student_id)
        if chosen:
            _lock_slots(session, [slot.id for slot, _ in chosen])
            if _first_full_slot(session, settings, chosen, branch_id, student_id):
                raise Conflict("BRANCH_UNAVAILABLE")

    now = datetime.now(UTC)
    student.branch_id = branch_id
    student.branch_selected_at = now
    student.updated_at = now
    used_approval = approval is not None
    if approval is not None:
        approval.used_at = now
    session.commit()
    return {
        "branch": branch,
        "branch_selected_at": now,
        "used_approval": used_approval,
    }


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
        ChangeRequest.type == "branch_change",
        ChangeRequest.status == "approved",
        ChangeRequest.used_at.is_(None),
    )


def _chosen_slots(session: Session, student_id: uuid.UUID) -> list[tuple[ExamSlot, str]]:
    return list(
        session.execute(
            select(ExamSlot, Course.code)
            .join(DateSheetEntry, DateSheetEntry.slot_id == ExamSlot.id)
            .join(Course, Course.id == ExamSlot.course_id)
            .where(DateSheetEntry.student_id == student_id)
            .order_by(ExamSlot.starts_at)
        ).all()
    )


def _lock_slots(session: Session, slot_ids: list[uuid.UUID]) -> None:
    session.execute(
        select(ExamSlot.id)
        .where(ExamSlot.id.in_(slot_ids))
        .order_by(ExamSlot.id)
        .with_for_update()
    ).all()


def _first_full_slot(
    session: Session,
    settings: Settings,
    slots: list[tuple[ExamSlot, str]],
    branch_id: uuid.UUID,
    student_id: uuid.UUID,
) -> str | None:
    if not slots:
        return None
    taken = _taken_counts(session, [slot.id for slot, _ in slots], branch_id, student_id)
    for slot, course_code in slots:
        if taken.get(slot.id, 0) >= slot.seats_per_branch:
            return (
                f"No seats left for {course_code} on"
                f" {format_date(slot.starts_at, settings.APP_TIMEZONE)}"
                f" at {clock_time(slot.starts_at, settings.APP_TIMEZONE)}."
            )
    return None


def _taken_counts(
    session: Session,
    slot_ids: list[uuid.UUID],
    branch_id: uuid.UUID,
    student_id: uuid.UUID,
) -> dict[uuid.UUID, int]:
    rows = session.execute(
        select(DateSheetEntry.slot_id, func.count())
        .where(
            DateSheetEntry.slot_id.in_(slot_ids),
            DateSheetEntry.branch_id == branch_id,
            DateSheetEntry.student_id != student_id,
        )
        .group_by(DateSheetEntry.slot_id)
    ).all()
    return dict(rows)
