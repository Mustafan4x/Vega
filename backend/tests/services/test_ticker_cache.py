"""Unit tests for the in-process ticker cache.

The cache is a small TTL+LRU layer wrapping any ``TickerLookup`` so a
burst of identical autocomplete queries does not become a burst of
outbound yfinance calls. Threat model T6 (cache server side to limit
egress and absorb upstream rate limits).
"""

from __future__ import annotations

import pytest

from app.services.tickers import (
    CachedTickerLookup,
    TickerLookup,
    TickerNotFound,
    TickerQuote,
)


class FakeClock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class FakeLookup:
    def __init__(self, quote: TickerQuote | None = None, raise_not_found: bool = False) -> None:
        self.quote = quote
        self.raise_not_found = raise_not_found
        self.calls = 0

    def lookup(self, symbol: str) -> TickerQuote:
        self.calls += 1
        if self.raise_not_found:
            raise TickerNotFound(symbol)
        assert self.quote is not None
        return TickerQuote(
            symbol=symbol,
            name=self.quote.name,
            price=self.quote.price,
            currency=self.quote.currency,
        )


def _make(
    delegate: TickerLookup,
    *,
    ttl_seconds: float = 60.0,
    max_entries: int = 256,
    clock: FakeClock | None = None,
) -> CachedTickerLookup:
    return CachedTickerLookup(
        delegate, ttl_seconds=ttl_seconds, max_entries=max_entries, clock=clock or FakeClock()
    )


def _quote(price: float = 199.5) -> TickerQuote:
    return TickerQuote(symbol="AAPL", name="Apple Inc.", price=price, currency="USD")


def test_first_call_delegates_and_returns_quote() -> None:
    delegate = FakeLookup(quote=_quote())
    cache = _make(delegate)

    out = cache.lookup("AAPL")

    assert out.symbol == "AAPL"
    assert out.price == 199.5
    assert delegate.calls == 1


def test_second_call_within_ttl_serves_from_cache() -> None:
    delegate = FakeLookup(quote=_quote())
    clock = FakeClock()
    cache = _make(delegate, ttl_seconds=60, clock=clock)

    cache.lookup("AAPL")
    clock.advance(30.0)
    cache.lookup("AAPL")

    assert delegate.calls == 1


def test_call_after_ttl_refreshes() -> None:
    delegate = FakeLookup(quote=_quote())
    clock = FakeClock()
    cache = _make(delegate, ttl_seconds=60, clock=clock)

    cache.lookup("AAPL")
    clock.advance(60.001)
    cache.lookup("AAPL")

    assert delegate.calls == 2


def test_different_symbols_are_cached_independently() -> None:
    delegate = FakeLookup(quote=_quote())
    cache = _make(delegate)

    cache.lookup("AAPL")
    cache.lookup("MSFT")
    cache.lookup("AAPL")

    assert delegate.calls == 2


def test_not_found_is_not_cached() -> None:
    delegate = FakeLookup(raise_not_found=True)
    cache = _make(delegate)

    with pytest.raises(TickerNotFound):
        cache.lookup("ZZZZ")
    with pytest.raises(TickerNotFound):
        cache.lookup("ZZZZ")

    assert delegate.calls == 2


def test_lru_eviction_drops_least_recent() -> None:
    delegate = FakeLookup(quote=_quote())
    cache = _make(delegate, max_entries=2)

    cache.lookup("AAPL")
    cache.lookup("MSFT")
    cache.lookup("GOOG")
    cache.lookup("AAPL")

    assert delegate.calls == 4
