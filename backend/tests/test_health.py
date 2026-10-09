from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_returns_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_reports_the_database(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_ready_reports_an_unreachable_database(settings):
    unreachable = settings.model_copy(
        update={"DATABASE_URL": settings.DATABASE_URL.replace("/examslot_test", "/examslot_absent")}
    )
    with TestClient(create_app(unreachable)) as client:
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_docs_routes_are_absent_in_production():
    with TestClient(create_app(Settings(APP_ENV="production"))) as client:
        for path in ("/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == 404
