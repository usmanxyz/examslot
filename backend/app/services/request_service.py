import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import Conflict, NotFound
from app.models.admin import Admin
from app.models.change_request import ChangeRequest
from app.models.student import Student
from app.schemas.change_request import (
    AdminRequestListQuery,
    DecisionIn,
    RequestCreate,
    StudentRequestListQuery,
)
from app.services.student_service import lock_student
from app.utils.pagination import page_out, paginate, sorted_by
from app.utils.search import like_pattern

FIELDS = (
    "id",
    "type",
    "reason",
    "status",
    "admin_remark",
    "created_at",
    "decided_at",
    "used_at",
)


def list_student_requests(
    session: Session, student_id: uuid.UUID, query: StudentRequestListQuery
) -> dict:
    statement = (
        select(ChangeRequest)
        .where(ChangeRequest.student_id == student_id)
        .order_by(ChangeRequest.created_at.desc(), ChangeRequest.id)
    )
    result, total = paginate(session, statement, query.page, query.page_size)
    items = [_out(request) for request in result.scalars().all()]
    return page_out(items, query.page, query.page_size, total)


def create_request(session: Session, student_id: uuid.UUID, data: RequestCreate) -> dict:
    student = lock_student(session, student_id)
    if data.type == "branch_change" and student.branch_id is None:
        raise Conflict("REQUEST_NOT_ALLOWED", message="Choose your branch first.")
    if data.type == "date_sheet_change" and student.date_sheet_saved_at is None:
        raise Conflict("REQUEST_NOT_ALLOWED", message="Save your date sheet first.")

    existing = session.scalars(
        select(ChangeRequest).where(
            ChangeRequest.student_id == student_id, ChangeRequest.type == data.type
        )
    ).all()
    if any(request.status == "pending" for request in existing):
        raise Conflict("REQUEST_PENDING_EXISTS")
    if any(
        request.status == "approved" and request.used_at is None for request in existing
    ):
        raise Conflict("REOPENING_OPEN")

    request = ChangeRequest(student_id=student_id, type=data.type, reason=data.reason)
    session.add(request)
    session.commit()
    return _out(request)


def list_requests(session: Session, query: AdminRequestListQuery) -> dict:
    statement = select(ChangeRequest, Student).join(
        Student, Student.id == ChangeRequest.student_id
    )
    if query.q:
        pattern = like_pattern(query.q)
        statement = statement.where(
            or_(
                Student.full_name.ilike(pattern, escape="\\"),
                Student.registration_no.ilike(pattern, escape="\\"),
            )
        )
    if query.status:
        statement = statement.where(ChangeRequest.status == query.status)
    if query.type:
        statement = statement.where(ChangeRequest.type == query.type)
    statement = sorted_by(
        statement, ChangeRequest.created_at, query.order, ChangeRequest.id
    )
    result, total = paginate(session, statement, query.page, query.page_size)
    items = [_out(request, student) for request, student in result.all()]
    return page_out(items, query.page, query.page_size, total)


def read_request(session: Session, request_id: uuid.UUID) -> dict:
    request, student = _load(session, request_id)
    return _out(request, student)


def decide_request(
    session: Session,
    request_id: uuid.UUID,
    admin: Admin,
    status: str,
    data: DecisionIn,
) -> dict:
    request = session.scalar(
        select(ChangeRequest)
        .where(ChangeRequest.id == request_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if request is None:
        raise NotFound("NOT_FOUND")
    if request.status != "pending":
        raise Conflict("REQUEST_ALREADY_DECIDED")
    request.status = status
    request.admin_remark = data.remark
    request.decided_at = datetime.now(UTC)
    request.decided_by = admin.id
    session.commit()
    return read_request(session, request_id)


def list_requests_for_student(
    session: Session, student_id: uuid.UUID, query: StudentRequestListQuery
) -> dict:
    if session.get(Student, student_id) is None:
        raise NotFound("NOT_FOUND")
    return list_student_requests(session, student_id, query)


def _load(session: Session, request_id: uuid.UUID) -> tuple[ChangeRequest, Student]:
    row = session.execute(
        select(ChangeRequest, Student)
        .join(Student, Student.id == ChangeRequest.student_id)
        .where(ChangeRequest.id == request_id)
    ).first()
    if row is None:
        raise NotFound("NOT_FOUND")
    return row


def _out(request: ChangeRequest, student: Student | None = None) -> dict:
    item = {field: getattr(request, field) for field in FIELDS}
    if student is not None:
        item["student"] = student
    return item
