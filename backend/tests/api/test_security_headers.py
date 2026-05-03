"""Tests for HTTP security headers and CORS posture.

References: ``docs/security/threat-model.md`` T13 (security headers / TLS posture)
and T5 (CSRF / CORS allow list).
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def _ci_get(headers: object, name: str) -> str | None:
    for k, v in dict(headers).items():
        if k.lower() == name.lower():
            return v
    return None


def test_response_has_hsts_header(client: TestClient) -> None:
    response = client.get("/health")

    hsts = _ci_get(response.headers, "strict-transport-security")
    assert hsts is not None
    assert "max-age=" in hsts
    assert "includesubdomains" in hsts.lower()


def test_response_has_no_sniff_header(client: TestClient) -> None:
    response = client.get("/health")

    assert _ci_get(response.headers, "x-content-type-options") == "nosniff"


def test_response_has_referrer_policy(client: TestClient) -> None:
    response = client.get("/health")

    assert _ci_get(response.headers, "referrer-policy") == "strict-origin-when-cross-origin"


def test_response_has_permissions_policy(client: TestClient) -> None:
    response = client.get("/health")

    pp = _ci_get(response.headers, "permissions-policy")
    assert pp is not None
    assert "camera=()" in pp
    assert "microphone=()" in pp
    assert "geolocation=()" in pp


def test_response_has_frame_ancestors_csp(client: TestClient) -> None:
    response = client.get("/health")

    csp = _ci_get(response.headers, "content-security-policy")
    assert csp is not None
    assert "frame-ancestors 'none'" in csp


def test_response_has_coop_corp(client: TestClient) -> None:
    response = client.get("/health")

    assert _ci_get(response.headers, "cross-origin-opener-policy") == "same-origin"
    assert _ci_get(response.headers, "cross-origin-resource-policy") == "same-site"


def test_cors_allows_frontend_dev_origin(client: TestClient) -> None:
    response = client.options(
        "/api/price",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code in (200, 204)
    assert _ci_get(response.headers, "access-control-allow-origin") == "http://localhost:5173"


def test_cors_blocks_unknown_origin(client: TestClient) -> None:
    response = client.options(
        "/api/price",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    allow = _ci_get(response.headers, "access-control-allow-origin")
    assert allow != "http://evil.example.com"
    assert allow != "*"


def test_cors_does_not_allow_credentials(client: TestClient) -> None:
    response = client.options(
        "/api/price",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    allow_creds = _ci_get(response.headers, "access-control-allow-credentials")
    assert allow_creds in (None, "false")


def test_no_server_header_leak(client: TestClient) -> None:
    response = client.get("/health")

    server = _ci_get(response.headers, "server")
    assert server is None or "uvicorn" not in server.lower()
