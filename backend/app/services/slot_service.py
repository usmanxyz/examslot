import uuid
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import Conflict, NotFound, Unprocessable
from app.models.branch import Branch
from app.models.course import Course
from app.models.date_sheet_entry import DateSheetEntry
from app.models.exam_slot import ExamSlot
from app.schemas.slot import SlotCreate, SlotListQuery, SlotUpdate
from app.utils.pagination import page_out, paginate, sorted_by
from app.utils.search import like_pattern
from app.utils.timeutil import clock_time, day_name, to_local, to_local_date, to_utc

TIMING_FIELDS = frozenset({"date", "start_time", "end_time"})


def list_slots(session: Session, settings: Settings, query: SlotListQuery) -> dict:
    statement = select(ExamSlot, Course, _chosen_count_sql()).join(
        Course, Course.id == ExamSlot.course_id
    )
    if query.q:
        pattern = like_pattern(query.q)
        statement = statement.where(
            or_(
                Course.code.ilike(pattern, escape="\\"),
                Course.title.ilike(pattern, escape="\\"),
            )
        )
    if query.course_id:
        statement = statement.where(ExamSlot.course_id == query.course_id)
    if query.date_from:
        statement = statement.where(
            ExamSlot.starts_at >= to_utc(query.date_from, time(0, 0), settings.APP_TIMEZONE)
        )
    if query.date_to:
        statement = statement.where(
            ExamSlot.starts_at
            < to_utc(query.date_to + timedelta(days=1), time(0, 0), settings.APP_TIMEZONE)
        )
    now = datetime.now(UTC)
    if query.when == "upcoming":
        statement = statement.where(ExamSlot.starts_at > now)
    elif query.when == "past":
        statement = statement.where(ExamSlot.starts_at <= now)
    column = Course.code if query.sort == "course_code" else ExamSlot.starts_at
    statement = sorted_by(statement, column, query.order, ExamSlot.id)
    result, total = paginate(session, statement, query.page, query.page_size)
    items = [
        _out(slot, course, chosen, settings, now) for slot, course, chosen in result.all()
    ]
    return page_out(items, query.page, query.page_size, total)


def create_slot(session: Session, settings: Settings, data: SlotCreate) -> dict:
    course = session.get(Course, data.course_id)
    if course is None:
        raise NotFound("NOT_FOUND")
    if course.status != "active":
        raise Conflict("COURSE_INACTIVE")
    starts_at, ends_at = _window(
        settings, data.date, data.start_time, data.end_time, data.end_time is not None
    )
    slot = ExamSlot(
        course_id=course.id,
        starts_at=starts_at,
        ends_at=ends_at,
        end_time_set=data.end_time is not None,
        seats_per_branch=data.seats_per_branch,
    )
    session.add(slot)
    session.commit()
    return read_slot(session, settings, slot.id)


def read_slot(session: Session, settings: Settings, slot_id: uuid.UUID) -> dict:
    slot, course, chosen = _load(session, slot_id)
    detail = _out(slot, course, chosen, settings, datetime.now(UTC))
    detail["seats_by_branch"] = _seats_by_branch(session, slot)
    return detail


def update_slot(
    session: Session, settings: Settings, slot_id: uuid.UUID, data: SlotUpdate
) -> dict:
    slot = session.scalar(select(ExamSlot).where(ExamSlot.id == slot_id).with_for_update())
    if slot is None:
        raise NotFound("NOT_FOUND")
    changes = data.model_dump(exclude_unset=True)
    chosen = _chosen_count(session, slot_id)

    if chosen and TIMING_FIELDS & set(changes):
        raise Conflict("SLOT_IN_USE", details={"chosen_count": chosen})

    if "seats_per_branch" in changes:
        _check_seats(session, slot_id, changes["seats_per_branch"])
        slot.seats_per_branch = changes["seats_per_branch"]

    if TIMING_FIELDS & set(changes):
        local_start = to_local(slot.starts_at, settings.APP_TIMEZONE)
        end_time_set = (
            changes["end_time"] is not None if "end_time" in changes else slot.end_time_set
        )
        end_time = (
            changes["end_time"]
            if "end_time" in changes
            else (to_local(slot.ends_at, settings.APP_TIMEZONE).time() if slot.end_time_set else None)
        )
        slot.starts_at, slot.ends_at = _window(
            settings,
            changes.get("date", local_start.date()),
            changes.get("start_time", local_start.time()),
            end_time,
            end_time_set,
        )
        slot.end_time_set = end_time_set

    slot.updated_at = datetime.now(UTC)
    session.commit()
    return read_slot(session, settings, slot_id)


def delete_slot(session: Session, slot_id: uuid.UUID) -> None:
    slot = session.get(ExamSlot, slot_id)
    if slot is None:
        raise NotFound("NOT_FOUND")
    chosen = _chosen_count(session, slot_id)
    if chosen:
        raise Conflict("SLOT_IN_USE", details={"chosen_count": chosen})
    session.delete(slot)
    session.commit()


def _window(
    settings: Settings,
    day: date,
    start: time,
    end: time | None,
    end_time_set: bool,
) -> tuple[datetime, datetime]:
    starts_at = to_utc(day, start, settings.APP_TIMEZONE)
    if starts_at <= datetime.now(UTC):
        raise Unprocessable("SLOT_IN_PAST")
    if not end_time_set or end is None:
        return starts_at, starts_at + timedelta(minutes=settings.DEFAULT_EXAM_MINUTES)
    ends_at = to_utc(day, end, settings.APP_TIMEZONE)
    if ends_at <= starts_at:
        raise Unprocessable("END_BEFORE_START")
    return starts_at, ends_at


def _chosen_count_sql():
    return (
        select(func.count())
        .select_from(DateSheetEntry)
        .where(DateSheetEntry.slot_id == ExamSlot.id)
        .scalar_subquery()
    )


def _chosen_count(session: Session, slot_id: uuid.UUID) -> int:
    return session.scalar(
        select(func.count()).select_from(DateSheetEntry).where(DateSheetEntry.slot_id == slot_id)
    )


def _load(session: Session, slot_id: uuid.UUID) -> tuple[ExamSlot, Course, int]:
    row = session.execute(
        select(ExamSlot, Course, _chosen_count_sql())
        .join(Course, Course.id == ExamSlot.course_id)
        .where(ExamSlot.id == slot_id)
    ).first()
    if row is None:
        raise NotFound("NOT_FOUND")
    return row


def _taken_by_branch(session: Session, slot_id: uuid.UUID) -> dict[uuid.UUID, int]:
    rows = session.execute(
        select(DateSheetEntry.branch_id, func.count())
        .where(DateSheetEntry.slot_id == slot_id)
        .group_by(DateSheetEntry.branch_id)
    ).all()
    return dict(rows)


def _seats_by_branch(session: Session, slot: ExamSlot) -> list[dict]:
    taken = _taken_by_branch(session, slot.id)
    branches = session.scalars(
        select(Branch).where(Branch.status == "active").order_by(Branch.code)
    ).all()
    return [
        {
            "branch": branch,
            "taken": taken.get(branch.id, 0),
            "left": slot.seats_per_branch - taken.get(branch.id, 0),
        }
        for branch in branches
    ]


def _check_seats(session: Session, slot_id: uuid.UUID, seats: int) -> None:
    taken = _taken_by_branch(session, slot_id)
    over = [branch_id for branch_id, count in taken.items() if count > seats]
    if not over:
        return
    codes = dict(
        session.execute(select(Branch.id, Branch.code).where(Branch.id.in_(over))).all()
    )
    raise Conflict(
        "SLOT_SEATS_BELOW_TAKEN",
        details={
            "branches": [
                {"code": codes[branch_id], "taken": taken[branch_id]} for branch_id in over
            ]
        },
    )


def _out(
    slot: ExamSlot, course: Course, chosen_count: int, settings: Settings, now: datetime
) -> dict:
    timezone = settings.APP_TIMEZONE
    return {
        "id": slot.id,
        "course": course,
        "date": to_local_date(slot.starts_at, timezone),
        "day": day_name(slot.starts_at, timezone),
        "start_time": clock_time(slot.starts_at, timezone),
        "end_time": clock_time(slot.ends_at, timezone) if slot.end_time_set else None,
        "end_time_set": slot.end_time_set,
        "starts_at": slot.starts_at,
        "ends_at": slot.ends_at,
        "seats_per_branch": slot.seats_per_branch,
        "chosen_count": chosen_count,
        "is_past": slot.starts_at <= now,
        "created_at": slot.created_at,
        "updated_at": slot.updated_at,
    }
