"""Contract tests for ``POST /api/backtest``.

The endpoint composes the historical price service (Phase 8 ticker
service style: SSRF guarded yfinance call with cache) with the pure
backtest engine (``app.backtest.engine``). Tests inject a fake
``HistoricalLookup`` so the suite never touches Yahoo.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.api.backtest import get_historical_lookup
from app.main import build_app
from app.services.historical import (
    HistoricalSeries,
    NotFoundError,
    UpstreamLookupError,
    UpstreamTimeoutError,
)


class StubHistorical:
    def __init__(
        self,
        *,
        series: HistoricalSeries | None = None,
        raises: Exception | None = None,
    ) -> None:
        self.series = series
        self.raises = raises
        self.calls: list[tuple[str, date, date]] = []

    def fetch(self, symbol: str, start: date, end: date) -> HistoricalSeries:
        self.calls.append((symbol, start, end))
        if self.raises is not None:
            raise self.raises
        assert self.series is not None
        return self.series


def _series(n_days: int = 30) -> HistoricalSeries:
    dates = tuple(date(2026, 1, 2 + i).isoformat() for i in range(n_days))
    closes = tuple(100.0 + i * 0.5 for i in range(n_days))
    return HistoricalSeries(symbol="AAPL", dates=dates, closes=closes)


VALID_PAYLOAD = {
    "symbol": "AAPL",
    "strategy": "long_call",
    "start_date": "2026-01-02",
    "end_date": "2026-02-15",
    "sigma": 0.20,
    "r": 0.05,
    "dte_days": 30,
}


@pytest.fixture
def stub() -> StubHistorical:
    return StubHistorical(series=_series())


@pytest.fixture
def stub_client(stub: StubHistorical) -> Iterator[TestClient]:
    app = build_app()
    app.dependency_overrides[get_historical_lookup] = lambda: stub
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_happy_path_returns_pnl_curve(stub_client: TestClient) -> None:
    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["strategy"] == "long_call"
    assert body["symbol"] == "AAPL"
    assert isinstance(body["dates"], list)
    assert len(body["dates"]) == 30
    assert len(body["spot"]) == 30
    assert len(body["position_value"]) == 30
    assert len(body["pnl"]) == 30
    assert body["strike"] == pytest.approx(100.0)
    assert body["entry_date"] == "2026-01-02"


def test_response_locks_down_extra_fields(stub_client: TestClient) -> None:
    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)

    body = response.json()
    expected = {
        "symbol",
        "strategy",
        "dates",
        "spot",
        "position_value",
        "pnl",
        "strike",
        "entry_basis",
        "entry_date",
        "expiry_date",
        "legs",
    }
    assert set(body.keys()) == expected


def test_legs_metadata_for_straddle(stub_client: TestClient) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={**VALID_PAYLOAD, "strategy": "straddle"},
    )

    body = response.json()
    legs = body["legs"]
    assert len(legs) == 2
    kinds = sorted(leg["kind"] for leg in legs)
    assert kinds == ["call", "put"]


def test_first_pnl_is_zero_at_entry(stub_client: TestClient) -> None:
    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)

    body = response.json()
    assert body["pnl"][0] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("strategy", ["long_call", "long_put", "straddle"])
def test_strategy_dispatches_correctly(stub_client: TestClient, strategy: str) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={**VALID_PAYLOAD, "strategy": strategy},
    )

    assert response.status_code == 200
    assert response.json()["strategy"] == strategy


def test_unknown_strategy_returns_422(stub_client: TestClient) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={**VALID_PAYLOAD, "strategy": "iron_condor"},
    )

    assert response.status_code == 422


def test_invalid_symbol_returns_422_without_calling_upstream(
    stub: StubHistorical, stub_client: TestClient
) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={**VALID_PAYLOAD, "symbol": "aapl!"},
    )

    assert response.status_code == 422
    assert stub.calls == []


def test_end_before_start_returns_422(stub_client: TestClient) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={**VALID_PAYLOAD, "start_date": "2026-02-15", "end_date": "2026-01-02"},
    )

    assert response.status_code == 422


def test_date_range_above_cap_returns_422(stub_client: TestClient) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={
            **VALID_PAYLOAD,
            "start_date": "2020-01-01",
            "end_date": "2026-12-31",
        },
    )

    assert response.status_code == 422


def test_dte_above_cap_returns_422(stub_client: TestClient) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={**VALID_PAYLOAD, "dte_days": 1000},
    )

    assert response.status_code == 422


def test_upstream_not_found_maps_to_404(stub: StubHistorical, stub_client: TestClient) -> None:
    stub.raises = NotFoundError("AAPL")
    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)

    assert response.status_code == 404
    assert response.json() == {"detail": "Ticker not found."}


def test_upstream_timeout_maps_to_504(stub: StubHistorical, stub_client: TestClient) -> None:
    stub.raises = UpstreamTimeoutError("AAPL")
    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)

    assert response.status_code == 504
    assert response.json() == {"detail": "Historical data lookup timed out."}


def test_upstream_error_maps_to_502(stub: StubHistorical, stub_client: TestClient) -> None:
    stub.raises = UpstreamLookupError("network blew up")
    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)

    assert response.status_code == 502
    assert response.json() == {"detail": "Historical data upstream unavailable."}


def test_does_not_echo_upstream_message(stub: StubHistorical, stub_client: TestClient) -> None:
    stub.raises = UpstreamLookupError("ConnectionError: HTTPSConnectionPool('finance.yahoo.com')")
    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)

    body = response.json()
    assert "yahoo" not in body["detail"].lower()
    assert "ConnectionError" not in body["detail"]


def test_too_few_prices_returns_422(stub_client: TestClient) -> None:
    # Stub returns a 1 day series; backtest needs at least 2 dates
    # for a meaningful curve.
    short = HistoricalSeries(symbol="AAPL", dates=("2026-01-02",), closes=(100.0,))
    stub_client.app.dependency_overrides[get_historical_lookup] = lambda: StubHistorical(
        series=short
    )

    response = stub_client.post("/api/backtest", json=VALID_PAYLOAD)
    assert response.status_code == 422


def test_rejects_extra_fields(stub_client: TestClient) -> None:
    response = stub_client.post(
        "/api/backtest",
        json={**VALID_PAYLOAD, "shenanigans": True},
    )

    assert response.status_code == 422
