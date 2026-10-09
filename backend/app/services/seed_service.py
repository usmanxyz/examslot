from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import Range
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.passwords import PasswordService
from app.models.admin import Admin
from app.models.branch import Branch
from app.models.change_request import ChangeRequest
from app.models.course import Course
from app.models.course_assignment import CourseAssignment
from app.models.date_sheet_entry import DateSheetEntry
from app.models.exam_slot import ExamSlot
from app.models.password_token import PasswordToken
from app.models.student import Student
from app.models.student_photo import StudentPhoto
from app.utils.normalize import (
    normalize_code,
    normalize_email,
    normalize_mobile,
    normalize_name,
    normalize_phone,
)
from app.utils.timeutil import to_utc


class SeedSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SEED_INBOX: str
    SEED_ADMIN_EMAIL: str
    SEED_ADMIN_PASSWORD: str
    SEED_STUDENT_PASSWORD: str


class SeedBlockedError(RuntimeError):
    pass


@dataclass(frozen=True)
class SeedStudent:
    index: int
    full_name: str
    branch_code: str | None
    courses: tuple[tuple[str, str | None], ...]
    has_password: bool
    saved: bool


BRANCHES = (
    ("LHR", "Lahore Gulberg Campus", "Lahore", "Gulberg III", "0300 0000101"),
    ("ISB", "Islamabad Blue Area Campus", "Islamabad", "Blue Area", "0300 0000102"),
    ("KHI", "Karachi Clifton Campus", "Karachi", "Clifton Block 5", "0300 0000103"),
)

COURSES = (
    ("CS-2101", "Data Structures", 3, "Computer Science"),
    ("CS-2203", "Database Systems", 3, "Computer Science"),
    ("CS-2304", "Operating Systems", 3, "Computer Science"),
    ("CS-3105", "Software Engineering", 3, "Computer Science"),
    ("CS-3208", "Computer Networks", 3, "Computer Science"),
    ("MT-2101", "Linear Algebra", 3, "Mathematics"),
    ("MT-2202", "Probability and Statistics", 3, "Mathematics"),
    ("HU-1101", "Technical Writing", 2, "Humanities"),
)

SLOTS = (
    ("CS-2101", "A", 1, time(9, 0), time(12, 0), 40),
    ("CS-2101", "B", 4, time(9, 0), time(12, 0), 40),
    ("CS-2203", "A", 1, time(10, 30), time(13, 30), 40),
    ("CS-2203", "B", 2, time(14, 0), time(17, 0), 40),
    ("CS-2304", "A", 2, time(9, 0), time(12, 0), 40),
    ("CS-2304", "B", 5, time(9, 0), time(12, 0), 40),
    ("CS-3105", "A", 4, time(14, 0), time(17, 0), 40),
    ("CS-3105", "B", 6, time(14, 0), time(17, 0), 40),
    ("CS-3208", "A", 5, time(14, 0), time(17, 0), 40),
    ("CS-3208", "B", 6, time(9, 0), time(12, 0), 40),
    ("MT-2101", "A", 1, time(14, 0), time(17, 0), 40),
    ("MT-2101", "B", 5, time(14, 0), time(17, 0), 40),
    ("MT-2202", "A", 3, time(9, 0), time(12, 0), 2),
    ("MT-2202", "B", 6, time(9, 0), time(12, 0), 40),
    ("HU-1101", "A", 3, time(14, 0), None, 40),
)

AYESHA_COURSES = (
    ("CS-2101", None),
    ("CS-2203", None),
    ("CS-2304", None),
    ("MT-2202", None),
    ("HU-1101", None),
)

STUDENTS = (
    SeedStudent(1, "Ayesha Siddiqui", None, AYESHA_COURSES, True, False),
    SeedStudent(2, "Hamza Rauf", None, (), False, False),
    SeedStudent(
        3,
        "Mahnoor Tariq",
        "LHR",
        (("CS-2101", "A"), ("MT-2101", "A"), ("MT-2202", "A"), ("HU-1101", "A")),
        True,
        True,
    ),
    SeedStudent(
        4,
        "Bilal Ahmed",
        "ISB",
        (
            ("CS-2101", "B"),
            ("CS-2203", "B"),
            ("CS-2304", "A"),
            ("CS-3105", "A"),
            ("CS-3208", "A"),
            ("MT-2101", "A"),
        ),
        True,
        True,
    ),
    SeedStudent(
        5,
        "Zainab Qureshi",
        "KHI",
        (
            ("CS-2203", "A"),
            ("CS-3105", "B"),
            ("CS-3208", "B"),
            ("MT-2202", "A"),
            ("HU-1101", "A"),
        ),
        True,
        True,
    ),
    SeedStudent(6, "Fatima Noor", None, AYESHA_COURSES, True, False),
    SeedStudent(7, "Usman Javed", None, AYESHA_COURSES, True, False),
    SeedStudent(
        8,
        "Areeba Khan",
        None,
        (("CS-2101", None), ("CS-2203", None), ("CS-2304", None), ("MT-2101", None)),
        False,
        False,
    ),
    SeedStudent(
        9,
        "Taimoor Abbas",
        None,
        (("CS-3105", None), ("CS-3208", None), ("MT-2202", None), ("HU-1101", None)),
        False,
        False,
    ),
    SeedStudent(10, "Sana Riaz", None, (), False, False),
    SeedStudent(11, "Hassan Malik", None, (), True, False),
    SeedStudent(12, "Rabia Aslam", None, (), True, False),
    SeedStudent(
        13,
        "Daniyal Shah",
        "LHR",
        (("CS-2101", None), ("CS-2203", None), ("CS-2304", None), ("CS-3105", None)),
        True,
        False,
    ),
    SeedStudent(
        14,
        "Komal Nawaz",
        "ISB",
        (
            ("CS-2304", None),
            ("CS-3105", None),
            ("CS-3208", None),
            ("MT-2101", None),
            ("MT-2202", None),
        ),
        True,
        False,
    ),
    SeedStudent(
        15,
        "Faizan Iqbal",
        "KHI",
        (("CS-2101", None), ("MT-2101", None), ("MT-2202", None), ("HU-1101", None)),
        True,
        False,
    ),
    SeedStudent(
        16,
        "Hira Bashir",
        "LHR",
        (
            ("CS-2101", "A"),
            ("MT-2101", "A"),
            ("CS-2304", "A"),
            ("CS-2203", "B"),
            ("CS-3208", "B"),
        ),
        True,
        True,
    ),
    SeedStudent(
        17,
        "Ahmed Raza",
        "ISB",
        (
            ("CS-2101", "B"),
            ("CS-3105", "A"),
            ("CS-2304", "B"),
            ("CS-3208", "A"),
            ("MT-2202", "B"),
            ("CS-2203", "B"),
        ),
        True,
        True,
    ),
    SeedStudent(
        18,
        "Noor Fatima",
        "KHI",
        (
            ("CS-2203", "A"),
            ("MT-2101", "B"),
            ("CS-2304", "B"),
            ("HU-1101", "A"),
            ("MT-2202", "B"),
        ),
        True,
        True,
    ),
    SeedStudent(
        19,
        "Shahzaib Butt",
        "LHR",
        (("CS-3105", "B"), ("CS-3208", "B"), ("CS-2101", "A"), ("MT-2101", "A")),
        True,
        True,
    ),
    SeedStudent(
        20,
        "Maryam Zafar",
        "ISB",
        (
            ("CS-2203", "B"),
            ("CS-2304", "A"),
            ("CS-3105", "A"),
            ("CS-2101", "B"),
            ("HU-1101", "A"),
            ("MT-2202", "B"),
        ),
        True,
        True,
    ),
)

REQUESTS = (
    (
        3,
        "date_sheet_change",
        "My Linear Algebra exam falls on the day of a family wedding in another city.",
        "pending",
        None,
    ),
    (
        4,
        "branch_change",
        "I have moved to Lahore for the whole semester and cannot travel to Islamabad.",
        "approved",
        "Approved. Choose your new branch once.",
    ),
    (
        5,
        "date_sheet_change",
        "I would like to move my Technical Writing exam to a later day if that is possible.",
        "rejected",
        "Exam times cannot change this close to the exams.",
    ),
)

GENDERS = ("female", "male", "transgender", "prefer_not_to_say")
PROGRAMS = ("BS Computer Science", "BS Software Engineering", "BS Mathematics")
QUALIFICATIONS = ("FSc Pre-Engineering", "Intermediate in Computer Science", "A Levels")
INSTITUTES = ("Government College Lahore", "Punjab College Islamabad", "Adamjee Science College")
OCCUPATIONS = ("Teacher", "Shopkeeper", "Engineer", "Farmer", "Accountant")
GUARDIAN_FIRST_NAMES = ("Abdul Rauf", "Mohammad Aslam", "Khalid", "Rehmat Ali", "Tariq")

RESET_MODELS = (
    DateSheetEntry,
    ChangeRequest,
    PasswordToken,
    StudentPhoto,
    CourseAssignment,
    ExamSlot,
    Student,
    Course,
    Branch,
)


def seed_demo(
    session: Session,
    passwords: PasswordService,
    settings: Settings,
    seed: SeedSettings,
    reset: bool = False,
) -> dict[str, int]:
    if reset:
        for model in RESET_MODELS:
            session.execute(delete(model))
    elif session.scalar(select(func.count()).select_from(Student)):
        raise SeedBlockedError(
            "Students already exist. Run seed-demo --reset to replace the demonstration data."
        )

    admins = _seed_admin(session, passwords, seed)
    branches = _seed_branches(session)
    courses = _seed_courses(session)
    slots = _seed_slots(session, courses, settings)
    counts = _seed_students(session, passwords, seed, branches, courses, slots)
    session.commit()

    return {
        "admins": admins,
        "branches": len(branches),
        "courses": len(courses),
        "exam_slots": len(slots),
        **counts,
    }


def exam_days(today: date) -> dict[int, date]:
    day = today + timedelta(days=10)
    days: dict[int, date] = {}
    while len(days) < 6:
        if day.weekday() != 6:
            days[len(days) + 1] = day
        day += timedelta(days=1)
    return days


def _seed_admin(session: Session, passwords: PasswordService, seed: SeedSettings) -> int:
    email = normalize_email(seed.SEED_ADMIN_EMAIL)
    if session.scalar(select(Admin.id).where(Admin.email == email)) is not None:
        return 0
    session.add(
        Admin(
            email=email,
            full_name=normalize_name("Exam Office"),
            password_hash=passwords.hash(seed.SEED_ADMIN_PASSWORD),
        )
    )
    session.flush()
    return 1


def _seed_branches(session: Session) -> dict[str, Branch]:
    branches = {}
    for code, name, city, address, contact_phone in BRANCHES:
        branch = Branch(
            code=normalize_code(code),
            name=normalize_name(name),
            city=normalize_name(city),
            address=normalize_name(address),
            contact_phone=normalize_phone(contact_phone),
        )
        session.add(branch)
        branches[code] = branch
    session.flush()
    return branches


def _seed_courses(session: Session) -> dict[str, Course]:
    courses = {}
    for code, title, credit_hours, department in COURSES:
        course = Course(
            code=normalize_code(code),
            title=normalize_name(title),
            credit_hours=credit_hours,
            department=normalize_name(department),
        )
        session.add(course)
        courses[code] = course
    session.flush()
    return courses


def _seed_slots(
    session: Session, courses: dict[str, Course], settings: Settings
) -> dict[tuple[str, str], ExamSlot]:
    days = exam_days(datetime.now(UTC).date())
    slots = {}
    for code, letter, day_index, starts, ends, seats in SLOTS:
        starts_at = to_utc(days[day_index], starts, settings.APP_TIMEZONE)
        if ends is None:
            ends_at = starts_at + timedelta(minutes=settings.DEFAULT_EXAM_MINUTES)
        else:
            ends_at = to_utc(days[day_index], ends, settings.APP_TIMEZONE)
        slot = ExamSlot(
            course_id=courses[code].id,
            starts_at=starts_at,
            ends_at=ends_at,
            end_time_set=ends is not None,
            seats_per_branch=seats,
        )
        session.add(slot)
        slots[(code, letter)] = slot
    session.flush()
    return slots


def _seed_students(
    session: Session,
    passwords: PasswordService,
    seed: SeedSettings,
    branches: dict[str, Branch],
    courses: dict[str, Course],
    slots: dict[tuple[str, str], ExamSlot],
) -> dict[str, int]:
    password_hash = passwords.hash(seed.SEED_STUDENT_PASSWORD)
    now = datetime.now(UTC)
    students: dict[int, Student] = {}
    assignments = 0
    entries = 0

    for seed_student in STUDENTS:
        branch = branches[seed_student.branch_code] if seed_student.branch_code else None
        student = Student(
            **_identity(seed_student, seed.SEED_INBOX),
            password_hash=password_hash if seed_student.has_password else None,
            password_set_at=now if seed_student.has_password else None,
            branch_id=branch.id if branch else None,
            branch_selected_at=now if branch else None,
            date_sheet_saved_at=now if seed_student.saved else None,
        )
        session.add(student)
        session.flush()
        students[seed_student.index] = student

        for code, _ in seed_student.courses:
            session.add(CourseAssignment(student_id=student.id, course_id=courses[code].id))
            assignments += 1
        session.flush()

        if not seed_student.saved:
            continue
        for code, letter in seed_student.courses:
            slot = slots[(code, letter)]
            session.add(
                DateSheetEntry(
                    student_id=student.id,
                    course_id=courses[code].id,
                    slot_id=slot.id,
                    branch_id=student.branch_id,
                    period=Range(slot.starts_at, slot.ends_at, bounds="[)"),
                )
            )
            entries += 1
        session.flush()

    admin_id = session.scalar(select(Admin.id).order_by(Admin.created_at))
    for index, kind, reason, status, remark in REQUESTS:
        decided = status != "pending"
        session.add(
            ChangeRequest(
                student_id=students[index].id,
                type=kind,
                reason=reason,
                status=status,
                admin_remark=remark,
                decided_at=now if decided else None,
                decided_by=admin_id if decided else None,
            )
        )
    session.flush()

    return {
        "students": len(students),
        "course_assignments": assignments,
        "date_sheet_entries": entries,
        "change_requests": len(REQUESTS),
    }


def _identity(seed_student: SeedStudent, inbox: str) -> dict[str, object]:
    index = seed_student.index
    full_name = normalize_name(seed_student.full_name)
    surname = full_name.rsplit(" ", 1)[-1]
    local_part, domain = normalize_email(inbox).split("@", 1)
    slug = full_name.lower().replace(" ", ".")
    percentage = index % 2 == 1
    return {
        "registration_no": normalize_code(f"2024-CS-{index:04d}"),
        "email": normalize_email(f"{local_part}+{slug}@{domain}"),
        "full_name": full_name,
        "phone": normalize_mobile(f"+923{200 + index:09d}"),
        "cnic": f"{index:013d}",
        "date_of_birth": date(2004, 1, 1) + timedelta(days=index * 11),
        "gender": GENDERS[index % len(GENDERS)],
        "address": normalize_name(f"House {index}, Street {index + 4}, Model Town"),
        "guardian_name": normalize_name(
            f"{GUARDIAN_FIRST_NAMES[index % len(GUARDIAN_FIRST_NAMES)]} {surname}"
        ),
        "guardian_cnic": f"{500 + index:013d}",
        "guardian_occupation": OCCUPATIONS[index % len(OCCUPATIONS)],
        "guardian_phone": normalize_mobile(f"+923{300 + index:09d}"),
        "emergency_phone": normalize_phone(f"+923{400 + index:09d}"),
        "program": PROGRAMS[index % len(PROGRAMS)],
        "semester": 4 + index % 4,
        "session": "2024-2028",
        "previous_qualification": QUALIFICATIONS[index % len(QUALIFICATIONS)],
        "previous_institute": INSTITUTES[index % len(INSTITUTES)],
        "previous_score_type": "percentage" if percentage else "cgpa",
        "previous_score": Decimal(f"{70 + index % 25}.50")
        if percentage
        else Decimal(f"{2 + (index % 20) / 10:.2f}"),
    }
