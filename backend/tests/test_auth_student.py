from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.student import Student
from tests.factories import STUDENT_PASSWORD, create_student

LOGIN = "/api/v1/auth/student/login"
LOGOUT = "/api/v1/auth/student/logout"
ME = "/api/v1/student/me"
CHANGE_PASSWORD = "/api/v1/student/me/password"

CREDENTIALS_ERROR = {
    "error": {"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect.", "details": {}}
}


def sign_in(client, email: str = "student1@example.com", password: str = STUDENT_PASSWORD, **extra):
    return client.post(LOGIN, json={"email": email, "password": password, **extra})


def test_sign_in_returns_a_token_and_the_student(client, session, passwords):
    student = create_student(session, passwords)

    response = sign_in(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 3600
    assert body["student"] == {
        "id": str(student.id),
        "full_name": "Ayesha Siddiqui",
        "progress": "assignment_incomplete",
    }
    assert client.get(ME, headers=_bearer(body)).status_code == 200


def test_sign_in_sets_last_login_at(client, session, passwords):
    student = create_student(session, passwords)

    assert sign_in(client).status_code == 200

    session.refresh(student)
    assert student.last_login_at is not None


@pytest.mark.parametrize(
    ("email", "password", "extra", "builder"),
    [
        ("nobody@example.com", STUDENT_PASSWORD, {}, "none"),
        ("student1@example.com", "the-wrong-password", {}, "active"),
        ("student1@example.com", STUDENT_PASSWORD, {}, "invited"),
        ("student1@example.com", STUDENT_PASSWORD, {}, "inactive"),
        ("student1@example.com", STUDENT_PASSWORD, {}, "locked"),
        ("student1@example.com", STUDENT_PASSWORD, {"website": "spam"}, "active"),
    ],
)
def test_every_sign_in_failure_looks_the_same(
    client, session, passwords, email, password, extra, builder
):
    if builder == "active":
        create_student(session, passwords)
    elif builder == "invited":
        create_student(session, passwords, password=None)
    elif builder == "inactive":
        create_student(session, passwords, status="inactive")
    elif builder == "locked":
        student = create_student(session, passwords)
        student.locked_until = datetime.now(UTC) + timedelta(minutes=15)
        session.commit()

    response = client.post(LOGIN, json={"email": email, "password": password, **extra})

    assert response.status_code == 401
    assert response.json() == CREDENTIALS_ERROR


def test_a_filled_honeypot_does_no_work(client, session, passwords):
    student = create_student(session, passwords)

    assert sign_in(client, website="spam").status_code == 401

    session.refresh(student)
    assert student.failed_login_count == 0
    assert student.last_login_at is None


def test_the_account_locks_after_five_failures(client, session, passwords):
    student = create_student(session, passwords)

    for _ in range(5):
        assert sign_in(client, password="the-wrong-password").status_code == 401

    session.refresh(student)
    assert student.failed_login_count == 5
    assert student.locked_until is not None
    assert sign_in(client).status_code == 401


def test_the_lock_releases_when_the_window_ends(client, session, passwords):
    student = create_student(session, passwords)
    for _ in range(5):
        sign_in(client, password="the-wrong-password")
    session.refresh(student)
    student.locked_until = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()

    assert sign_in(client).status_code == 200

    session.refresh(student)
    assert student.failed_login_count == 0
    assert student.locked_until is None


def test_a_successful_sign_in_resets_the_counter(client, session, passwords):
    student = create_student(session, passwords)
    sign_in(client, password="the-wrong-password")

    assert sign_in(client).status_code == 200

    session.refresh(student)
    assert student.failed_login_count == 0


def test_logout_ends_every_session(client, session, passwords):
    create_student(session, passwords)
    first = _bearer(sign_in(client).json())
    second = _bearer(sign_in(client).json())

    assert client.post(LOGOUT, headers=first).status_code == 204

    assert client.get(ME, headers=first).status_code == 401
    assert client.get(ME, headers=second).status_code == 401


def test_changing_the_password_ends_other_sessions_and_returns_a_token(client, session, passwords):
    create_student(session, passwords)
    old = _bearer(sign_in(client).json())

    response = client.post(
        CHANGE_PASSWORD,
        headers=old,
        json={"current_password": STUDENT_PASSWORD, "new_password": "an-even-longer-password"},
    )

    assert response.status_code == 200
    fresh = _bearer(response.json())
    assert client.get(ME, headers=old).status_code == 401
    assert client.get(ME, headers=fresh).status_code == 200
    assert sign_in(client, password="an-even-longer-password").status_code == 200


def test_changing_the_password_rejects_a_wrong_current_password(client, session, passwords):
    create_student(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.post(
        CHANGE_PASSWORD,
        headers=headers,
        json={"current_password": "not-the-password", "new_password": "an-even-longer-password"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CURRENT_PASSWORD_INCORRECT"


@pytest.mark.parametrize("new_password", ["too-short", "student1-is-my-password"])
def test_changing_the_password_applies_the_policy(client, session, passwords, new_password):
    create_student(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.post(
        CHANGE_PASSWORD,
        headers=headers,
        json={"current_password": STUDENT_PASSWORD, "new_password": new_password},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PASSWORD_TOO_WEAK"


def test_changing_the_password_rejects_an_over_long_password(client, session, passwords):
    create_student(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.post(
        CHANGE_PASSWORD,
        headers=headers,
        json={"current_password": STUDENT_PASSWORD, "new_password": "a" * 129},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"]["fields"][0]["field"] == "new_password"


def test_a_student_token_is_rejected_on_admin_routes(client, session, passwords):
    create_student(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.get("/api/v1/admin/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_a_deactivated_student_token_is_rejected(client, session, passwords):
    student = create_student(session, passwords)
    headers = _bearer(sign_in(client).json())
    student.status = "inactive"
    session.commit()

    assert client.get(ME, headers=headers).status_code == 401


def test_sign_in_normalizes_the_email(client, session, passwords):
    create_student(session, passwords, email="ayesha@example.com")

    assert sign_in(client, email="  Ayesha@Example.COM  ").status_code == 200

    assert session.scalar(select(Student.email)) == "ayesha@example.com"


def _bearer(body: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {body['access_token']}"}
