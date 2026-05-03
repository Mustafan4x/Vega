"""Rate limiting tests.

Threat model T12: 60 req/min for cheap endpoints. We assert the limiter
returns 429 once the burst is exhausted within a small time window.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def low_limit_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Client with a deliberately tight rate limit so tests run in milliseconds."""

    monkeypatch.setenv("TRADER_RATE_LIMIT_DEFAULT", "5/minute")

    from app.main import build_app

    app = build_app()
    with TestClient(app) as c:
        yield c


def test_rate_limit_blocks_after_burst(low_limit_client: TestClient) -> None:
    payload = {"S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.2}

    statuses = [low_limit_client.post("/api/price", json=payload).status_code for _ in range(8)]

    assert statuses[:5] == [200, 200, 200, 200, 200]
    assert 429 in statuses[5:]


def test_rate_limit_response_429_is_json(low_limit_client: TestClient) -> None:
    payload = {"S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.2}

    last = None
    for _ in range(10):
        last = low_limit_client.post("/api/price", json=payload)

    assert last is not None
    assert last.status_code == 429
    body = last.json()
    assert "detail" in body or "error" in body
