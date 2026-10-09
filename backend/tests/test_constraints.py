import uuid
from contextlib import contextmanager
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import Connection, text
from sqlalchemy.exc import IntegrityError

DAY = datetime(2026, 10, 27, 4, 0, tzinfo=UTC)

STUDENT_COLUMNS = (
    "registration_no",
    "email",
    "full_name",
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
    "program",
    "semester",
    "session",
    "previous_qualification",
    "previous_institute",
    "previous_score_type",
    "previous_score",
    "branch_id",
    "branch_selected_at",
    "date_sheet_saved_at",
)

INSERT_STUDENT = text(
    f"INSERT INTO students ({', '.join(STUDENT_COLUMNS)})"
    f" VALUES ({', '.join(f':{column}' for column in STUDENT_COLUMNS)}) RETURNING id"
)

INSERT_BRANCH = text(
    "INSERT INTO branches (code, name, city, address, contact_phone)"
    " VALUES (:code, :name, 'Lahore', 'Gulberg III', :contact_phone) RETURNING id"
)

INSERT_COURSE = text(
    "INSERT INTO courses (code, title, credit_hours, department)"
    " VALUES (:code, 'Data Structures', 3, 'Computer Science') RETURNING id"
)

INSERT_SLOT = text(
    "INSERT INTO exam_slots (course_id, starts_at, ends_at, end_time_set, seats_per_branch)"
    " VALUES (:course_id, :starts_at, :ends_at, true, 40) RETURNING id"
)

INSERT_ASSIGNMENT = text(
    "INSERT INTO course_assignments (student_id, course_id) VALUES (:student_id, :course_id)"
)

INSERT_ENTRY_FROM_SLOT = text(
    "INSERT INTO date_sheet_entries (student_id, course_id, slot_id, branch_id, period)"
    " SELECT :student_id, :course_id, :slot_id, :branch_id, exam_slots.period"
    " FROM exam_slots WHERE exam_slots.id = :slot_id"
)

INSERT_ENTRY_WITH_PERIOD = text(
    "INSERT INTO date_sheet_entries (student_id, course_id, slot_id, branch_id, period)"
    " VALUES (:student_id, :course_id, :slot_id, :branch_id, tstzrange(:starts_at, :ends_at, '[)'))"
)

INSERT_ADMIN = text(
    "INSERT INTO admins (email, full_name, password_hash)"
    " VALUES (:email, 'Exam Office', 'argon2-hash') RETURNING id"
)

INSERT_REQUEST = text(
    "INSERT INTO change_requests (student_id, type, reason, status, admin_remark, decided_at, used_at)"
    " VALUES (:student_id, :type, 'A reason long enough to pass the check.', :status,"
    " :admin_remark, :decided_at, :used_at) RETURNING id"
)

INSERT_TOKEN = text(
    "INSERT INTO password_tokens (student_id, purpose, secret_hash, expires_at, used_at, revoked_at)"
    " VALUES (:student_id, 'setup', 'argon2-hash', :expires_at, :used_at, :revoked_at) RETURNING id"
)


@contextmanager
def violates(constraint: str):
    with pytest.raises(IntegrityError) as error:
        yield
    assert error.value.orig.diag.constraint_name == constraint


def student_values(index: int = 1, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "registration_no": f"2024-CS-{index:04d}",
        "email": f"student{index}@example.com",
        "full_name": "Test Student",
        "phone": f"+923{200 + index:09d}",
        "cnic": f"{index:013d}",
        "date_of_birth": date(2004, 1, 1),
        "gender": "female",
        "address": "House 1, Model Town",
        "guardian_name": "Test Guardian",
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
        "branch_id": None,
        "branch_selected_at": None,
        "date_sheet_saved_at": None,
    }
    values.update(overrides)
    return values


def insert_student(connection: Connection, index: int = 1, **overrides: object) -> uuid.UUID:
    return connection.scalar(INSERT_STUDENT, student_values(index, **overrides))


def insert_branch(connection: Connection, index: int = 1, **overrides: object) -> uuid.UUID:
    values = {
        "code": f"LHR{index}",
        "name": "Lahore Gulberg Campus",
        "contact_phone": f"+923{100 + index:09d}",
    }
    values.update(overrides)
    return connection.scalar(INSERT_BRANCH, values)


def insert_course(connection: Connection, index: int = 1, **overrides: object) -> uuid.UUID:
    values = {"code": f"CS-{2100 + index}"}
    values.update(overrides)
    return connection.scalar(INSERT_COURSE, values)


def insert_slot(
    connection: Connection,
    course_id: uuid.UUID,
    starts_at: datetime = DAY,
    ends_at: datetime | None = None,
) -> uuid.UUID:
    return connection.scalar(
        INSERT_SLOT,
        {
            "course_id": course_id,
            "starts_at": starts_at,
            "ends_at": ends_at or starts_at + timedelta(hours=3),
        },
    )


def insert_assignment(connection: Connection, student_id: uuid.UUID, course_id: uuid.UUID) -> None:
    connection.execute(INSERT_ASSIGNMENT, {"student_id": student_id, "course_id": course_id})


def insert_entry(
    connection: Connection,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    slot_id: uuid.UUID,
    branch_id: uuid.UUID,
) -> None:
    connection.execute(
        INSERT_ENTRY_FROM_SLOT,
        {
            "student_id": student_id,
            "course_id": course_id,
            "slot_id": slot_id,
            "branch_id": branch_id,
        },
    )


def enrolled_student(
    connection: Connection, course_count: int = 4
) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
    branch_id = insert_branch(connection)
    student_id = insert_student(
        connection, branch_id=branch_id, branch_selected_at=datetime.now(UTC)
    )
    course_ids = []
    for index in range(1, course_count + 1):
        course_id = insert_course(connection, index)
        insert_assignment(connection, student_id, course_id)
        course_ids.append(course_id)
    return student_id, branch_id, course_ids


def test_student_email_is_unique(connection):
    insert_student(connection, 1, email="shared@example.com")

    with violates("students_email_key"):
        insert_student(connection, 2, email="shared@example.com")


def test_student_registration_no_is_unique(connection):
    insert_student(connection, 1)

    with violates("students_registration_no_key"):
        insert_student(connection, 2, registration_no="2024-CS-0001")


def test_student_cnic_is_unique(connection):
    insert_student(connection, 1)

    with violates("students_cnic_key"):
        insert_student(connection, 2, cnic="0000000000001")


def test_branch_code_is_unique(connection):
    insert_branch(connection, 1, code="LHR")

    with violates("branches_code_key"):
        insert_branch(connection, 2, code="LHR")


def test_course_code_is_unique(connection):
    insert_course(connection, 1, code="CS-2101")

    with violates("courses_code_key"):
        insert_course(connection, 2, code="CS-2101")


def test_admin_email_is_unique(connection):
    connection.execute(INSERT_ADMIN, {"email": "office@example.com"})

    with violates("admins_email_key"):
        connection.execute(INSERT_ADMIN, {"email": "office@example.com"})


def test_student_cnic_must_be_thirteen_digits(connection):
    with violates("students_cnic_format"):
        insert_student(connection, cnic="abcdefghijklm")


def test_guardian_cnic_must_be_thirteen_digits(connection):
    with violates("students_guardian_cnic_format"):
        insert_student(connection, guardian_cnic="35202-12345-1")


@pytest.mark.parametrize(
    ("field", "constraint"),
    [
        ("phone", "students_phone_format"),
        ("guardian_phone", "students_guardian_phone_format"),
    ],
)
def test_student_phones_must_be_pakistani_mobiles(connection, field, constraint):
    with violates(constraint):
        insert_student(connection, **{field: "+924235761234"})


def test_emergency_phone_must_be_a_pakistani_number(connection):
    with violates("students_emergency_phone_format"):
        insert_student(connection, emergency_phone="0300 1234567")


def test_emergency_phone_accepts_a_landline(connection):
    insert_student(connection, emergency_phone="+924235761234")


def test_branch_contact_phone_must_be_a_pakistani_number(connection):
    with violates("branches_contact_phone_format"):
        insert_branch(connection, contact_phone="042-35761234")


@pytest.mark.parametrize(
    ("score_type", "score"),
    [("percentage", Decimal("100.01")), ("cgpa", Decimal("4.01")), ("cgpa", Decimal("82.50"))],
)
def test_previous_score_outside_its_range_is_rejected(connection, score_type, score):
    with violates("students_previous_score_range"):
        insert_student(connection, previous_score_type=score_type, previous_score=score)


@pytest.mark.parametrize(
    ("score_type", "score"),
    [("percentage", Decimal("100.00")), ("percentage", Decimal("0")), ("cgpa", Decimal("4.00"))],
)
def test_previous_score_inside_its_range_is_accepted(connection, score_type, score):
    insert_student(connection, previous_score_type=score_type, previous_score=score)


def test_branch_without_a_selection_time_is_rejected(connection):
    branch_id = insert_branch(connection)

    with violates("students_branch_pair"):
        insert_student(connection, branch_id=branch_id)


def test_selection_time_without_a_branch_is_rejected(connection):
    with violates("students_branch_pair"):
        insert_student(connection, branch_selected_at=datetime.now(UTC))


def test_branch_with_a_selection_time_is_accepted(connection):
    branch_id = insert_branch(connection)

    insert_student(connection, branch_id=branch_id, branch_selected_at=datetime.now(UTC))


def test_a_course_cannot_be_assigned_twice(connection):
    student_id = insert_student(connection)
    course_id = insert_course(connection)
    insert_assignment(connection, student_id, course_id)

    with violates("course_assignments_pkey"):
        insert_assignment(connection, student_id, course_id)


@pytest.mark.parametrize("count", [0, 4, 5, 6])
def test_allowed_assignment_counts_commit(connection, count):
    student_id = insert_student(connection)
    for index in range(1, count + 1):
        insert_assignment(connection, student_id, insert_course(connection, index))

    connection.commit()

    assert connection.scalar(
        text("SELECT count(*) FROM course_assignments WHERE student_id = :id"), {"id": student_id}
    ) == count


@pytest.mark.parametrize("count", [3, 7])
def test_forbidden_assignment_counts_are_rejected_at_commit(connection, count):
    student_id = insert_student(connection)
    for index in range(1, count + 1):
        insert_assignment(connection, student_id, insert_course(connection, index))

    with violates("course_assignments_count"):
        connection.commit()


def test_slot_end_must_be_after_its_start(connection):
    course_id = insert_course(connection)

    with violates("exam_slots_end_after_start"):
        insert_slot(connection, course_id, DAY, DAY)


def test_a_course_cannot_have_two_slots_with_one_start(connection):
    course_id = insert_course(connection)
    insert_slot(connection, course_id, DAY)

    with violates("exam_slots_course_start_key"):
        insert_slot(connection, course_id, DAY, DAY + timedelta(hours=2))


def test_an_entry_needs_an_assignment(connection):
    student_id, branch_id, _ = enrolled_student(connection)
    other_course_id = insert_course(connection, 9)
    slot_id = insert_slot(connection, other_course_id)

    with violates("date_sheet_entries_assignment_fkey"):
        insert_entry(connection, student_id, other_course_id, slot_id, branch_id)


def test_an_entry_cannot_point_at_another_courses_slot(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    slot_id = insert_slot(connection, course_ids[1])

    with violates("date_sheet_entries_slot_fkey"):
        insert_entry(connection, student_id, course_ids[0], slot_id, branch_id)


def test_an_entry_period_must_match_its_slot(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    slot_id = insert_slot(connection, course_ids[0])

    with violates("date_sheet_entries_slot_fkey"):
        connection.execute(
            INSERT_ENTRY_WITH_PERIOD,
            {
                "student_id": student_id,
                "course_id": course_ids[0],
                "slot_id": slot_id,
                "branch_id": branch_id,
                "starts_at": DAY,
                "ends_at": DAY + timedelta(hours=4),
            },
        )


def test_one_student_cannot_have_two_slots_for_one_course(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    first = insert_slot(connection, course_ids[0], DAY)
    second = insert_slot(connection, course_ids[0], DAY + timedelta(days=1))
    insert_entry(connection, student_id, course_ids[0], first, branch_id)

    with violates("date_sheet_entries_student_course_key"):
        insert_entry(connection, student_id, course_ids[0], second, branch_id)


def test_overlapping_entries_are_rejected(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    first = insert_slot(connection, course_ids[0], DAY)
    second = insert_slot(connection, course_ids[1], DAY + timedelta(minutes=90))
    insert_entry(connection, student_id, course_ids[0], first, branch_id)

    with violates("date_sheet_entries_no_overlap"):
        insert_entry(connection, student_id, course_ids[1], second, branch_id)


def test_back_to_back_entries_are_accepted(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    first = insert_slot(connection, course_ids[0], DAY, DAY + timedelta(hours=3))
    second = insert_slot(connection, course_ids[1], DAY + timedelta(hours=3))
    insert_entry(connection, student_id, course_ids[0], first, branch_id)

    insert_entry(connection, student_id, course_ids[1], second, branch_id)

    assert connection.scalar(
        text("SELECT count(*) FROM date_sheet_entries WHERE student_id = :id"), {"id": student_id}
    ) == 2


def test_a_chosen_slot_cannot_be_deleted(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    slot_id = insert_slot(connection, course_ids[0])
    insert_entry(connection, student_id, course_ids[0], slot_id, branch_id)

    with violates("date_sheet_entries_slot_fkey"):
        connection.execute(text("DELETE FROM exam_slots WHERE id = :id"), {"id": slot_id})


def test_a_chosen_slot_cannot_be_retimed(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    slot_id = insert_slot(connection, course_ids[0])
    insert_entry(connection, student_id, course_ids[0], slot_id, branch_id)

    with violates("date_sheet_entries_slot_fkey"):
        connection.execute(
            text("UPDATE exam_slots SET starts_at = :starts_at, ends_at = :ends_at WHERE id = :id"),
            {
                "starts_at": DAY + timedelta(days=1),
                "ends_at": DAY + timedelta(days=1, hours=3),
                "id": slot_id,
            },
        )


def test_an_unchosen_slot_can_be_deleted(connection):
    course_id = insert_course(connection)
    slot_id = insert_slot(connection, course_id)

    connection.execute(text("DELETE FROM exam_slots WHERE id = :id"), {"id": slot_id})

    assert connection.scalar(text("SELECT count(*) FROM exam_slots")) == 0


def test_a_branch_change_cascades_to_entries(connection):
    student_id, branch_id, course_ids = enrolled_student(connection)
    slot_id = insert_slot(connection, course_ids[0])
    insert_entry(connection, student_id, course_ids[0], slot_id, branch_id)
    new_branch_id = insert_branch(connection, 2)

    connection.execute(
        text("UPDATE students SET branch_id = :branch_id WHERE id = :id"),
        {"branch_id": new_branch_id, "id": student_id},
    )

    assert connection.scalar(
        text("SELECT branch_id FROM date_sheet_entries WHERE student_id = :id"), {"id": student_id}
    ) == new_branch_id


def test_a_referenced_branch_cannot_be_deleted(connection):
    branch_id = insert_branch(connection)
    insert_student(connection, branch_id=branch_id, branch_selected_at=datetime.now(UTC))

    with violates("students_branch_id_fkey"):
        connection.execute(text("DELETE FROM branches WHERE id = :id"), {"id": branch_id})


def test_an_unreferenced_branch_can_be_deleted(connection):
    branch_id = insert_branch(connection)

    connection.execute(text("DELETE FROM branches WHERE id = :id"), {"id": branch_id})

    assert connection.scalar(text("SELECT count(*) FROM branches")) == 0


def test_a_student_cannot_have_two_pending_requests_of_one_type(connection):
    student_id = insert_student(connection)
    request(connection, student_id, "branch_change", "pending")

    with violates("change_requests_one_pending"):
        request(connection, student_id, "branch_change", "pending")


def test_a_student_may_have_one_pending_request_of_each_type(connection):
    student_id = insert_student(connection)
    request(connection, student_id, "branch_change", "pending")

    request(connection, student_id, "date_sheet_change", "pending")

    assert connection.scalar(text("SELECT count(*) FROM change_requests")) == 2


def test_a_student_cannot_have_two_unused_approvals_of_one_type(connection):
    student_id = insert_student(connection)
    request(connection, student_id, "branch_change", "approved")

    with violates("change_requests_one_open_reopening"):
        request(connection, student_id, "branch_change", "approved")


def test_a_used_approval_allows_a_new_one(connection):
    student_id = insert_student(connection)
    request(connection, student_id, "branch_change", "approved", used=True)

    request(connection, student_id, "branch_change", "approved")

    assert connection.scalar(text("SELECT count(*) FROM change_requests")) == 2


def test_a_student_cannot_have_two_live_password_tokens(connection):
    student_id = insert_student(connection)
    token(connection, student_id)

    with violates("password_tokens_one_live"):
        token(connection, student_id)


def test_a_revoked_token_allows_a_new_one(connection):
    student_id = insert_student(connection)
    token(connection, student_id, revoked=True)

    token(connection, student_id)

    assert connection.scalar(text("SELECT count(*) FROM password_tokens")) == 2


def request(
    connection: Connection,
    student_id: uuid.UUID,
    kind: str,
    status: str,
    used: bool = False,
) -> uuid.UUID:
    decided = status != "pending"
    return connection.scalar(
        INSERT_REQUEST,
        {
            "student_id": student_id,
            "type": kind,
            "status": status,
            "admin_remark": "Decided." if decided else None,
            "decided_at": datetime.now(UTC) if decided else None,
            "used_at": datetime.now(UTC) if used else None,
        },
    )


def token(
    connection: Connection,
    student_id: uuid.UUID,
    used: bool = False,
    revoked: bool = False,
) -> uuid.UUID:
    return connection.scalar(
        INSERT_TOKEN,
        {
            "student_id": student_id,
            "expires_at": datetime.now(UTC) + timedelta(hours=24),
            "used_at": datetime.now(UTC) if used else None,
            "revoked_at": datetime.now(UTC) if revoked else None,
        },
    )
