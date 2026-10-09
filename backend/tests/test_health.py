import subprocess
import sys

from fastapi.testclient import TestClient

from app.main import create_app

STARTUP_SCRIPT = (
    "from app.core.config import Settings;"
    "from app.main import create_app;"
    "create_app(Settings(APP_ENV='test', DATABASE_URL='{url}'))"
)


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


def test_the_app_starts_in_a_fresh_process(settings):
    result = subprocess.run(
        [sys.executable, "-c", STARTUP_SCRIPT.format(url=settings.DATABASE_URL)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
