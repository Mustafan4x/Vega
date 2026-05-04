"""Contract tests for the JWT auth dependency."""

from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient


def test_require_user_accepts_valid_jwt(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/calculations", headers=auth_headers)
    assert response.status_code == 200, response.text


def test_require_user_rejects_missing_header(client: TestClient) -> None:
    response = client.get("/api/calculations")
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_require_user_rejects_malformed_header(client: TestClient) -> None:
    response = client.get("/api/calculations", headers={"Authorization": "Token abc"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_require_user_rejects_expired_jwt(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(exp_offset_seconds=-60)
    response = client.get("/api/calculations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_require_user_rejects_wrong_audience(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(aud="wrong-audience")
    response = client.get("/api/calculations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_require_user_rejects_wrong_issuer(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(iss="https://attacker.example.com/")
    response = client.get("/api/calculations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_require_user_rejects_unknown_kid(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(kid="not-a-real-kid")
    response = client.get("/api/calculations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_require_user_rejects_alg_none(client: TestClient) -> None:
    import base64
    import json as _json

    header = base64.urlsafe_b64encode(_json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(
        b"="
    )
    payload = base64.urlsafe_b64encode(
        _json.dumps(
            {
                "sub": "x",
                "aud": "vega-api",
                "iss": "https://vega-test.us.auth0.com/",
                "exp": 9999999999,
            }
        ).encode()
    ).rstrip(b"=")
    token = f"{header.decode()}.{payload.decode()}."

    response = client.get("/api/calculations", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_require_user_does_not_leak_error_detail(client: TestClient) -> None:
    response = client.get("/api/calculations", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401
    body = response.json()
    assert body == {"detail": "Authentication required."}
    assert "exp" not in str(body)
    assert "signature" not in str(body).lower()
