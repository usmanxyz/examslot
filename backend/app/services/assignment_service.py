import uuid

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound, Unprocessable
from app.models.change_request import ChangeRequest
from app.models.course import Course
from app.models.course_assignment import CourseAssignment
from app.models.date_sheet_entry import DateSheetEntry
from app.models.student import Student
from app.schemas.assignment import AssignmentListQuery, AssignmentsUpdate
from app.services.student_service import assigned_count_sql, lock_student
from app.utils.pagination import page_out, paginate, sorted_by
from app.utils.search import like_pattern

MINIMUM_COURSES = 4
MAXIMUM_COURSES = 6

open_date_sheet_change_sql = (
    select(func.count())
    .select_from(ChangeRequest)
    .where(
        ChangeRequest.student_id == Student.id,
        ChangeRequest.type == "date_sheet_change",
        ChangeRequest.status == "approved",
        ChangeRequest.used_at.is_(None),
    )
    .scalar_subquery()
)

assignment_status_sql = case(
    (assigned_count_sql == 0, "incomplete"),
    (
        and_(Student.date_sheet_saved_at.is_not(None), open_date_sheet_change_sql == 0),
        "locked",
    ),
    else_="complete",
)

SORTS = {
    "full_name": Student.full_name,
    "registration_no": Student.registration_no,
    "course_count": assigned_count_sql,
}


def list_assignments(session: Session, query: AssignmentListQuery) -> dict:
    statement = select(Student, assigned_count_sql, assignment_status_sql)
    if query.q:
        pattern = like_pattern(query.q)
        statement = statement.where(
            or_(
                Student.full_name.ilike(pattern, escape="\\"),
                Student.registration_no.ilike(pattern, escape="\\"),
                exists(
                    select(1)
                    .select_from(CourseAssignment)
                    .join(Course, Course.id == CourseAssignment.course_id)
                    .where(
                        CourseAssignment.student_id == Student.id,
                        Course.code.ilike(pattern, escape="\\"),
                    )
                ),
            )
        )
    if query.status:
        statement = statement.where(assignment_status_sql == query.status)
    statement = sorted_by(statement, SORTS[query.sort], query.order, Student.id)
    result, total = paginate(session, statement, query.page, query.page_size)
    rows = result.all()
    labels = _course_labels(session, [student.id for student, _, _ in rows])
    items = [
        {
            "student": student,
            "course_count": count,
            "courses": labels.get(student.id, []),
            "status": status,
        }
        for student, count, status in rows
    ]
    return page_out(items, query.page, query.page_size, total)


def read_assignments(session: Session, student_id: uuid.UUID) -> dict:
    student = _load(session, student_id)
    status = _status(session, student)
    return {
        "status": status,
        "editable": status != "locked",
        "courses": _assigned_courses(session, student_id),
    }


def replace_assignments(
    session: Session, student_id: uuid.UUID, data: AssignmentsUpdate
) -> dict:
    student = lock_student(session, student_id)
    if _status(session, student) == "locked":
        raise Conflict("ASSIGNMENT_LOCKED")

    requested = list(dict.fromkeys(data.course_ids))
    if len(requested) != len(data.course_ids) or not (
        MINIMUM_COURSES <= len(requested) <= MAXIMUM_COURSES
    ):
        raise Unprocessable("ASSIGNMENT_COUNT_INVALID")

    courses = session.scalars(select(Course).where(Course.id.in_(requested))).all()
    if len(courses) != len(requested):
        raise NotFound("NOT_FOUND")

    current = set(
        session.scalars(
            select(CourseAssignment.course_id).where(
                CourseAssignment.student_id == student_id
            )
        )
    )
    for course in courses:
        if course.status != "active" and course.id not in current:
            raise Conflict("COURSE_INACTIVE")

    for course_id in current - set(requested):
        session.execute(
            CourseAssignment.__table__.delete().where(
                CourseAssignment.student_id == student_id,
                CourseAssignment.course_id == course_id,
            )
        )
    for course_id in set(requested) - current:
        session.add(CourseAssignment(student_id=student_id, course_id=course_id))
    session.commit()
    return read_assignments(session, student_id)


def _load(session: Session, student_id: uuid.UUID) -> Student:
    student = session.get(Student, student_id)
    if student is None:
        raise NotFound("NOT_FOUND")
    return student


def _status(session: Session, student: Student) -> str:
    count = session.scalar(
        select(func.count())
        .select_from(CourseAssignment)
        .where(CourseAssignment.student_id == student.id)
    )
    if count == 0:
        return "incomplete"
    if student.date_sheet_saved_at is not None and not _has_open_change(session, student.id):
        return "locked"
    return "complete"


def _has_open_change(session: Session, student_id: uuid.UUID) -> bool:
    return session.scalar(
        select(
            exists().where(
                ChangeRequest.student_id == student_id,
                ChangeRequest.type == "date_sheet_change",
                ChangeRequest.status == "approved",
                ChangeRequest.used_at.is_(None),
            )
        )
    )


def _assigned_courses(session: Session, student_id: uuid.UUID) -> list[dict]:
    has_entry = (
        select(
            exists().where(
                DateSheetEntry.student_id == student_id,
                DateSheetEntry.course_id == Course.id,
            )
        )
        .scalar_subquery()
        .label("has_entry")
    )
    rows = session.execute(
        select(Course, has_entry)
        .join(CourseAssignment, CourseAssignment.course_id == Course.id)
        .where(CourseAssignment.student_id == student_id)
        .order_by(Course.code)
    ).all()
    return [
        {
            "id": course.id,
            "code": course.code,
            "title": course.title,
            "credit_hours": course.credit_hours,
            "status": course.status,
            "has_entry": entry,
        }
        for course, entry in rows
    ]


def _course_labels(
    session: Session, student_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[dict]]:
    if not student_ids:
        return {}
    rows = session.execute(
        select(CourseAssignment.student_id, Course.id, Course.code)
        .join(Course, Course.id == CourseAssignment.course_id)
        .where(CourseAssignment.student_id.in_(student_ids))
        .order_by(Course.code)
    ).all()
    labels: dict[uuid.UUID, list[dict]] = {}
    for student_id, course_id, code in rows:
        labels.setdefault(student_id, []).append({"id": course_id, "code": code})
    return labels
