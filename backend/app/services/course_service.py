import uuid
from datetime import UTC, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound
from app.models.course import Course
from app.models.course_assignment import CourseAssignment
from app.models.exam_slot import ExamSlot
from app.schemas.course import CourseCreate, CourseListQuery, CourseUpdate
from app.utils.pagination import page_out, paginate, sorted_by
from app.utils.search import like_pattern

SORTS = {
    "code": Course.code,
    "title": Course.title,
    "department": Course.department,
    "created_at": Course.created_at,
}

FIELDS = (
    "id",
    "code",
    "title",
    "credit_hours",
    "department",
    "status",
    "created_at",
    "updated_at",
)


def list_courses(session: Session, query: CourseListQuery) -> dict:
    statement = _base_statement()
    if query.q:
        pattern = like_pattern(query.q)
        statement = statement.where(
            or_(
                Course.code.ilike(pattern, escape="\\"),
                Course.title.ilike(pattern, escape="\\"),
                Course.department.ilike(pattern, escape="\\"),
            )
        )
    if query.status:
        statement = statement.where(Course.status == query.status)
    if query.department:
        statement = statement.where(Course.department == query.department)
    statement = sorted_by(statement, SORTS[query.sort], query.order, Course.id)
    result, total = paginate(session, statement, query.page, query.page_size)
    items = [_out(course, assigned, slots) for course, assigned, slots in result.all()]
    return page_out(items, query.page, query.page_size, total)


def create_course(session: Session, data: CourseCreate) -> dict:
    course = Course(**data.model_dump())
    session.add(course)
    session.commit()
    return read_course(session, course.id)


def read_course(session: Session, course_id: uuid.UUID) -> dict:
    course = _load(session, course_id)
    return _out(course, *_usage(session, course_id))


def update_course(session: Session, course_id: uuid.UUID, data: CourseUpdate) -> dict:
    course = _load(session, course_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    course.updated_at = datetime.now(UTC)
    session.commit()
    return read_course(session, course_id)


def delete_course(session: Session, course_id: uuid.UUID) -> None:
    course = _load(session, course_id)
    assigned_count, slot_count = _usage(session, course_id)
    if assigned_count or slot_count:
        raise Conflict(
            "COURSE_IN_USE",
            details={"assigned_count": assigned_count, "slot_count": slot_count},
        )
    session.delete(course)
    session.commit()


def _base_statement() -> Select:
    assigned_count = (
        select(func.count())
        .select_from(CourseAssignment)
        .where(CourseAssignment.course_id == Course.id)
        .scalar_subquery()
    )
    slot_count = (
        select(func.count())
        .select_from(ExamSlot)
        .where(ExamSlot.course_id == Course.id)
        .scalar_subquery()
    )
    return select(Course, assigned_count, slot_count)


def _load(session: Session, course_id: uuid.UUID) -> Course:
    course = session.get(Course, course_id)
    if course is None:
        raise NotFound("NOT_FOUND")
    return course


def _usage(session: Session, course_id: uuid.UUID) -> tuple[int, int]:
    assigned_count = session.scalar(
        select(func.count())
        .select_from(CourseAssignment)
        .where(CourseAssignment.course_id == course_id)
    )
    slot_count = session.scalar(
        select(func.count()).select_from(ExamSlot).where(ExamSlot.course_id == course_id)
    )
    return assigned_count, slot_count


def _out(course: Course, assigned_count: int, slot_count: int) -> dict:
    return {
        **{field: getattr(course, field) for field in FIELDS},
        "assigned_count": assigned_count,
        "slot_count": slot_count,
    }
