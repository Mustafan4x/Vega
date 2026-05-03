"""Unit tests for the historical price lookup cache.

The cache mirrors ``CachedTickerLookup`` from Phase 8 but keys on
``(symbol, start, end)`` and uses a longer TTL because past prices
do not change. Same TTL+LRU semantics, same threat model T6
defence in depth (the symbol regex is enforced upstream and again
inside the adapter).
"""

from __future__ import annotations

from datetime import date

import pytest

from app.services.historical import (
    CachedHistoricalLookup,
    HistoricalLookup,
    HistoricalSeries,
    NotFoundError,
)


class FakeClock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


class FakeLookup:
    def __init__(
        self,
        series: HistoricalSeries | None = None,
        raise_not_found: bool = False,
    ) -> None:
        self.series = series
        self.raise_not_found = raise_not_found
        self.calls: list[tuple[str, date, date]] = []

    def fetch(self, symbol: str, start: date, end: date) -> HistoricalSeries:
        self.calls.append((symbol, start, end))
        if self.raise_not_found:
            raise NotFoundError(symbol)
        assert self.series is not None
        return self.series


def _series(symbol: str = "AAPL") -> HistoricalSeries:
    return HistoricalSeries(
        symbol=symbol,
        dates=("2026-01-02", "2026-01-03", "2026-01-06"),
        closes=(180.0, 181.5, 179.25),
    )


def _make(
    delegate: HistoricalLookup,
    *,
    ttl_seconds: float = 86_400.0,
    max_entries: int = 32,
    clock: FakeClock | None = None,
) -> CachedHistoricalLookup:
    return CachedHistoricalLookup(
        delegate,
        ttl_seconds=ttl_seconds,
        max_entries=max_entries,
        clock=clock or FakeClock(),
    )


def test_first_call_delegates_and_returns_series() -> None:
    delegate = FakeLookup(series=_series())
    cache = _make(delegate)

    out = cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))

    assert out.symbol == "AAPL"
    assert out.dates == ("2026-01-02", "2026-01-03", "2026-01-06")
    assert delegate.calls == [("AAPL", date(2026, 1, 2), date(2026, 1, 6))]


def test_second_call_within_ttl_serves_from_cache() -> None:
    delegate = FakeLookup(series=_series())
    clock = FakeClock()
    cache = _make(delegate, ttl_seconds=86_400.0, clock=clock)

    cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))
    clock.advance(1_000.0)
    cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))

    assert len(delegate.calls) == 1


def test_call_after_ttl_refreshes() -> None:
    delegate = FakeLookup(series=_series())
    clock = FakeClock()
    cache = _make(delegate, ttl_seconds=86_400.0, clock=clock)

    cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))
    clock.advance(86_400.001)
    cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))

    assert len(delegate.calls) == 2


def test_different_keys_are_cached_independently() -> None:
    delegate = FakeLookup(series=_series())
    cache = _make(delegate)

    cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))
    cache.fetch("AAPL", date(2026, 1, 3), date(2026, 1, 6))  # different start
    cache.fetch("MSFT", date(2026, 1, 2), date(2026, 1, 6))  # different symbol

    assert len(delegate.calls) == 3


def test_not_found_is_not_cached() -> None:
    delegate = FakeLookup(raise_not_found=True)
    cache = _make(delegate)

    with pytest.raises(NotFoundError):
        cache.fetch("ZZZZ", date(2026, 1, 2), date(2026, 1, 6))
    with pytest.raises(NotFoundError):
        cache.fetch("ZZZZ", date(2026, 1, 2), date(2026, 1, 6))

    assert len(delegate.calls) == 2


def test_lru_eviction_drops_least_recent() -> None:
    delegate = FakeLookup(series=_series())
    cache = _make(delegate, max_entries=2)

    cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))
    cache.fetch("MSFT", date(2026, 1, 2), date(2026, 1, 6))
    cache.fetch("GOOG", date(2026, 1, 2), date(2026, 1, 6))
    # AAPL should be evicted now.
    cache.fetch("AAPL", date(2026, 1, 2), date(2026, 1, 6))

    assert len(delegate.calls) == 4
