from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.core.passwords import PasswordService
from app.models.admin import Admin
from app.models.branch import Branch
from app.models.course import Course
from app.models.course_assignment import CourseAssignment
from app.models.date_sheet_entry import DateSheetEntry
from app.models.exam_slot import ExamSlot
from app.models.student import Student

STUDENT_PASSWORD = "a-long-student-password"
ADMIN_PASSWORD = "a-long-admin-password"


def student_values(index: int = 1, **overrides: object) -> dict:
    values: dict = {
        "registration_no": f"2024-CS-{index:04d}",
        "email": f"student{index}@example.com",
        "full_name": "Ayesha Siddiqui",
        "phone": f"+923{200 + index:09d}",
        "cnic": f"{index:013d}",
        "date_of_birth": date(2004, 1, 1),
        "gender": "female",
        "address": "House 1, Model Town",
        "guardian_name": "Tariq Siddiqui",
        "guardian_cnic": f"{500 + index:013d}",
        "guardian_occupation": "Teacher",
        "guardian_phone": f"+923{300 + index:09d}",
        "emergency_phone": f"+923{400 + index:09d}",
        "program": "BS Computer Science",
        "semester": 5,
        "session": "2024-2028",
        "previous_qualification": "FSc Pre-Engineering",
        "previous_institute": "Government College Lahore",
        "previous_score_type": "percentage",
        "previous_score": Decimal("82.50"),
    }
    values.update(overrides)
    return values


def create_student(
    session: Session,
    passwords: PasswordService,
    index: int = 1,
    password: str | None = STUDENT_PASSWORD,
    **overrides: object,
) -> Student:
    now = datetime.now(UTC)
    student = Student(
        **student_values(index, **overrides),
        password_hash=passwords.hash(password) if password else None,
        password_set_at=now if password else None,
    )
    session.add(student)
    session.commit()
    return student


def create_admin(
    session: Session,
    passwords: PasswordService,
    email: str = "office@example.com",
    password: str = ADMIN_PASSWORD,
    **overrides: object,
) -> Admin:
    admin = Admin(
        email=email,
        full_name="Exam Office",
        password_hash=passwords.hash(password),
        **overrides,
    )
    session.add(admin)
    session.commit()
    return admin


def admin_headers(client, session: Session, passwords: PasswordService) -> dict[str, str]:
    create_admin(session, passwords)
    token = client.post(
        "/api/v1/auth/admin/login",
        json={"email": "office@example.com", "password": ADMIN_PASSWORD},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def student_headers(
    client, session: Session, passwords: PasswordService, student: Student
) -> dict[str, str]:
    token = client.post(
        "/api/v1/auth/student/login",
        json={"email": student.email, "password": STUDENT_PASSWORD},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_branch(session: Session, index: int = 1, **overrides: object) -> Branch:
    values: dict = {
        "code": f"LHR{index}",
        "name": "Lahore Gulberg Campus",
        "city": "Lahore",
        "address": "Gulberg III",
        "contact_phone": f"+923{100 + index:09d}",
    }
    values.update(overrides)
    branch = Branch(**values)
    session.add(branch)
    session.commit()
    return branch


def create_course(session: Session, index: int = 1, **overrides: object) -> Course:
    values: dict = {
        "code": f"CS-{2100 + index}",
        "title": "Data Structures",
        "credit_hours": 3,
        "department": "Computer Science",
    }
    values.update(overrides)
    course = Course(**values)
    session.add(course)
    session.commit()
    return course


def create_courses(
    session: Session, count: int = 4, start: int = 1, **overrides: object
) -> list[Course]:
    return [create_course(session, index, **overrides) for index in range(start, start + count)]


def assign_courses(session: Session, student: Student, courses: list[Course]) -> None:
    for course in courses:
        session.add(CourseAssignment(student_id=student.id, course_id=course.id))
    session.commit()


def create_slot(
    session: Session,
    course: Course,
    days_ahead: int = 10,
    start: time = time(9, 0),
    hours: int = 3,
    seats_per_branch: int = 40,
    end_time_set: bool = True,
) -> ExamSlot:
    starts_at = datetime.combine(
        datetime.now(UTC).date() + timedelta(days=days_ahead), start, tzinfo=UTC
    )
    slot = ExamSlot(
        course_id=course.id,
        starts_at=starts_at,
        ends_at=starts_at + timedelta(hours=hours),
        end_time_set=end_time_set,
        seats_per_branch=seats_per_branch,
    )
    session.add(slot)
    session.commit()
    return slot


def create_entry(
    session: Session, student: Student, course: Course, slot: ExamSlot
) -> DateSheetEntry:
    entry = DateSheetEntry(
        student_id=student.id,
        course_id=course.id,
        slot_id=slot.id,
        branch_id=student.branch_id,
        period=Range(slot.starts_at, slot.ends_at, bounds="[)"),
    )
    session.add(entry)
    session.commit()
    return entry
