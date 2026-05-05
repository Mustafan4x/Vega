"""Pure backtest engine for vanilla European option strategies.

Given a daily close price series and a strategy spec, marks the
position to market every day at the close and produces a P&L curve
under the long holder convention from ``docs/risk/conventions.md``.

The engine does not talk to the network, the database, or the
clock. It is fully deterministic and unit testable on synthetic
series. The historical price service (``app.services.historical``)
provides the (date, close) pairs; the API layer
(``app.api.backtest``) wires the two together.

Strategy library for v1:

* ``LONG_CALL``: one long call at the money.
* ``LONG_PUT``: one long put at the money.
* ``STRADDLE``: one long call plus one long put at the money.

Each strategy enters on the first date in the series with the strike
set to the entry day's close. The expiry date is entry + dte_days
(calendar days). On every subsequent date until the earlier of the
last date in the series or the expiry, each leg is marked using the
analytical Black Scholes formula at ``T = max(expiry - day, 0) / 365``.
At expiry the option value collapses to the intrinsic payoff, which
is the standard textbook limit (sigma * sqrt(T) collapses to zero,
so the BS formula returns ``max(S - K, 0)`` for a call).

The P&L is `position_value - entry_basis`, where entry_basis is the
total premium paid on the entry day (positive for long legs).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum

from app.pricing.black_scholes import black_scholes_call, black_scholes_put

DAYS_PER_YEAR = 365.0
MAX_DATES = 1300  # five years of trading days plus a margin (matches the API date range cap)


class Strategy(StrEnum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    STRADDLE = "straddle"


@dataclass(frozen=True)
class Leg:
    """A single position leg within a strategy.

    ``sign``: +1 long, -1 short. v1 strategies only have long legs;
    short legs (covered call, cash secured put) are deferred.
    ``kind``: ``call`` or ``put``.
    """

    sign: int
    kind: str


STRATEGY_LEGS: dict[Strategy, tuple[Leg, ...]] = {
    Strategy.LONG_CALL: (Leg(sign=+1, kind="call"),),
    Strategy.LONG_PUT: (Leg(sign=+1, kind="put"),),
    Strategy.STRADDLE: (Leg(sign=+1, kind="call"), Leg(sign=+1, kind="put")),
}


@dataclass(frozen=True)
class BacktestRequest:
    strategy: Strategy
    dates: tuple[str, ...]
    closes: tuple[float, ...]
    sigma: float
    r: float
    dte_days: int
    q: float = 0.0


@dataclass(frozen=True)
class BacktestResult:
    strategy: Strategy
    legs: tuple[Leg, ...]
    dates: tuple[str, ...]
    spot: tuple[float, ...]
    position_value: tuple[float, ...]
    pnl: tuple[float, ...]
    strike: float
    entry_basis: float
    entry_date: str
    expiry_date: str


def _validate(req: BacktestRequest) -> None:
    if len(req.dates) == 0:
        raise ValueError("dates must not be empty.")
    if len(req.dates) != len(req.closes):
        raise ValueError("dates and closes must be the same length.")
    if len(req.dates) > MAX_DATES:
        raise ValueError(f"too many dates: {len(req.dates)} > {MAX_DATES}.")
    if req.sigma < 0:
        raise ValueError(f"sigma must be non negative, got sigma={req.sigma}.")
    if req.dte_days <= 0:
        raise ValueError(f"dte_days must be strictly positive, got {req.dte_days}.")
    for c in req.closes:
        if c <= 0 or not math.isfinite(c):
            raise ValueError(f"every close price must be positive and finite, got {c}.")
    if req.r < -1.0 or req.r > 1.0:
        raise ValueError(f"r out of supported range, got r={req.r}.")
    if not math.isfinite(req.q):
        raise ValueError(f"q must be finite, got q={req.q}.")
    if req.q < -1.0 or req.q > 1.0:
        raise ValueError(f"q out of supported range, got q={req.q}.")


def _leg_value(leg: Leg, S: float, K: float, T: float, r: float, sigma: float, q: float) -> float:
    if leg.kind == "call":
        v = black_scholes_call(S, K, T, r, sigma, q=q)
    elif leg.kind == "put":
        v = black_scholes_put(S, K, T, r, sigma, q=q)
    else:
        raise ValueError(f"unknown leg kind: {leg.kind!r}")
    return leg.sign * v


def run_backtest(req: BacktestRequest) -> BacktestResult:
    _validate(req)

    legs = STRATEGY_LEGS[req.strategy]
    entry_close = req.closes[0]
    entry_date = date.fromisoformat(req.dates[0])
    expiry_date = entry_date + timedelta(days=req.dte_days)
    K = entry_close

    # Entry basis is the total premium paid on entry. Time to expiry
    # at entry is exactly dte_days / 365.
    T_entry = req.dte_days / DAYS_PER_YEAR
    entry_basis = 0.0
    for leg in legs:
        entry_basis += _leg_value(leg, entry_close, K, T_entry, req.r, req.sigma, req.q)

    dates_out: list[str] = []
    spot_out: list[float] = []
    position_out: list[float] = []
    pnl_out: list[float] = []
    for date_iso, close in zip(req.dates, req.closes, strict=True):
        d = date.fromisoformat(date_iso)
        # Days remaining until expiry (calendar days). Once the date
        # is at or past expiry, T collapses to zero and the BS
        # formula returns the intrinsic payoff.
        days_remaining = (expiry_date - d).days
        T = max(days_remaining, 0) / DAYS_PER_YEAR
        position_value = 0.0
        for leg in legs:
            position_value += _leg_value(leg, close, K, T, req.r, req.sigma, req.q)
        dates_out.append(date_iso)
        spot_out.append(close)
        position_out.append(position_value)
        pnl_out.append(position_value - entry_basis)

    return BacktestResult(
        strategy=req.strategy,
        legs=legs,
        dates=tuple(dates_out),
        spot=tuple(spot_out),
        position_value=tuple(position_out),
        pnl=tuple(pnl_out),
        strike=K,
        entry_basis=entry_basis,
        entry_date=req.dates[0],
        expiry_date=expiry_date.isoformat(),
    )
