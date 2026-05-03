"""``POST /api/price``: Black Scholes call and put pricing.

Strict Pydantic validation per ``docs/security/threat-model.md`` T4 and T9:
no extra fields, no infinity or NaN, mathematical bounds enforced before the
pricing module is called.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.pricing.black_scholes import Greeks as MathGreeks
from app.pricing.black_scholes import (
    black_scholes_call,
    black_scholes_call_greeks,
    black_scholes_put,
    black_scholes_put_greeks,
)

router = APIRouter(prefix="/api", tags=["pricing"])


class PriceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Sane upper bounds keep the math finite: math.exp blows up well before
    # the values below are reached, so an attacker cannot turn a public
    # endpoint into a guaranteed OverflowError. See threat model T12.
    S: float = Field(ge=0, le=1e9, allow_inf_nan=False, description="Current asset price.")
    K: float = Field(gt=0, le=1e9, allow_inf_nan=False, description="Strike price.")
    T: float = Field(ge=0, le=100, allow_inf_nan=False, description="Time to expiry in years.")
    r: float = Field(
        ge=-1.0, le=1.0, allow_inf_nan=False, description="Risk free rate (annualized, continuous)."
    )
    sigma: float = Field(ge=0, le=10, allow_inf_nan=False, description="Volatility (annualized).")


class GreeksDisplay(BaseModel):
    """Greeks scaled for trader friendly display.

    The math layer (`app.pricing.black_scholes.Greeks`) returns textbook
    units (per unit sigma, per unit r, per year). The API rescales:
    vega per 1 percent sigma, rho per 1 percent r, theta per calendar day.
    Delta and gamma stay in their natural units.
    """

    delta: float
    gamma: float
    theta_per_day: float
    vega_per_pct: float
    rho_per_pct: float


class PriceResponse(BaseModel):
    call: float
    put: float
    call_greeks: GreeksDisplay
    put_greeks: GreeksDisplay


def _to_display(g: MathGreeks) -> GreeksDisplay:
    return GreeksDisplay(
        delta=g.delta,
        gamma=g.gamma,
        theta_per_day=g.theta / 365.0,
        vega_per_pct=g.vega * 0.01,
        rho_per_pct=g.rho * 0.01,
    )


@router.post("/price", response_model=PriceResponse)
def price(payload: PriceRequest) -> PriceResponse:
    call = black_scholes_call(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    put = black_scholes_put(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    call_g = black_scholes_call_greeks(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    put_g = black_scholes_put_greeks(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    return PriceResponse(
        call=call,
        put=put,
        call_greeks=_to_display(call_g),
        put_greeks=_to_display(put_g),
    )
