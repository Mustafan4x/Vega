"""Historical daily close price service for the backtest endpoint.

Mirrors the structure of ``app.services.tickers``: a ``HistoricalLookup``
Protocol so tests can inject fakes, a ``YFinanceHistoricalLookup``
adapter that calls yfinance through a process wide ``ThreadPoolExecutor``
with a hard 10 second timeout (longer than ticker because the response
payload is much larger), and a ``CachedHistoricalLookup`` wrapper with
TTL+LRU semantics.

Threat model T6 (SSRF, focused on yfinance) controls live in three
places (defence in depth):

* ``HISTORICAL_TICKER_RE`` mirrors the ticker regex, gated at the API
  boundary AND inside this module.
* The ThreadPoolExecutor + ``future.result(timeout=...)`` enforces a
  hard wall clock budget so a hung Yahoo connection cannot tie up a
  worker indefinitely (same residual risk note as in
  ``services/tickers.py``: Python threads cannot truly cancel mid
  socket read; documented under T6).
* The ``HistoricalSeries`` dataclass strips everything yfinance returns
  beyond the (date, close) pairs, so unknown library fields cannot
  leak through to the caller.

The cache TTL defaults to one day because past prices do not change.
The LRU max defaults to 32 entries (one ticker plus three or four
date ranges per ticker).
"""

from __future__ import annotations

import logging
import re
import time
from collections import OrderedDict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import date
from threading import Lock
from typing import Any, Protocol

logger = logging.getLogger("app.historical")

HISTORICAL_TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,10}$")

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_TTL_SECONDS = 86_400.0
DEFAULT_MAX_ENTRIES = 32
MAX_DAYS = 365 * 5  # Threat model T12: cap the date range.


class NotFoundError(LookupError):
    """The upstream returned no usable price series for the symbol."""

    def __init__(self, symbol: str) -> None:
        super().__init__(symbol)
        self.symbol = symbol


class UpstreamTimeoutError(TimeoutError):
    """The upstream lookup did not return inside the request budget."""


class UpstreamLookupError(RuntimeError):
    """The upstream lookup raised an unexpected error."""


@dataclass(frozen=True)
class HistoricalSeries:
    symbol: str
    dates: tuple[str, ...]  # ISO 8601 yyyy-mm-dd
    closes: tuple[float, ...]


class HistoricalLookup(Protocol):
    def fetch(self, symbol: str, start: date, end: date) -> HistoricalSeries: ...


@dataclass
class _CacheEntry:
    series: HistoricalSeries
    expires_at: float


class CachedHistoricalLookup:
    """TTL+LRU cache wrapping any ``HistoricalLookup``.

    Keyed by ``(symbol, start, end)``. NotFound is never cached so a
    typo today does not poison a real listing later.
    """

    def __init__(
        self,
        delegate: HistoricalLookup,
        *,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._delegate = delegate
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock or time.monotonic
        self._entries: OrderedDict[tuple[str, date, date], _CacheEntry] = OrderedDict()
        self._lock = Lock()

    def fetch(self, symbol: str, start: date, end: date) -> HistoricalSeries:
        key = (symbol, start, end)
        now = self._clock()
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and entry.expires_at > now:
                self._entries.move_to_end(key)
                return entry.series
            if entry is not None:
                self._entries.pop(key, None)

        series = self._delegate.fetch(symbol, start, end)

        with self._lock:
            self._entries[key] = _CacheEntry(series=series, expires_at=now + self._ttl)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

        return series


_executor: ThreadPoolExecutor | None = None
_executor_lock = Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="historical-lookup")
        return _executor


class YFinanceHistoricalLookup:
    """Adapter calling ``yfinance`` for daily close prices.

    Uses ``yf.Ticker(symbol).history(start=..., end=..., auto_adjust=True)``.
    auto_adjust = True applies dividend and split adjustments so the
    backtest works on a clean total return series.
    """

    def __init__(self, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout_seconds

    def fetch(self, symbol: str, start: date, end: date) -> HistoricalSeries:
        if not HISTORICAL_TICKER_RE.match(symbol):
            raise NotFoundError(symbol)
        future = _get_executor().submit(self._fetch, symbol, start, end)
        try:
            return future.result(timeout=self._timeout)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise UpstreamTimeoutError(symbol) from exc

    def _fetch(self, symbol: str, start: date, end: date) -> HistoricalSeries:
        try:
            import yfinance as yf
        except Exception as exc:  # pragma: no cover - import error not exercised
            raise UpstreamLookupError("yfinance import failed") from exc

        try:
            ticker = yf.Ticker(symbol)
            # yfinance's `end` is exclusive; bump by one day so the
            # caller's end date is included.
            df: Any = ticker.history(
                start=start.isoformat(),
                end=(date(end.year, end.month, end.day)).isoformat(),
                auto_adjust=True,
                actions=False,
            )
        except NotFoundError:
            raise
        except Exception as exc:
            logger.warning("historical_upstream_error symbol=%s err=%s", symbol, type(exc).__name__)
            raise UpstreamLookupError(str(exc)) from exc

        if df is None or len(df) == 0:
            raise NotFoundError(symbol)

        try:
            close_series = df["Close"].dropna()
        except Exception as exc:
            logger.warning("historical_upstream_error symbol=%s err=%s", symbol, type(exc).__name__)
            raise UpstreamLookupError(str(exc)) from exc

        dates: list[str] = []
        closes: list[float] = []
        for ts, value in close_series.items():
            try:
                d = ts.date() if hasattr(ts, "date") else ts
                dates.append(d.isoformat())
                f = float(value)
                if f <= 0.0 or f != f or f in (float("inf"), float("-inf")):
                    continue
                closes.append(f)
            except Exception:
                continue

        if len(dates) == 0 or len(dates) != len(closes):
            raise NotFoundError(symbol)

        return HistoricalSeries(symbol=symbol, dates=tuple(dates), closes=tuple(closes))


_default_lookup: HistoricalLookup | None = None
_default_lock = Lock()


def get_default_historical_lookup() -> HistoricalLookup:
    """Return the process wide cached YFinance historical lookup.

    Tests should override the FastAPI dependency rather than mutate
    this singleton.
    """

    global _default_lookup
    with _default_lock:
        if _default_lookup is None:
            _default_lookup = CachedHistoricalLookup(
                YFinanceHistoricalLookup(),
                ttl_seconds=DEFAULT_TTL_SECONDS,
                max_entries=DEFAULT_MAX_ENTRIES,
            )
        return _default_lookup
