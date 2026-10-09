import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.change_request import ChangeRequest
from app.models.course_assignment import CourseAssignment
from app.models.student import Student
from app.models.student_photo import StudentPhoto

MINIMUM_ASSIGNMENTS = 4

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


def read_profile(session: Session, student: Student) -> dict:
    state = load_state(session, student)
    branch = session.get(Branch, student.branch_id) if student.branch_id else None
    return {
        **{column: getattr(student, column) for column in PROFILE_COLUMNS},
        "has_photo": session.get(StudentPhoto, student.id) is not None,
        "branch": branch,
        "progress": state.progress,
        "assigned_course_count": state.assigned_course_count,
        "can_change_branch": state.can_change_branch,
        "can_change_date_sheet": state.can_change_date_sheet,
        "pending_request_types": state.pending_request_types,
    }
