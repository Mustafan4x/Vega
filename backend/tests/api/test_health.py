"""Liveness endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_response_has_request_id_header(client: TestClient) -> None:
    response = client.get("/health")

    assert "x-request-id" in {k.lower() for k in response.headers}
    assert len(response.headers["x-request-id"]) >= 8
