import pytest

EXPECTED_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


@pytest.mark.parametrize("path", ["/health", "/api/v1/admin/me", "/api/v1/does-not-exist"])
def test_every_response_carries_the_security_headers(client, path):
    response = client.get(path)

    for name, value in EXPECTED_HEADERS.items():
        assert response.headers[name] == value


def test_api_responses_are_never_cached(client):
    assert client.get("/api/v1/admin/me").headers["Cache-Control"] == "no-store"


def test_hsts_is_absent_outside_production(client):
    assert "Strict-Transport-Security" not in client.get("/health").headers


def test_hsts_is_present_in_production(production_settings, build_client):
    client = build_client(production_settings)

    response = client.get("/health")

    assert response.headers["Strict-Transport-Security"] == "max-age=63072000; includeSubDomains"
    for name, value in EXPECTED_HEADERS.items():
        assert response.headers[name] == value


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_routes_are_absent_in_production(production_settings, build_client, path):
    assert build_client(production_settings).get(path).status_code == 404


@pytest.mark.parametrize("path", ["/docs", "/openapi.json"])
def test_docs_routes_keep_their_own_policy_in_development(client, path):
    response = client.get(path)

    assert response.status_code == 200
    assert "Content-Security-Policy" not in response.headers


def test_cors_allows_the_frontend_origin(client, settings):
    response = client.options(
        "/api/v1/auth/student/login",
        headers={
            "Origin": settings.FRONTEND_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == settings.FRONTEND_ORIGIN
    assert "Access-Control-Allow-Credentials" not in response.headers
    assert response.headers["Access-Control-Max-Age"] == "600"


def test_cors_rejects_another_origin(client):
    response = client.options(
        "/api/v1/auth/student/login",
        headers={
            "Origin": "https://attacker.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_exposes_the_headers_the_frontend_reads(client, settings):
    response = client.get("/api/v1/admin/me", headers={"Origin": settings.FRONTEND_ORIGIN})

    exposed = response.headers["Access-Control-Expose-Headers"]
    assert "X-Request-ID" in exposed
    assert "Retry-After" in exposed
    assert "Content-Disposition" in exposed
