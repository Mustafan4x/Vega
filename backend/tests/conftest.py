"""Shared pytest fixtures for the FastAPI service.

Each test gets a fresh TestClient bound to a freshly built app, so middleware
state (rate limiter counters, request id counters) does not leak across tests.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import build_app

    app = build_app()
    with TestClient(app) as c:
        yield c
