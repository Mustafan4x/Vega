"""``GET /api/tickers/{symbol}``: yfinance backed price lookup.

Threat model T6 (SSRF) controls live in two places:

* The symbol path parameter is gated by ``TICKER_RE`` here, so an
  invalid symbol returns 422 before any lookup runs. This blocks the
  obvious attacks (path traversal, URL injection, oversize input).
* The lookup itself enforces a hard timeout, never follows arbitrary
  redirects, and validates response shape via Pydantic. See
  ``app.services.tickers``.

Errors map to discrete HTTP statuses so the frontend can render a
useful message without seeing library internals: 404 for unknown
symbols, 504 for upstream timeouts, 502 for any other upstream error.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel, ConfigDict, Field
from starlette.requests import Request

from app.core.rate_limit import limiter
from app.services.tickers import (
    TICKER_RE,
    TickerLookup,
    TickerNotFound,
    TickerUpstreamError,
    TickerUpstreamTimeout,
    get_default_ticker_lookup,
)

router = APIRouter(prefix="/api", tags=["tickers"])

# Per route cap. Tighter than the default per IP cap because every cache
# miss issues an upstream yfinance call (T6). The 60 second TTL plus 256
# entry LRU absorb most repeats, but we cap the route directly to bound
# upstream load even on a cold cache.
TICKERS_RATE_LIMIT = "30/minute"


class TickerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=10)
    name: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0, allow_inf_nan=False)
    currency: str = Field(min_length=1, max_length=8)


def get_ticker_lookup() -> TickerLookup:
    return get_default_ticker_lookup()


@router.get(
    "/tickers/{symbol}",
    response_model=TickerResponse,
)
@limiter.limit(TICKERS_RATE_LIMIT)
def read_ticker(
    request: Request,
    symbol: str = Path(
        ...,
        pattern=TICKER_RE.pattern,
        min_length=1,
        max_length=10,
        description="Ticker symbol; alphanumeric plus dot and dash, max 10 characters.",
    ),
    lookup: TickerLookup = Depends(get_ticker_lookup),
) -> TickerResponse:
    try:
        quote = lookup.lookup(symbol)
    except TickerNotFound as exc:
        raise HTTPException(status_code=404, detail="Ticker not found.") from exc
    except TickerUpstreamTimeout as exc:
        raise HTTPException(status_code=504, detail="Ticker lookup timed out.") from exc
    except TickerUpstreamError as exc:
        raise HTTPException(status_code=502, detail="Ticker upstream unavailable.") from exc

    return TickerResponse(
        symbol=quote.symbol,
        name=quote.name,
        price=quote.price,
        currency=quote.currency,
    )
