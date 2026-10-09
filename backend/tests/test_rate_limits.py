import time

import pytest

from app.core.errors import RateLimited
from app.core.rate_limit import RateLimiter
from tests.factories import ADMIN_PASSWORD, STUDENT_PASSWORD, create_admin, create_student

LOGIN = "/api/v1/auth/student/login"
FORGOT = "/api/v1/auth/password/forgot"
ADMIN_ME = "/api/v1/admin/me"
ADMIN_PASSWORD_CHANGE = "/api/v1/admin/me/password"

GENEROUS = {
    "RATE_API_LIMIT": 1000,
    "RATE_LOGIN_LIMIT": 1000,
    "RATE_PASSWORD_LIMIT": 1000,
    "RATE_ADMIN_WRITE_LIMIT": 1000,
}


def limited(settings, **overrides):
    return settings.model_copy(update={**GENEROUS, **overrides})


def assert_rate_limited(response) -> None:
    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert body["error"]["message"] == "Too many requests. Try again later."
    retry_after = body["error"]["details"]["retry_after_seconds"]
    assert retry_after >= 1
    assert response.headers["Retry-After"] == str(retry_after)


def test_the_login_group_limits_sign_in_attempts(settings, build_client, session, passwords):
    create_student(session, passwords)
    client = build_client(limited(settings, RATE_LOGIN_LIMIT=2))
    body = {"email": "student1@example.com", "password": STUDENT_PASSWORD}

    assert client.post(LOGIN, json=body).status_code == 200
    assert client.post(LOGIN, json=body).status_code == 200

    assert_rate_limited(client.post(LOGIN, json=body))


def test_the_password_group_limits_link_requests(settings, build_client, session, passwords):
    create_student(session, passwords)
    client = build_client(limited(settings, RATE_PASSWORD_LIMIT=2))
    body = {"email": "student1@example.com"}

    assert client.post(FORGOT, json=body).status_code == 202
    assert client.post(FORGOT, json=body).status_code == 202

    assert_rate_limited(client.post(FORGOT, json=body))


def test_the_api_group_limits_every_versioned_request(settings, build_client):
    client = build_client(limited(settings, RATE_API_LIMIT=2))

    assert client.get(ADMIN_ME).status_code == 401
    assert client.get(ADMIN_ME).status_code == 401

    assert_rate_limited(client.get(ADMIN_ME))
    assert client.get("/health").status_code == 200


def test_the_admin_write_group_limits_writes_but_not_reads(
    settings, build_client, session, passwords
):
    create_admin(session, passwords)
    client = build_client(limited(settings, RATE_ADMIN_WRITE_LIMIT=2))
    token = client.post(
        "/api/v1/auth/admin/login",
        json={"email": "office@example.com", "password": ADMIN_PASSWORD},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    body = {"current_password": "the-wrong-password", "new_password": "a-long-new-password"}

    assert client.post(ADMIN_PASSWORD_CHANGE, headers=headers, json=body).status_code == 422
    assert client.post(ADMIN_PASSWORD_CHANGE, headers=headers, json=body).status_code == 422

    assert_rate_limited(client.post(ADMIN_PASSWORD_CHANGE, headers=headers, json=body))
    for _ in range(5):
        assert client.get(ADMIN_ME, headers=headers).status_code == 200


def test_the_next_window_allows_requests_again(settings, build_client, session, passwords):
    create_student(session, passwords)
    client = build_client(
        limited(settings, RATE_LOGIN_LIMIT=1, RATE_LOGIN_WINDOW_SECONDS=1)
    )
    body = {"email": "student1@example.com", "password": STUDENT_PASSWORD}
    assert client.post(LOGIN, json=body).status_code == 200
    assert client.post(LOGIN, json=body).status_code == 429

    time.sleep(1.1)

    assert client.post(LOGIN, json=body).status_code == 200


@pytest.mark.parametrize("group", ["login", "password", "requests", "admin_write", "api"])
def test_every_group_is_configured(settings, build_client, group):
    limiter = build_client(settings).app.state.rate_limiter

    limiter.check(group, "10.0.0.1")


def test_the_limiter_counts_each_client_separately():
    limiter = RateLimiter({"requests": (1, 3600)})

    limiter.check("requests", "10.0.0.1")
    limiter.check("requests", "10.0.0.2")

    with pytest.raises(RateLimited):
        limiter.check("requests", "10.0.0.1")


def test_the_limiter_prunes_finished_windows():
    limiter = RateLimiter({"requests": (1, 1)})
    limiter.check("requests", "10.0.0.1")

    time.sleep(1.1)
    limiter.check("requests", "10.0.0.1")

    assert len(limiter._counters) == 1
