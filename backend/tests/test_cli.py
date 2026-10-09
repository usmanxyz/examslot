import io

import pytest
from sqlalchemy import select, text

from app.cli import main
from app.models.admin import Admin
from app.services.seed_service import SLOTS, STUDENTS

ADMIN_PASSWORD = "a-long-admin-password"


@pytest.fixture(autouse=True)
def cli_environment(monkeypatch, database_url):
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("SEED_INBOX", "inbox@example.com")
    monkeypatch.setenv("SEED_ADMIN_EMAIL", "inbox+admin@example.com")
    monkeypatch.setenv("SEED_ADMIN_PASSWORD", "a-long-seed-admin-password")
    monkeypatch.setenv("SEED_STUDENT_PASSWORD", "a-long-seed-student-password")


def answer(monkeypatch, password: str, confirm: bool = True) -> None:
    lines = f"{password}\n{password}\n" if confirm else f"{password}\n"
    monkeypatch.setattr("sys.stdin", io.StringIO(lines))


def test_seed_demo_creates_the_specified_counts(session):
    assert main(["seed-demo"]) == 0

    assert session.scalar(text("SELECT count(*) FROM admins")) == 1
    assert session.scalar(text("SELECT count(*) FROM branches")) == 3
    assert session.scalar(text("SELECT count(*) FROM courses")) == 8
    assert session.scalar(text("SELECT count(*) FROM exam_slots")) == len(SLOTS)
    assert session.scalar(text("SELECT count(*) FROM students")) == len(STUDENTS)
    assert session.scalar(text("SELECT count(*) FROM change_requests")) == 3


def test_seed_demo_creates_every_student_state(session):
    main(["seed-demo"])

    assert session.scalar(text("SELECT count(*) FROM students WHERE password_hash IS NULL")) == 4
    assert (
        session.scalar(text("SELECT count(*) FROM students WHERE date_sheet_saved_at IS NOT NULL"))
        == 8
    )
    assert session.scalar(text("SELECT count(*) FROM students WHERE branch_id IS NULL")) == 9
    assert (
        session.scalar(
            text(
                "SELECT count(*) FROM students s WHERE NOT EXISTS"
                " (SELECT 1 FROM course_assignments a WHERE a.student_id = s.id)"
            )
        )
        == 4
    )


def test_seed_demo_creates_the_designed_demo_cases(session):
    main(["seed-demo"])

    assert (
        session.scalar(
            text(
                "SELECT count(*) FROM date_sheet_entries e"
                " JOIN exam_slots s ON s.id = e.slot_id"
                " JOIN courses c ON c.id = s.course_id"
                " JOIN branches b ON b.id = e.branch_id"
                " WHERE c.code = 'MT-2202' AND s.seats_per_branch = 2 AND b.code = 'LHR'"
            )
        )
        == 1
    )
    assert session.scalar(text("SELECT count(*) FROM exam_slots WHERE NOT end_time_set")) == 1
    assert (
        session.scalar(
            text(
                "SELECT min((starts_at AT TIME ZONE 'Asia/Karachi')::date) - current_date"
                " FROM exam_slots"
            )
        )
        >= 10
    )
    assert (
        session.scalar(
            text(
                "SELECT count(*) FROM exam_slots"
                " WHERE extract(isodow FROM starts_at AT TIME ZONE 'Asia/Karachi') = 7"
            )
        )
        == 0
    )
    statuses = session.execute(
        text("SELECT status, count(*) FROM change_requests GROUP BY status")
    ).all()
    assert dict(statuses) == {"pending": 1, "approved": 1, "rejected": 1}
    assert (
        session.scalar(
            text(
                "SELECT count(*) FROM change_requests"
                " WHERE status = 'approved' AND used_at IS NULL AND type = 'branch_change'"
            )
        )
        == 1
    )


def test_seed_demo_entries_match_the_assignments_of_saved_students(session):
    main(["seed-demo"])

    assert (
        session.scalar(
            text(
                "SELECT count(*) FROM students s"
                " WHERE s.date_sheet_saved_at IS NOT NULL AND"
                " (SELECT count(*) FROM course_assignments a WHERE a.student_id = s.id) <>"
                " (SELECT count(*) FROM date_sheet_entries e WHERE e.student_id = s.id)"
            )
        )
        == 0
    )


def test_seed_demo_refuses_a_second_run(session):
    assert main(["seed-demo"]) == 0

    assert main(["seed-demo"]) == 1
    assert session.scalar(text("SELECT count(*) FROM students")) == len(STUDENTS)


def test_seed_demo_reset_replaces_the_data(session):
    main(["seed-demo"])
    before = session.scalar(
        text("SELECT id FROM students WHERE registration_no = '2024-CS-0001'")
    )

    assert main(["seed-demo", "--reset"]) == 0

    assert (
        session.scalar(text("SELECT id FROM students WHERE registration_no = '2024-CS-0001'"))
        != before
    )
    assert session.scalar(text("SELECT count(*) FROM students")) == len(STUDENTS)
    assert session.scalar(text("SELECT count(*) FROM admins")) == 1


def test_create_admin_stores_an_argon2id_hash(monkeypatch, session):
    answer(monkeypatch, ADMIN_PASSWORD)

    assert main(["create-admin", "--email", "Office@Example.com", "--name", "Exam  Office"]) == 0

    admin = session.scalar(select(Admin).where(Admin.email == "office@example.com"))
    assert admin.full_name == "Exam Office"
    assert admin.password_hash.startswith("$argon2id$v=19$m=19456,t=2,p=1$")
    assert admin.is_active is True
    assert admin.token_version == 0


def test_create_admin_refuses_a_duplicate_email(monkeypatch, session):
    answer(monkeypatch, ADMIN_PASSWORD)
    assert main(["create-admin", "--email", "office@example.com", "--name", "Exam Office"]) == 0
    answer(monkeypatch, "a-different-long-password")

    assert main(["create-admin", "--email", "Office@example.com", "--name", "Exam Office"]) == 1
    assert session.scalar(text("SELECT count(*) FROM admins")) == 1


def test_create_admin_rejects_a_password_outside_the_policy(monkeypatch, session):
    answer(monkeypatch, "short")

    assert main(["create-admin", "--email", "office@example.com", "--name", "Exam Office"]) == 1
    assert session.scalar(text("SELECT count(*) FROM admins")) == 0


def test_reset_admin_password_increments_token_version(monkeypatch, session):
    answer(monkeypatch, ADMIN_PASSWORD)
    main(["create-admin", "--email", "office@example.com", "--name", "Exam Office"])
    answer(monkeypatch, "a-different-long-password", confirm=False)

    assert main(["reset-admin-password", "--email", "office@example.com"]) == 0

    admin = session.scalar(select(Admin).where(Admin.email == "office@example.com"))
    assert admin.token_version == 1
    assert admin.password_hash.startswith("$argon2id$")


def test_deactivate_admin_blocks_the_account(monkeypatch, session):
    answer(monkeypatch, ADMIN_PASSWORD)
    main(["create-admin", "--email", "office@example.com", "--name", "Exam Office"])

    assert main(["deactivate-admin", "--email", "office@example.com"]) == 0

    admin = session.scalar(select(Admin).where(Admin.email == "office@example.com"))
    assert admin.is_active is False
    assert admin.token_version == 1
