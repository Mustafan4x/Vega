"""Environment dependent behavior.

In production the OpenAPI docs and schema are not served; in development
they are. The production env loader also fails loud on missing or
unsafe ``VEGA_CORS_ORIGINS``. This suite exercises both modes by
toggling ``VEGA_ENVIRONMENT`` (and the matching CORS env) before
building the app.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.config import ConfigError, load_settings


@pytest.fixture
def production_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("VEGA_ENVIRONMENT", "production")
    monkeypatch.setenv("VEGA_CORS_ORIGINS", "https://vega.pages.dev")

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
    assert body["info"]["title"] == "Vega Backend"


def test_development_serves_swagger_docs(client: TestClient) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "swagger" in response.text.lower() or "openapi" in response.text.lower()


def test_production_requires_cors_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEGA_ENVIRONMENT", "production")
    monkeypatch.delenv("VEGA_CORS_ORIGINS", raising=False)

    with pytest.raises(ConfigError, match="VEGA_CORS_ORIGINS"):
        load_settings()


def test_production_rejects_wildcard_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEGA_ENVIRONMENT", "production")
    monkeypatch.setenv("VEGA_CORS_ORIGINS", "*")

    with pytest.raises(ConfigError, match="not allowed in production"):
        load_settings()


def test_production_rejects_http_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEGA_ENVIRONMENT", "production")
    monkeypatch.setenv("VEGA_CORS_ORIGINS", "http://vega.example.com")

    with pytest.raises(ConfigError, match="https"):
        load_settings()


def test_production_accepts_multiple_https_origins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEGA_ENVIRONMENT", "production")
    monkeypatch.setenv(
        "VEGA_CORS_ORIGINS",
        "https://vega.pages.dev,https://vega.example.com",
    )

    settings = load_settings()
    assert settings.cors_origins == (
        "https://vega.pages.dev",
        "https://vega.example.com",
    )


def test_development_allows_localhost_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEGA_ENVIRONMENT", "development")
    monkeypatch.delenv("VEGA_CORS_ORIGINS", raising=False)

    settings = load_settings()
    # Development falls back to localhost. No fail loud in dev.
    assert settings.cors_origins == ("http://localhost:5173",)


def test_legacy_trader_env_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """The legacy ``TRADER_*`` fallback was removed after the project
    rename. Setting only ``TRADER_*`` in production must fail loud just
    like leaving the env unset."""

    monkeypatch.setenv("VEGA_ENVIRONMENT", "production")
    monkeypatch.delenv("VEGA_CORS_ORIGINS", raising=False)
    monkeypatch.setenv("TRADER_CORS_ORIGINS", "https://legacy.pages.dev")

    with pytest.raises(ConfigError, match="VEGA_CORS_ORIGINS"):
        load_settings()
