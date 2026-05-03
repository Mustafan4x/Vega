"""``POST /api/backtest``: replay a strategy against historical prices.

Composes :mod:`app.services.historical` (yfinance with SSRF guards
and cache) with :mod:`app.backtest.engine` (the pure backtest
engine). This endpoint is the heaviest in the service: it makes one
upstream call to yfinance per uncached request, then runs the
engine in process. Both are bounded; the engine is microsecond
cheap and the upstream call is bounded by the historical service's
hard timeout.

Threat model T6 (SSRF): the symbol is gated by the same
``HISTORICAL_TICKER_RE`` as the ticker endpoint at the Pydantic
boundary. Errors map to discrete HTTP statuses without leaking
library internals (404 not found, 504 upstream timeout, 502 other
upstream, 422 input validation).
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.backtest.engine import (
    BacktestRequest as EngineRequest,
)
from app.backtest.engine import (
    Leg,
    Strategy,
    run_backtest,
)
from app.services.historical import (
    HISTORICAL_TICKER_RE,
    HistoricalLookup,
    NotFoundError,
    UpstreamLookupError,
    UpstreamTimeoutError,
    get_default_historical_lookup,
)

router = APIRouter(prefix="/api", tags=["backtest"])

MAX_DATE_RANGE_DAYS = 365 * 5


class BacktestPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(
        min_length=1,
        max_length=10,
        pattern=HISTORICAL_TICKER_RE.pattern,
        description="Ticker symbol; alphanumeric plus dot and dash, max 10 chars.",
    )
    strategy: Strategy = Field(description="Strategy: long_call, long_put, or straddle.")
    start_date: date
    end_date: date
    sigma: float = Field(
        gt=0,
        le=10,
        allow_inf_nan=False,
        description=(
            "Implied volatility the position was opened against, "
            "held constant for every daily mark of the trade."
        ),
    )
    r: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False, description="Risk free rate.")
    dte_days: int = Field(gt=0, le=365, description="Days to expiry from the entry date.")

    @model_validator(mode="after")
    def _validate_dates(self) -> BacktestPayload:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        delta = (self.end_date - self.start_date).days
        if delta > MAX_DATE_RANGE_DAYS:
            raise ValueError(
                f"date range too large: {delta} days exceeds the {MAX_DATE_RANGE_DAYS} day cap."
            )
        return self


class LegOut(BaseModel):
    sign: int
    kind: str


class BacktestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    strategy: Strategy
    dates: list[str]
    spot: list[float]
    position_value: list[float]
    pnl: list[float]
    strike: float
    entry_basis: float
    entry_date: str
    expiry_date: str
    legs: list[LegOut]


def get_historical_lookup() -> HistoricalLookup:
    return get_default_historical_lookup()


def _to_leg_out(leg: Leg) -> LegOut:
    return LegOut(sign=leg.sign, kind=leg.kind)


@router.post("/backtest", response_model=BacktestResponse)
def backtest(
    payload: BacktestPayload,
    lookup: HistoricalLookup = Depends(get_historical_lookup),
) -> BacktestResponse:
    try:
        series = lookup.fetch(payload.symbol, payload.start_date, payload.end_date)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail="Ticker not found.") from exc
    except UpstreamTimeoutError as exc:
        raise HTTPException(status_code=504, detail="Historical data lookup timed out.") from exc
    except UpstreamLookupError as exc:
        raise HTTPException(
            status_code=502, detail="Historical data upstream unavailable."
        ) from exc

    if len(series.dates) < 2:
        raise HTTPException(
            status_code=422,
            detail="Not enough price data for the requested range.",
        )

    try:
        result = run_backtest(
            EngineRequest(
                strategy=payload.strategy,
                dates=series.dates,
                closes=series.closes,
                sigma=payload.sigma,
                r=payload.r,
                dte_days=payload.dte_days,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return BacktestResponse(
        symbol=payload.symbol,
        strategy=result.strategy,
        dates=list(result.dates),
        spot=list(result.spot),
        position_value=list(result.position_value),
        pnl=list(result.pnl),
        strike=result.strike,
        entry_basis=result.entry_basis,
        entry_date=result.entry_date,
        expiry_date=result.expiry_date,
        legs=[_to_leg_out(leg) for leg in result.legs],
    )
