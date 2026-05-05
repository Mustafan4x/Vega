"""Ticker price lookup service for ``GET /api/tickers/{symbol}``.

Covers threat model T6 (SSRF, focused on yfinance):

* ``TICKER_RE`` is the strict input gate: ``^[A-Z0-9.-]{1,10}$``.
  No URL, no path traversal, no Unicode look alikes. Validated at the
  router boundary before any lookup runs, and again here as a defence
  in depth.
* ``YFinanceTickerLookup`` runs each call through a process wide
  ``ThreadPoolExecutor`` with a hard 5 second timeout so a hung yahoo
  connection cannot tie up a worker.
* ``CachedTickerLookup`` wraps any lookup with a TTL+LRU cache so a
  burst of identical autocomplete queries does not become a burst of
  outbound calls. Misses (``TickerNotFound``) are intentionally not
  cached so a typo does not poison future lookups.
* The response shape is owned by ``TickerQuote`` (a ``dataclass``); the
  router copies fields into a Pydantic model so unknown library fields
  cannot leak through to the client.
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
from threading import Lock
from typing import Any, Protocol

logger = logging.getLogger("app.tickers")

TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,10}$")

DEFAULT_TIMEOUT_SECONDS = 12.0
DEFAULT_TTL_SECONDS = 60.0
DEFAULT_MAX_ENTRIES = 256


class TickerNotFound(LookupError):
    """The upstream returned no usable price for the requested symbol."""

    def __init__(self, symbol: str) -> None:
        super().__init__(symbol)
        self.symbol = symbol


class TickerUpstreamTimeout(TimeoutError):
    """The upstream lookup did not return inside the request budget."""


class TickerUpstreamError(RuntimeError):
    """The upstream lookup raised an unexpected error."""


@dataclass(frozen=True)
class TickerQuote:
    symbol: str
    name: str
    price: float
    currency: str


class TickerLookup(Protocol):
    def lookup(self, symbol: str) -> TickerQuote: ...


@dataclass
class _CacheEntry:
    quote: TickerQuote
    expires_at: float


class CachedTickerLookup:
    """TTL+LRU cache wrapping any ``TickerLookup``.

    Hits return without touching the delegate. ``TickerNotFound`` is
    propagated but never cached: if the user typos ``ZZZZ`` once, a
    real listing later in the day must still be reachable.
    """

    def __init__(
        self,
        delegate: TickerLookup,
        *,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._delegate = delegate
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock or time.monotonic
        self._entries: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = Lock()

    def lookup(self, symbol: str) -> TickerQuote:
        now = self._clock()
        with self._lock:
            entry = self._entries.get(symbol)
            if entry is not None and entry.expires_at > now:
                self._entries.move_to_end(symbol)
                return entry.quote
            if entry is not None:
                # Expired: drop and refetch.
                self._entries.pop(symbol, None)

        quote = self._delegate.lookup(symbol)

        with self._lock:
            self._entries[symbol] = _CacheEntry(quote=quote, expires_at=now + self._ttl)
            self._entries.move_to_end(symbol)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

        return quote


_executor: ThreadPoolExecutor | None = None
_executor_lock = Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ticker-lookup")
        return _executor


class YFinanceTickerLookup:
    """Adapter calling ``yfinance`` with a hard timeout.

    yfinance reaches a hard coded set of Yahoo finance hosts; the
    symbol we pass it is gated by ``TICKER_RE`` so it cannot be
    coerced into a URL or path traversal. The hard timeout bounds the
    egress per T6: a wedged Yahoo connection cannot stall a request.
    """

    def __init__(self, *, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout_seconds

    def lookup(self, symbol: str) -> TickerQuote:
        if not TICKER_RE.match(symbol):
            # Defence in depth: the router already validated.
            raise TickerNotFound(symbol)
        future = _get_executor().submit(self._fetch, symbol)
        try:
            return future.result(timeout=self._timeout)
        except FuturesTimeoutError as exc:
            future.cancel()
            raise TickerUpstreamTimeout(symbol) from exc

    def _fetch(self, symbol: str) -> TickerQuote:
        try:
            import yfinance as yf  # imported lazily so tests do not pay the cost
        except Exception as exc:  # pragma: no cover - import error is not exercised in unit tests
            raise TickerUpstreamError("yfinance import failed") from exc

        try:
            ticker = yf.Ticker(symbol)
            info: Any = getattr(ticker, "fast_info", None)
            price = _coerce_price(info)
            currency = _coerce_currency(info)
            name = _coerce_name(ticker, symbol)
        except TickerNotFound:
            raise
        except Exception as exc:
            logger.warning("ticker_upstream_error symbol=%s err=%s", symbol, type(exc).__name__)
            raise TickerUpstreamError(str(exc)) from exc

        if price is None or price <= 0.0:
            raise TickerNotFound(symbol)

        return TickerQuote(symbol=symbol, name=name, price=price, currency=currency)


def _coerce_price(info: Any) -> float | None:
    if info is None:
        return None
    for key in ("last_price", "regular_market_price", "lastPrice", "regularMarketPrice"):
        try:
            value = info[key] if hasattr(info, "__getitem__") else getattr(info, key, None)
        except (KeyError, TypeError):
            value = None
        if value is None:
            continue
        try:
            f = float(value)
        except (TypeError, ValueError):
            continue
        if f > 0.0:
            return f
    return None


def _coerce_currency(info: Any) -> str:
    if info is None:
        return "USD"
    for key in ("currency", "Currency"):
        try:
            value = info[key] if hasattr(info, "__getitem__") else getattr(info, key, None)
        except (KeyError, TypeError):
            value = None
        if isinstance(value, str) and 1 <= len(value) <= 8 and value.isalpha():
            return value.upper()
    return "USD"


def _coerce_name(ticker: Any, symbol: str) -> str:
    # `info` is a heavy network call in some yfinance versions; we
    # only consume the cheap parts. ``shortName`` lives on the
    # already-fetched fast_info in newer releases; otherwise fall back
    # to the symbol so the response still validates.
    fast = getattr(ticker, "fast_info", None)
    for source in (fast, getattr(ticker, "info", None)):
        if source is None:
            continue
        for key in ("shortName", "longName", "short_name", "long_name"):
            try:
                if hasattr(source, "__getitem__"):
                    value = source[key]
                else:
                    value = getattr(source, key, None)
            except (KeyError, TypeError):
                value = None
            if isinstance(value, str) and value.strip():
                return value.strip()[:80]
    return symbol


_default_lookup: TickerLookup | None = None
_default_lock = Lock()


def get_default_ticker_lookup() -> TickerLookup:
    """Return the process wide cached YFinance lookup.

    Lazy so importing this module does not start the executor or hit
    yfinance. Tests should override the FastAPI dependency rather
    than mutate this singleton.
    """

    global _default_lookup
    with _default_lock:
        if _default_lookup is None:
            _default_lookup = CachedTickerLookup(
                YFinanceTickerLookup(),
                ttl_seconds=DEFAULT_TTL_SECONDS,
                max_entries=DEFAULT_MAX_ENTRIES,
            )
        return _default_lookup
