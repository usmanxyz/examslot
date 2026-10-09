import re
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.models.password_token import PasswordToken
from tests.factories import STUDENT_PASSWORD, create_student

FORGOT = "/api/v1/auth/password/forgot"
VERIFY = "/api/v1/auth/password/verify-link"
SET = "/api/v1/auth/password/set"
LOGIN = "/api/v1/auth/student/login"

FORGOT_BODY = {
    "message": (
        "If that email belongs to a student account, a reset link is on its way."
        " It expires in 60 minutes."
    )
}
NEW_PASSWORD = "a-brand-new-long-password"
LINK_INVALID = {
    "error": {
        "code": "LINK_INVALID",
        "message": "This link is no longer valid. Request a new one from the sign-in page.",
        "details": {},
    }
}

TOKEN_PATTERN = re.compile(r"#token=([\w.-]+)")


def forgot(client, email: str = "student1@example.com", **extra):
    return client.post(FORGOT, json={"email": email, **extra})


def token_from(emails) -> str:
    return TOKEN_PATTERN.search(emails[-1].text).group(1)


def test_an_invited_student_gets_a_setup_link_and_can_set_a_password(
    client, session, passwords, emails
):
    student = create_student(session, passwords, password=None)

    assert forgot(client).status_code == 202
    assert emails[-1].subject == "Set your ExamSlot password"
    assert "#token=" in emails[-1].text
    assert "#token=" in emails[-1].html

    token = token_from(emails)
    verified = client.post(VERIFY, json={"token": token})
    assert verified.status_code == 200
    assert verified.json()["purpose"] == "setup"

    response = client.post(SET, json={"token": token, "password": NEW_PASSWORD})
    assert response.status_code == 200
    assert response.json() == {
        "message": "Your password is set. Sign in with your email and new password."
    }

    session.refresh(student)
    assert student.password_hash is not None
    assert student.password_set_at is not None
    assert student.token_version == 1
    assert client.post(
        LOGIN, json={"email": student.email, "password": NEW_PASSWORD}
    ).status_code == 200


def test_a_student_with_a_password_gets_a_reset_link(client, session, passwords, emails):
    create_student(session, passwords)

    assert forgot(client).status_code == 202

    assert emails[-1].subject == "Reset your ExamSlot password"
    assert client.post(VERIFY, json={"token": token_from(emails)}).json()["purpose"] == "reset"


def test_setting_a_password_clears_the_lock(client, session, passwords, emails):
    student = create_student(session, passwords)
    student.failed_login_count = 5
    student.locked_until = datetime.now(UTC) + timedelta(minutes=15)
    session.commit()
    forgot(client)

    assert client.post(
        SET, json={"token": token_from(emails), "password": NEW_PASSWORD}
    ).status_code == 200

    session.refresh(student)
    assert student.failed_login_count == 0
    assert student.locked_until is None


def test_a_link_works_only_once(client, session, passwords, emails):
    create_student(session, passwords, password=None)
    forgot(client)
    token = token_from(emails)
    client.post(SET, json={"token": token, "password": NEW_PASSWORD})

    response = client.post(SET, json={"token": token, "password": "another-long-password"})

    assert response.status_code == 400
    assert response.json() == LINK_INVALID
    assert client.post(VERIFY, json={"token": token}).status_code == 400


def test_an_expired_link_is_rejected(client, session, passwords, emails):
    create_student(session, passwords, password=None)
    forgot(client)
    token = token_from(emails)
    row = session.scalar(select(PasswordToken))
    row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()

    assert client.post(VERIFY, json={"token": token}).json() == LINK_INVALID
    assert client.post(SET, json={"token": token, "password": NEW_PASSWORD}).status_code == 400


def test_a_newer_link_revokes_the_older_one(client, session, passwords, emails):
    create_student(session, passwords, password=None)
    forgot(client)
    first = token_from(emails)
    forgot(client)
    second = token_from(emails)

    assert client.post(VERIFY, json={"token": first}).status_code == 400
    assert client.post(VERIFY, json={"token": second}).status_code == 200


def test_deactivating_the_student_invalidates_the_link(client, session, passwords, emails):
    student = create_student(session, passwords, password=None)
    forgot(client)
    token = token_from(emails)
    student.status = "inactive"
    session.commit()

    assert client.post(VERIFY, json={"token": token}).json() == LINK_INVALID


@pytest.mark.parametrize(
    "token",
    [
        "not-a-token",
        "no-dot-secret",
        f"{uuid.uuid4()}.",
        f"{uuid.uuid4()}.wrong-secret-value",
        "....",
        f"not-a-uuid.{'s' * 43}",
    ],
)
def test_malformed_and_unknown_tokens_are_rejected(client, session, passwords, token):
    create_student(session, passwords, password=None)

    assert client.post(VERIFY, json={"token": token}).json() == LINK_INVALID
    assert client.post(SET, json={"token": token, "password": NEW_PASSWORD}).status_code == 400


def test_a_wrong_secret_for_a_live_token_is_rejected(client, session, passwords, emails):
    create_student(session, passwords, password=None)
    forgot(client)
    token_id = token_from(emails).split(".", 1)[0]

    response = client.post(VERIFY, json={"token": f"{token_id}.{'x' * 43}"})

    assert response.json() == LINK_INVALID


@pytest.mark.parametrize("builder", ["unknown", "invited", "inactive", "active"])
def test_forgot_password_always_answers_the_same(client, session, passwords, builder):
    if builder == "invited":
        create_student(session, passwords, password=None)
    elif builder == "inactive":
        create_student(session, passwords, status="inactive")
    elif builder == "active":
        create_student(session, passwords)

    response = forgot(client)

    assert response.status_code == 202
    assert response.json() == FORGOT_BODY


def test_forgot_password_sends_nothing_for_unknown_or_inactive_accounts(
    client, session, passwords, emails
):
    create_student(session, passwords, status="inactive")

    forgot(client)
    forgot(client, email="nobody@example.com")

    assert emails == []


def test_a_filled_honeypot_sends_nothing(client, session, passwords, emails):
    create_student(session, passwords)

    assert forgot(client, website="spam").status_code == 202

    assert emails == []


def test_at_most_three_reset_emails_per_hour(client, session, passwords, emails):
    create_student(session, passwords)

    for _ in range(5):
        assert forgot(client).status_code == 202

    assert len(emails) == 3


def test_an_older_reset_does_not_count_against_the_hour(client, session, passwords, emails):
    create_student(session, passwords)
    for _ in range(3):
        forgot(client)
    session.execute(
        PasswordToken.__table__.update().values(created_at=datetime.now(UTC) - timedelta(hours=2))
    )
    session.commit()

    assert forgot(client).status_code == 202

    assert len(emails) == 4


def test_delivery_status_is_recorded(client, session, passwords, emails):
    create_student(session, passwords, password=None)

    forgot(client)

    assert session.scalar(select(PasswordToken.delivery_status)) == "sent"


def test_a_filled_honeypot_on_set_password_does_no_work(client, session, passwords, emails):
    student = create_student(session, passwords, password=None)
    forgot(client)

    response = client.post(
        SET, json={"token": token_from(emails), "password": NEW_PASSWORD, "website": "spam"}
    )

    assert response.status_code == 200
    session.refresh(student)
    assert student.password_hash is None


def test_set_password_applies_the_policy(client, session, passwords, emails):
    create_student(session, passwords, password=None)
    forgot(client)

    response = client.post(SET, json={"token": token_from(emails), "password": "student1x"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PASSWORD_TOO_WEAK"


def test_setting_a_password_ends_existing_sessions(client, session, passwords, emails):
    create_student(session, passwords)
    token = client.post(
        LOGIN, json={"email": "student1@example.com", "password": STUDENT_PASSWORD}
    ).json()["access_token"]
    forgot(client)

    client.post(SET, json={"token": token_from(emails), "password": NEW_PASSWORD})

    assert client.get(
        "/api/v1/student/me", headers={"Authorization": f"Bearer {token}"}
    ).status_code == 401
