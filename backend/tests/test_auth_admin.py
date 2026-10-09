from datetime import UTC, datetime, timedelta

import pytest

from tests.factories import ADMIN_PASSWORD, create_admin, create_student

LOGIN = "/api/v1/auth/admin/login"
LOGOUT = "/api/v1/auth/admin/logout"
ME = "/api/v1/admin/me"
CHANGE_PASSWORD = "/api/v1/admin/me/password"

CREDENTIALS_ERROR = {
    "error": {"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect.", "details": {}}
}


def sign_in(client, email: str = "office@example.com", password: str = ADMIN_PASSWORD, **extra):
    return client.post(LOGIN, json={"email": email, "password": password, **extra})


def test_sign_in_returns_a_token_and_the_admin(client, session, passwords):
    admin = create_admin(session, passwords)

    response = sign_in(client)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    assert body["admin"] == {"id": str(admin.id), "full_name": "Exam Office"}


def test_me_returns_the_admin(client, session, passwords):
    admin = create_admin(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.get(ME, headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "id": str(admin.id),
        "full_name": "Exam Office",
        "email": "office@example.com",
    }


def test_sign_in_sets_last_login_at(client, session, passwords):
    admin = create_admin(session, passwords)

    assert sign_in(client).status_code == 200

    session.refresh(admin)
    assert admin.last_login_at is not None


@pytest.mark.parametrize(
    ("email", "password", "extra", "builder"),
    [
        ("nobody@example.com", ADMIN_PASSWORD, {}, "active"),
        ("office@example.com", "the-wrong-password", {}, "active"),
        ("office@example.com", ADMIN_PASSWORD, {}, "inactive"),
        ("office@example.com", ADMIN_PASSWORD, {}, "locked"),
        ("office@example.com", ADMIN_PASSWORD, {"website": "spam"}, "active"),
    ],
)
def test_every_sign_in_failure_looks_the_same(
    client, session, passwords, email, password, extra, builder
):
    if builder == "inactive":
        create_admin(session, passwords, is_active=False)
    elif builder == "locked":
        admin = create_admin(session, passwords)
        admin.locked_until = datetime.now(UTC) + timedelta(minutes=15)
        session.commit()
    else:
        create_admin(session, passwords)

    response = client.post(LOGIN, json={"email": email, "password": password, **extra})

    assert response.status_code == 401
    assert response.json() == CREDENTIALS_ERROR


def test_the_account_locks_after_five_failures(client, session, passwords):
    admin = create_admin(session, passwords)

    for _ in range(5):
        assert sign_in(client, password="the-wrong-password").status_code == 401

    session.refresh(admin)
    assert admin.locked_until is not None
    assert sign_in(client).status_code == 401


def test_the_lock_releases_when_the_window_ends(client, session, passwords):
    admin = create_admin(session, passwords)
    for _ in range(5):
        sign_in(client, password="the-wrong-password")
    session.refresh(admin)
    admin.locked_until = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()

    assert sign_in(client).status_code == 200

    session.refresh(admin)
    assert admin.failed_login_count == 0
    assert admin.locked_until is None


def test_logout_ends_every_session(client, session, passwords):
    create_admin(session, passwords)
    first = _bearer(sign_in(client).json())
    second = _bearer(sign_in(client).json())

    assert client.post(LOGOUT, headers=first).status_code == 204

    assert client.get(ME, headers=first).status_code == 401
    assert client.get(ME, headers=second).status_code == 401


def test_changing_the_password_ends_other_sessions_and_returns_a_token(client, session, passwords):
    create_admin(session, passwords)
    old = _bearer(sign_in(client).json())

    response = client.post(
        CHANGE_PASSWORD,
        headers=old,
        json={"current_password": ADMIN_PASSWORD, "new_password": "an-even-longer-password"},
    )

    assert response.status_code == 200
    fresh = _bearer(response.json())
    assert client.get(ME, headers=old).status_code == 401
    assert client.get(ME, headers=fresh).status_code == 200
    assert sign_in(client, password="an-even-longer-password").status_code == 200


def test_changing_the_password_rejects_a_wrong_current_password(client, session, passwords):
    create_admin(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.post(
        CHANGE_PASSWORD,
        headers=headers,
        json={"current_password": "not-the-password", "new_password": "an-even-longer-password"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "CURRENT_PASSWORD_INCORRECT"


@pytest.mark.parametrize("new_password", ["too-short", "office-is-my-password"])
def test_changing_the_password_applies_the_policy(client, session, passwords, new_password):
    create_admin(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.post(
        CHANGE_PASSWORD,
        headers=headers,
        json={"current_password": ADMIN_PASSWORD, "new_password": new_password},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "PASSWORD_TOO_WEAK"


def test_an_admin_token_is_rejected_on_student_routes(client, session, passwords):
    create_admin(session, passwords)
    create_student(session, passwords)
    headers = _bearer(sign_in(client).json())

    response = client.get("/api/v1/student/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_a_deactivated_admin_token_is_rejected(client, session, passwords):
    admin = create_admin(session, passwords)
    headers = _bearer(sign_in(client).json())
    admin.is_active = False
    session.commit()

    assert client.get(ME, headers=headers).status_code == 401


def test_a_missing_token_is_rejected(client):
    response = client.get(ME)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_a_malformed_token_is_rejected(client):
    assert client.get(ME, headers={"Authorization": "Bearer not-a-jwt"}).status_code == 401
    assert client.get(ME, headers={"Authorization": ADMIN_PASSWORD}).status_code == 401


def _bearer(body: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {body['access_token']}"}
