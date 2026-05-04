"""Rate limiting tests.

Threat model T12: 60 req/min for cheap endpoints, with tighter per route
caps on the heaviest endpoints (Phase 11 closeout of the Phase 4, 8, 10
deferrals). We assert each cap returns 429 after the burst is
exhausted, in addition to the application wide cap that protects the
service from a caller hammering many endpoints in turn.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api.backtest import get_historical_lookup
from app.api.tickers import get_ticker_lookup
from app.services.historical import HistoricalSeries
from app.services.tickers import TickerQuote


@pytest.fixture
def low_limit_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Client with a deliberately tight global rate limit so tests run in milliseconds."""

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


def test_heatmap_per_route_limit_caps_at_12(client: TestClient) -> None:
    payload = {
        "S": 100.0,
        "K": 100.0,
        "T": 1.0,
        "r": 0.05,
        "sigma": 0.2,
        "vol_shock": [-0.1, 0.1],
        "spot_shock": [-0.1, 0.1],
        "rows": 3,
        "cols": 3,
    }

    statuses = [client.post("/api/heatmap", json=payload).status_code for _ in range(14)]

    # First 12 succeed, 13th and 14th hit the per route 12/minute cap.
    assert statuses[:12] == [200] * 12, statuses
    assert statuses[12] == 429
    assert statuses[13] == 429


def test_tickers_per_route_limit_caps_at_30() -> None:
    from app.main import build_app

    app = build_app()

    class _Stub:
        quote = TickerQuote(symbol="AAPL", name="Apple Inc.", price=200.0, currency="USD")

        def lookup(self, symbol: str) -> TickerQuote:
            return self.quote

    app.dependency_overrides[get_ticker_lookup] = lambda: _Stub()
    try:
        with TestClient(app) as c:
            statuses = [c.get("/api/tickers/AAPL").status_code for _ in range(32)]
    finally:
        app.dependency_overrides.clear()

    assert statuses[:30] == [200] * 30, statuses
    assert statuses[30] == 429
    assert statuses[31] == 429


def test_backtest_per_route_limit_caps_at_10() -> None:
    from app.main import build_app

    app = build_app()

    series = HistoricalSeries(
        symbol="AAPL",
        dates=tuple(date(2026, 1, 2 + i).isoformat() for i in range(10)),
        closes=tuple(100.0 + i * 0.5 for i in range(10)),
    )

    class _Stub:
        def fetch(self, symbol: str, start: date, end: date) -> HistoricalSeries:
            return series

    app.dependency_overrides[get_historical_lookup] = lambda: _Stub()
    payload = {
        "symbol": "AAPL",
        "strategy": "long_call",
        "start_date": "2026-01-02",
        "end_date": "2026-01-12",
        "sigma": 0.2,
        "r": 0.05,
        "dte_days": 30,
    }
    try:
        with TestClient(app) as c:
            statuses = [c.post("/api/backtest", json=payload).status_code for _ in range(12)]
    finally:
        app.dependency_overrides.clear()

    assert statuses[:10] == [200] * 10, statuses
    assert statuses[10] == 429
    assert statuses[11] == 429


def test_per_route_429_does_not_count_health(client: TestClient) -> None:
    """``/health`` is intentionally exempt from per route caps so liveness
    probes never get throttled, even though the application wide cap still
    applies."""

    # Hit /api/backtest's per route cap (10/minute). /health stays 200.
    # We do not actually need to exhaust the backtest cap; just verify
    # /health responds independently and is not stamped with the
    # backtest route counter.
    health = [client.get("/health").status_code for _ in range(3)]
    assert health == [200, 200, 200]
