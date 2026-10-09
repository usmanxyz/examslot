from fastapi.testclient import TestClient

from app.main import create_app
from tests.factories import create_student

SECRET_DETAIL = "database password is hunter2"


def test_an_unknown_path_uses_the_envelope(client):
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "We could not find that.", "details": {}}
    }


def test_a_wrong_method_uses_the_envelope(client):
    response = client.get("/api/v1/auth/student/login")

    assert response.status_code == 405
    assert response.json() == {
        "error": {
            "code": "METHOD_NOT_ALLOWED",
            "message": "This action is not supported here.",
            "details": {},
        }
    }


def test_a_validation_error_lists_fields(client):
    response = client.post("/api/v1/auth/student/login", json={"email": "not-an-email"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "Some fields need attention."
    fields = {item["field"] for item in error["details"]["fields"]}
    assert fields == {"email", "password"}


def test_unknown_fields_are_rejected(client):
    response = client.post(
        "/api/v1/auth/student/login",
        json={"email": "a@example.com", "password": "a-long-password", "status": "active"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["details"]["fields"][0]["field"] == "status"


def test_a_normalization_message_reaches_the_field_list(client, session, passwords):
    create_student(session, passwords)

    response = client.post("/api/v1/auth/password/forgot", json={"email": "no-at-sign"})

    assert response.status_code == 422
    assert "Value error," not in response.text


def test_an_unhandled_error_returns_the_generic_envelope(settings):
    app = create_app(settings)

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError(SECRET_DETAIL)

    with TestClient(app) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Something went wrong on our side. Try again in a moment.",
            "details": {},
        }
    }
    assert SECRET_DETAIL not in response.text
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_an_unreachable_database_returns_service_unavailable(settings):
    unreachable = settings.model_copy(
        update={"DATABASE_URL": settings.DATABASE_URL.replace("/examslot_test", "/examslot_absent")}
    )
    with TestClient(create_app(unreachable)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "error": {
            "code": "SERVICE_UNAVAILABLE",
            "message": "The service is temporarily unavailable. Try again in a moment.",
            "details": {},
        }
    }


def test_a_request_id_is_reused_when_it_is_a_uuid(client):
    given = "11111111-2222-4333-8444-555555555555"

    response = client.get("/health", headers={"X-Request-ID": given})

    assert response.headers["X-Request-ID"] == given


def test_a_bad_request_id_is_replaced(client):
    response = client.get("/health", headers={"X-Request-ID": "not-a-uuid"})

    assert response.headers["X-Request-ID"] != "not-a-uuid"


def test_an_over_long_body_is_rejected(client):
    response = client.post(
        "/api/v1/auth/student/login",
        content=b"x" * 1_048_577,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "PAYLOAD_TOO_LARGE"
