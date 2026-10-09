from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.passwords import PasswordService
from app.models.admin import Admin
from app.models.branch import Branch
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
