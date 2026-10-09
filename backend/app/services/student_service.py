import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import Select, case, delete, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.email import EmailGate
from app.core.errors import Conflict, NotFound, Unprocessable
from app.core.passwords import PasswordService
from app.models.branch import Branch
from app.models.change_request import ChangeRequest
from app.models.course_assignment import CourseAssignment
from app.models.password_token import PasswordToken
from app.models.student import Student
from app.models.student_photo import StudentPhoto
from app.schemas.student import (
    EARLIEST_BIRTH_DATE,
    MINIMUM_AGE_YEARS,
    StudentCreate,
    StudentListQuery,
    StudentUpdate,
)
from app.services import password_link_service
from app.utils.pagination import page_out, paginate, sorted_by
from app.utils.search import like_pattern

MINIMUM_ASSIGNMENTS = 4

SCORE_LIMITS = {"percentage": Decimal(100), "cgpa": Decimal(4)}

SORTS = {
    "created_at": Student.created_at,
    "full_name": Student.full_name,
    "registration_no": Student.registration_no,
}

PROFILE_COLUMNS = (
    "id",
    "full_name",
    "email",
    "phone",
    "cnic",
    "date_of_birth",
    "gender",
    "address",
    "guardian_name",
    "guardian_cnic",
    "guardian_occupation",
    "guardian_phone",
    "emergency_phone",
    "registration_no",
    "program",
    "semester",
    "session",
    "previous_qualification",
    "previous_institute",
    "previous_score_type",
    "previous_score",
    "branch_selected_at",
    "date_sheet_saved_at",
)

DETAIL_COLUMNS = (*PROFILE_COLUMNS, "status", "last_login_at", "created_at", "updated_at")

assigned_count_sql = (
    select(func.count())
    .select_from(CourseAssignment)
    .where(CourseAssignment.student_id == Student.id)
    .scalar_subquery()
)

account_status_sql = case(
    (Student.status == "inactive", "inactive"),
    (Student.password_hash.is_(None), "invited"),
    else_="active",
)

progress_sql = case(
    (assigned_count_sql < MINIMUM_ASSIGNMENTS, "assignment_incomplete"),
    (Student.branch_id.is_(None), "branch_pending"),
    (Student.date_sheet_saved_at.is_(None), "planning"),
    else_="saved",
)


@dataclass(frozen=True)
class StudentState:
    account_status: str
    progress: str
    assigned_course_count: int
    can_change_branch: bool
    can_change_date_sheet: bool
    pending_request_types: list[str]


def account_status(student: Student) -> str:
    if student.status == "inactive":
        return "inactive"
    if student.password_hash is None:
        return "invited"
    return "active"


def progress(student: Student, assigned_course_count: int) -> str:
    if assigned_course_count < MINIMUM_ASSIGNMENTS:
        return "assignment_incomplete"
    if student.branch_id is None:
        return "branch_pending"
    if student.date_sheet_saved_at is None:
        return "planning"
    return "saved"


def load_state(session: Session, student: Student) -> StudentState:
    assigned = count_assignments(session, student.id)
    unused = unused_approval_types(session, student.id)
    return StudentState(
        account_status=account_status(student),
        progress=progress(student, assigned),
        assigned_course_count=assigned,
        can_change_branch="branch_change" in unused,
        can_change_date_sheet="date_sheet_change" in unused,
        pending_request_types=pending_request_types(session, student.id),
    )


def count_assignments(session: Session, student_id: uuid.UUID) -> int:
    return session.scalar(
        select(func.count())
        .select_from(CourseAssignment)
        .where(CourseAssignment.student_id == student_id)
    )


def unused_approval_types(session: Session, student_id: uuid.UUID) -> set[str]:
    return set(
        session.scalars(
            select(ChangeRequest.type).where(
                ChangeRequest.student_id == student_id,
                ChangeRequest.status == "approved",
                ChangeRequest.used_at.is_(None),
            )
        )
    )


def pending_request_types(session: Session, student_id: uuid.UUID) -> list[str]:
    return sorted(
        session.scalars(
            select(ChangeRequest.type).where(
                ChangeRequest.student_id == student_id,
                ChangeRequest.status == "pending",
            )
        )
    )


def read_profile(session: Session, student: Session) -> dict:
    state = load_state(session, student)
    return {
        **{column: getattr(student, column) for column in PROFILE_COLUMNS},
        "has_photo": _has_photo(session, student.id),
        "branch": _branch(session, student),
        "progress": state.progress,
        "assigned_course_count": state.assigned_course_count,
        "can_change_branch": state.can_change_branch,
        "can_change_date_sheet": state.can_change_date_sheet,
        "pending_request_types": state.pending_request_types,
    }


def list_students(session: Session, query: StudentListQuery) -> dict:
    statement = _list_statement()
    if query.q:
        pattern = like_pattern(query.q)
        statement = statement.where(
            or_(
                Student.full_name.ilike(pattern, escape="\\"),
                Student.email.ilike(pattern, escape="\\"),
                Student.registration_no.ilike(pattern, escape="\\"),
            )
        )
    if query.account_status:
        statement = statement.where(account_status_sql == query.account_status)
    if query.progress:
        statement = statement.where(progress_sql == query.progress)
    if query.branch_id:
        statement = statement.where(Student.branch_id == query.branch_id)
    if query.program:
        statement = statement.where(Student.program == query.program)
    statement = sorted_by(statement, SORTS[query.sort], query.order, Student.id)
    result, total = paginate(session, statement, query.page, query.page_size)
    items = [
        {
            "id": student.id,
            "full_name": student.full_name,
            "registration_no": student.registration_no,
            "program": student.program,
            "semester": student.semester,
            "account_status": status,
            "progress": student_progress,
            "branch": branch,
            "assigned_course_count": assigned,
            "created_at": student.created_at,
        }
        for student, branch, assigned, status, student_progress in result.all()
    ]
    return page_out(items, query.page, query.page_size, total)


def create_student(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    gate: EmailGate,
    data: StudentCreate,
) -> dict:
    _check_score(data.previous_score_type, data.previous_score)
    _check_birth_date(data.date_of_birth)
    student = Student(**data.model_dump())
    session.add(student)
    session.flush()
    token_id, secret, expires_at = password_link_service.issue(
        session, passwords, settings, student, "setup"
    )
    session.commit()
    password_link_service.deliver(
        session, settings, gate, student, "setup", token_id, secret, expires_at
    )
    return read_student(session, student.id)


def read_student(session: Session, student_id: uuid.UUID) -> dict:
    student = _load(session, student_id)
    state = load_state(session, student)
    return {
        **{column: getattr(student, column) for column in DETAIL_COLUMNS},
        "has_photo": _has_photo(session, student_id),
        "account_status": state.account_status,
        "progress": state.progress,
        "branch": _branch(session, student),
        "assigned_course_count": state.assigned_course_count,
        "can_change_branch": state.can_change_branch,
        "can_change_date_sheet": state.can_change_date_sheet,
        "latest_link": _latest_link(session, student_id),
    }


def update_student(session: Session, student_id: uuid.UUID, data: StudentUpdate) -> dict:
    student = lock_student(session, student_id)
    changes = data.model_dump(exclude_unset=True)
    _check_score(
        changes.get("previous_score_type", student.previous_score_type),
        changes.get("previous_score", student.previous_score),
    )
    if "date_of_birth" in changes:
        _check_birth_date(changes["date_of_birth"])
    email_changed = "email" in changes and changes["email"] != student.email
    for field, value in changes.items():
        setattr(student, field, value)
    if email_changed:
        student.token_version += 1
        password_link_service.revoke_live(session, student_id)
    student.updated_at = datetime.now(UTC)
    session.commit()
    return read_student(session, student_id)


def set_student_status(session: Session, student_id: uuid.UUID, status: str) -> dict:
    student = lock_student(session, student_id)
    student.status = status
    if status == "inactive":
        student.token_version += 1
    student.updated_at = datetime.now(UTC)
    session.commit()
    return read_student(session, student_id)


def delete_student(session: Session, student_id: uuid.UUID, confirm: str) -> None:
    student = _load(session, student_id)
    if confirm.strip().upper() != student.registration_no:
        raise Unprocessable("CONFIRMATION_MISMATCH")
    session.execute(delete(Student).where(Student.id == student_id))
    session.commit()


def resend_setup_email(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    gate: EmailGate,
    student_id: uuid.UUID,
) -> dict:
    student = lock_student(session, student_id)
    if student.password_hash is not None:
        raise Conflict("PASSWORD_ALREADY_SET")
    if student.status != "active":
        raise Conflict("STUDENT_INACTIVE")
    token_id, secret, expires_at = password_link_service.issue(
        session, passwords, settings, student, "setup"
    )
    session.commit()
    password_link_service.deliver(
        session, settings, gate, student, "setup", token_id, secret, expires_at
    )
    return {"latest_link": _latest_link(session, student_id)}


def lock_student(session: Session, student_id: uuid.UUID) -> Student:
    student = session.scalar(
        select(Student)
        .where(Student.id == student_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if student is None:
        raise NotFound("NOT_FOUND")
    return student


def _list_statement() -> Select:
    return select(Student, Branch, assigned_count_sql, account_status_sql, progress_sql).outerjoin(
        Branch, Branch.id == Student.branch_id
    )


def _load(session: Session, student_id: uuid.UUID) -> Student:
    student = session.get(Student, student_id)
    if student is None:
        raise NotFound("NOT_FOUND")
    return student


def _branch(session: Session, student: Student) -> Branch | None:
    return session.get(Branch, student.branch_id) if student.branch_id else None


def _has_photo(session: Session, student_id: uuid.UUID) -> bool:
    return session.get(StudentPhoto, student_id) is not None


def _latest_link(session: Session, student_id: uuid.UUID) -> dict | None:
    token = session.scalar(
        select(PasswordToken)
        .where(PasswordToken.student_id == student_id)
        .order_by(PasswordToken.created_at.desc())
        .limit(1)
    )
    if token is None:
        return None
    return {
        "purpose": token.purpose,
        "delivery_status": token.delivery_status,
        "created_at": token.created_at,
        "expires_at": token.expires_at,
        "used_at": token.used_at,
    }


def _check_score(score_type: str, score: Decimal) -> None:
    if score < 0 or score > SCORE_LIMITS[score_type]:
        raise Unprocessable(
            "VALIDATION_ERROR",
            details={
                "fields": [
                    {
                        "field": "previous_score",
                        "message": f"Enter a value from 0 to {SCORE_LIMITS[score_type]}.",
                    }
                ]
            },
        )


def _check_birth_date(value: date) -> None:
    today = date.today()
    oldest = date(today.year - MINIMUM_AGE_YEARS, today.month, today.day)
    if value < EARLIEST_BIRTH_DATE or value > oldest:
        raise Unprocessable(
            "VALIDATION_ERROR",
            details={
                "fields": [
                    {
                        "field": "date_of_birth",
                        "message": (
                            f"Enter a date from {EARLIEST_BIRTH_DATE.isoformat()}"
                            f" and at least {MINIMUM_AGE_YEARS} years ago."
                        ),
                    }
                ]
            },
        )
