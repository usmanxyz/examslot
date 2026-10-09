from sqlalchemy import select

from app.models.password_token import PasswordToken
from tests.factories import (
    STUDENT_PASSWORD,
    admin_headers,
    assign_courses,
    create_branch,
    create_courses,
    create_student,
)

STUDENTS = "/api/v1/admin/students"

PAYLOAD = {
    "full_name": "  Ayesha   Siddiqui ",
    "email": "  Ayesha@Example.COM ",
    "phone": "0300 1234567",
    "cnic": "35202-1234567-1",
    "date_of_birth": "2004-03-14",
    "gender": "female",
    "address": "House 12, Street 4, Johar Town",
    "guardian_name": "Tariq Siddiqui",
    "guardian_cnic": "3520212345672",
    "guardian_occupation": "Civil engineer",
    "guardian_phone": "0301 1234567",
    "emergency_phone": "042 35761234",
    "registration_no": "2024-cs-0001",
    "program": "BS Computer Science",
    "semester": 5,
    "session": "Fall 2024",
    "previous_qualification": "FSc Pre-Engineering",
    "previous_institute": "Higher Secondary School, Lahore",
    "previous_score_type": "percentage",
    "previous_score": "86.50",
}


def test_create_normalizes_invites_and_emails_a_setup_link(client, session, passwords, emails):
    headers = admin_headers(client, session, passwords)

    response = client.post(STUDENTS, json=PAYLOAD, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["full_name"] == "Ayesha Siddiqui"
    assert body["email"] == "ayesha@example.com"
    assert body["phone"] == "+923001234567"
    assert body["cnic"] == "3520212345671"
    assert body["emergency_phone"] == "+924235761234"
    assert body["registration_no"] == "2024-CS-0001"
    assert body["previous_score"] == "86.50"
    assert body["account_status"] == "invited"
    assert body["progress"] == "assignment_incomplete"
    assert body["branch"] is None
    assert body["latest_link"] == {
        "purpose": "setup",
        "delivery_status": "sent",
        "created_at": body["latest_link"]["created_at"],
        "expires_at": body["latest_link"]["expires_at"],
        "used_at": None,
    }
    assert emails[-1].to == "ayesha@example.com"
    assert emails[-1].subject == "Set your ExamSlot password"
    assert "#token=" in emails[-1].text


def test_create_rejects_extra_fields_and_each_taken_value(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    client.post(STUDENTS, json=PAYLOAD, headers=headers)

    extra = client.post(STUDENTS, json={**PAYLOAD, "status": "active"}, headers=headers)
    assert extra.status_code == 422
    assert extra.json()["error"]["details"]["fields"][0]["field"] == "status"

    unique = {"email": "other@example.com", "registration_no": "2024-CS-0002", "cnic": "9999999999999"}
    for field, code in [
        ("email", "EMAIL_TAKEN"),
        ("registration_no", "REGISTRATION_NO_TAKEN"),
        ("cnic", "CNIC_TAKEN"),
    ]:
        body = {**PAYLOAD, **unique, field: PAYLOAD[field]}
        clash = client.post(STUDENTS, json=body, headers=headers)
        assert clash.status_code == 409, field
        assert clash.json()["error"]["code"] == code


def test_create_rejects_a_young_student_and_a_cgpa_out_of_range(client, session, passwords):
    headers = admin_headers(client, session, passwords)

    young = client.post(STUDENTS, json={**PAYLOAD, "date_of_birth": "2020-01-01"}, headers=headers)
    assert young.status_code == 422
    assert young.json()["error"]["details"]["fields"][0]["field"] == "date_of_birth"

    cgpa = client.post(
        STUDENTS,
        json={**PAYLOAD, "previous_score_type": "cgpa", "previous_score": "86.50"},
        headers=headers,
    )
    assert cgpa.status_code == 422
    assert cgpa.json()["error"]["details"]["fields"][0]["field"] == "previous_score"


def test_list_minimizes_data_and_filters_by_derived_state(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    branch = create_branch(session, 1, code="LHR")
    invited = create_student(session, passwords, 1, password=None, full_name="Hamza Rauf")
    planning = create_student(
        session,
        passwords,
        2,
        full_name="Mahnoor Tariq",
        branch_id=branch.id,
        branch_selected_at="2026-10-20",
    )
    assign_courses(session, planning, create_courses(session, 4))

    page = client.get(STUDENTS, headers=headers).json()
    assert page["total"] == 2
    item = next(row for row in page["items"] if row["id"] == str(planning.id))
    assert set(item) == {
        "id",
        "full_name",
        "registration_no",
        "program",
        "semester",
        "account_status",
        "progress",
        "branch",
        "assigned_course_count",
        "created_at",
    }
    assert item["branch"] == {"code": "LHR", "name": "Lahore Gulberg Campus"}
    assert item["assigned_course_count"] == 4
    assert item["progress"] == "planning"

    by_status = client.get(STUDENTS, params={"account_status": "invited"}, headers=headers).json()
    assert [row["id"] for row in by_status["items"]] == [str(invited.id)]

    by_progress = client.get(STUDENTS, params={"progress": "planning"}, headers=headers).json()
    assert [row["id"] for row in by_progress["items"]] == [str(planning.id)]

    by_branch = client.get(
        STUDENTS, params={"branch_id": str(branch.id)}, headers=headers
    ).json()
    assert [row["id"] for row in by_branch["items"]] == [str(planning.id)]

    searched = client.get(STUDENTS, params={"q": "hamza"}, headers=headers).json()
    assert [row["id"] for row in searched["items"]] == [str(invited.id)]


def test_changing_the_email_ends_sessions_and_revokes_the_live_link(
    client, session, passwords, emails
):
    headers = admin_headers(client, session, passwords)
    created = client.post(STUDENTS, json=PAYLOAD, headers=headers).json()
    link_token = emails[-1].text.split("#token=")[1].split()[0]

    updated = client.patch(
        f"{STUDENTS}/{created['id']}", json={"email": "renamed@example.com"}, headers=headers
    )

    assert updated.status_code == 200
    assert updated.json()["email"] == "renamed@example.com"
    assert client.post(
        "/api/v1/auth/password/verify-link", json={"token": link_token}
    ).status_code == 400
    assert session.scalar(select(PasswordToken.revoked_at)) is not None


def test_deactivate_blocks_sign_in_and_reactivate_restores_it(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    student = create_student(session, passwords, email="ayesha@example.com")
    credentials = {"email": "ayesha@example.com", "password": STUDENT_PASSWORD}
    assert client.post("/api/v1/auth/student/login", json=credentials).status_code == 200

    deactivated = client.post(f"{STUDENTS}/{student.id}/deactivate", headers=headers)
    assert deactivated.status_code == 200
    assert deactivated.json()["account_status"] == "inactive"
    assert client.post("/api/v1/auth/student/login", json=credentials).status_code == 401

    reactivated = client.post(f"{STUDENTS}/{student.id}/reactivate", headers=headers)
    assert reactivated.json()["account_status"] == "active"
    assert client.post("/api/v1/auth/student/login", json=credentials).status_code == 200


def test_delete_needs_the_registration_number(client, session, passwords):
    headers = admin_headers(client, session, passwords)
    student = create_student(session, passwords)

    wrong = client.delete(f"{STUDENTS}/{student.id}", params={"confirm": "nope"}, headers=headers)
    assert wrong.status_code == 422
    assert wrong.json()["error"]["code"] == "CONFIRMATION_MISMATCH"

    right = client.delete(
        f"{STUDENTS}/{student.id}", params={"confirm": "2024-cs-0001"}, headers=headers
    )
    assert right.status_code == 204
    assert client.get(f"{STUDENTS}/{student.id}", headers=headers).status_code == 404


def test_resend_setup_email_only_for_invited_active_students(client, session, passwords, emails):
    headers = admin_headers(client, session, passwords)
    invited = create_student(session, passwords, 1, password=None)
    settled = create_student(session, passwords, 2)

    resent = client.post(f"{STUDENTS}/{invited.id}/setup-email", headers=headers)
    assert resent.status_code == 200
    assert resent.json()["latest_link"]["purpose"] == "setup"
    assert emails[-1].to == invited.email

    already = client.post(f"{STUDENTS}/{settled.id}/setup-email", headers=headers)
    assert already.status_code == 409
    assert already.json()["error"]["code"] == "PASSWORD_ALREADY_SET"

    client.post(f"{STUDENTS}/{invited.id}/deactivate", headers=headers)
    inactive = client.post(f"{STUDENTS}/{invited.id}/setup-email", headers=headers)
    assert inactive.status_code == 409
    assert inactive.json()["error"]["code"] == "STUDENT_INACTIVE"


def test_student_routes_need_an_admin_token(client):
    assert client.get(STUDENTS).status_code == 401
    assert client.post(STUDENTS, json=PAYLOAD).status_code == 401
