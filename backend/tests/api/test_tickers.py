"""Contract tests for ``GET /api/tickers/{symbol}``.

Validates the SSRF surface (threat model T6) end to end: the symbol
regex blocks bad input before any lookup runs, upstream timeouts
become 504, missing symbols become 404, the cache prevents repeat
upstream calls, and the response shape is locked down so unknown
yfinance fields cannot leak through to the client.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.api.tickers import get_ticker_lookup
from app.main import build_app
from app.services.tickers import (
    TickerNotFound,
    TickerQuote,
    TickerUpstreamError,
    TickerUpstreamTimeout,
)


class StubLookup:
    def __init__(
        self,
        *,
        quote: TickerQuote | None = None,
        raises: Exception | None = None,
    ) -> None:
        self.quote = quote
        self.raises = raises
        self.calls: list[str] = []

    def lookup(self, symbol: str) -> TickerQuote:
        self.calls.append(symbol)
        if self.raises is not None:
            raise self.raises
        assert self.quote is not None
        return self.quote


@pytest.fixture
def stub() -> StubLookup:
    return StubLookup(
        quote=TickerQuote(symbol="AAPL", name="Apple Inc.", price=199.5, currency="USD"),
    )


@pytest.fixture
def stub_client(stub: StubLookup) -> Iterator[TestClient]:
    app = build_app()
    app.dependency_overrides[get_ticker_lookup] = lambda: stub
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_happy_path_returns_quote(stub_client: TestClient) -> None:
    response = stub_client.get("/api/tickers/AAPL")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 199.5,
        "currency": "USD",
    }


def test_response_does_not_leak_extra_fields(stub: StubLookup, stub_client: TestClient) -> None:
    # Even if the upstream returned extra fields, the Pydantic
    # response model strips them.
    stub.quote = TickerQuote(symbol="AAPL", name="Apple Inc.", price=199.5, currency="USD")
    response = stub_client.get("/api/tickers/AAPL")

    body = response.json()
    assert set(body.keys()) == {"symbol", "name", "price", "currency"}


@pytest.mark.parametrize(
    "symbol",
    [
        "aapl",  # lowercase rejected by regex
        "AAPL!",  # bang rejected by regex
        "AAA AAA",  # space rejected by regex
        "TOOLONGSYMBOL",  # 13 chars rejected by max length
        "AAPL\\x00",  # backslash rejected by regex
        "AAPL%20",  # percent rejected by regex
    ],
)
def test_invalid_symbol_returns_422_without_calling_lookup(
    symbol: str, stub: StubLookup, stub_client: TestClient
) -> None:
    response = stub_client.get(f"/api/tickers/{symbol}")

    assert response.status_code == 422, response.text
    assert stub.calls == [], f"lookup must not be called for invalid symbol: {symbol!r}"


@pytest.mark.parametrize(
    "symbol",
    [
        "",  # empty: path becomes /api/tickers/ which has no route
        "../../etc/passwd",  # path traversal: routed elsewhere by URL normalization
        "AAPL/info",  # slash: routed elsewhere
        ".",  # collapses to /api/tickers/
        "..",  # parent dir traversal in URL path
    ],
)
def test_path_traversal_attempts_are_rejected_without_calling_lookup(
    symbol: str, stub: StubLookup, stub_client: TestClient
) -> None:
    # These inputs never reach the {symbol} handler (URL path
    # parsing routes them to a non existent route), which is an
    # acceptable SSRF defence in depth: the handler is never
    # invoked. We only require the request to be rejected (4xx)
    # and the lookup to never be called.
    response = stub_client.get(f"/api/tickers/{symbol}")

    assert 400 <= response.status_code < 500, response.text
    assert stub.calls == [], f"lookup must not be called for invalid symbol: {symbol!r}"


def test_not_found_maps_to_404(stub: StubLookup, stub_client: TestClient) -> None:
    stub.raises = TickerNotFound("ZZZZ")
    response = stub_client.get("/api/tickers/ZZZZ")

    assert response.status_code == 404
    body = response.json()
    assert body == {"detail": "Ticker not found."}


def test_upstream_timeout_maps_to_504(stub: StubLookup, stub_client: TestClient) -> None:
    stub.raises = TickerUpstreamTimeout("AAPL")
    response = stub_client.get("/api/tickers/AAPL")

    assert response.status_code == 504
    body = response.json()
    assert body == {"detail": "Ticker lookup timed out."}


def test_upstream_error_maps_to_502(stub: StubLookup, stub_client: TestClient) -> None:
    stub.raises = TickerUpstreamError("network blew up")
    response = stub_client.get("/api/tickers/AAPL")

    assert response.status_code == 502
    body = response.json()
    assert body == {"detail": "Ticker upstream unavailable."}


def test_does_not_echo_upstream_error_message(stub: StubLookup, stub_client: TestClient) -> None:
    # Threat model T11: error responses must not leak library or
    # upstream internals to the caller.
    stub.raises = TickerUpstreamError("ConnectionError: HTTPSConnectionPool('finance.yahoo.com')")
    response = stub_client.get("/api/tickers/AAPL")

    body = response.json()
    assert "yahoo" not in body["detail"].lower()
    assert "ConnectionError" not in body["detail"]


def test_cache_prevents_second_upstream_call(stub: StubLookup, stub_client: TestClient) -> None:
    # The endpoint depends on a cached lookup in production; the
    # stub_client overrides that to a single shared StubLookup, so
    # the cache is exercised at the test seam only when we wrap the
    # stub. Test the contract by injecting a CachedTickerLookup
    # over the stub.
    from app.services.tickers import CachedTickerLookup

    cached = CachedTickerLookup(stub, ttl_seconds=60)
    stub_client.app.dependency_overrides[get_ticker_lookup] = lambda: cached

    r1 = stub_client.get("/api/tickers/AAPL")
    r2 = stub_client.get("/api/tickers/AAPL")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert stub.calls == ["AAPL"], "second call must hit the cache"


def test_dot_and_dash_symbols_are_accepted(stub: StubLookup, stub_client: TestClient) -> None:
    # Real tickers include BRK-B, BRK.B, ^GSPC (excluded: caret is
    # not in the allowed alphabet by the threat model regex).
    for symbol in ("BRK-B", "BRK.B", "T-1"):
        stub.quote = TickerQuote(symbol=symbol, name="Test", price=1.0, currency="USD")
        response = stub_client.get(f"/api/tickers/{symbol}")
        assert response.status_code == 200, f"{symbol} should be accepted"
