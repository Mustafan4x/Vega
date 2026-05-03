"""Environment dependent behavior.

In production the OpenAPI docs and schema are not served; in development
they are. This test suite exercises both modes by toggling
``TRADER_ENVIRONMENT`` before building the app.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def production_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("TRADER_ENVIRONMENT", "production")

    from app.main import build_app

    app = build_app()
    with TestClient(app) as c:
        yield c


def test_production_hides_openapi_schema(production_client: TestClient) -> None:
    response = production_client.get("/openapi.json")

    assert response.status_code == 404


def test_production_hides_swagger_docs(production_client: TestClient) -> None:
    response = production_client.get("/docs")

    assert response.status_code == 404


def test_production_still_serves_health(production_client: TestClient) -> None:
    response = production_client.get("/health")

    assert response.status_code == 200


def test_development_serves_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "Trader Backend"


def test_development_serves_swagger_docs(client: TestClient) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()
