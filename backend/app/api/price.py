"""``POST /api/price``: pricing across three models.

Strict Pydantic validation per ``docs/security/threat-model.md`` T4 and T9:
no extra fields, no infinity or NaN, mathematical bounds enforced before the
pricing module is called.

The ``model`` field selects which pricer computes the call and put values:
``black_scholes`` (closed form), ``binomial`` (Cox Ross Rubinstein tree), or
``monte_carlo`` (geometric Brownian motion with antithetic variates). The
Greeks always come from the analytical Black Scholes formula; this matches
market convention where dealers quote Greeks from the closed form regardless
of their internal pricing model. See ``docs/risk/conventions.md``.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.pricing.binomial import binomial_call, binomial_put
from app.pricing.black_scholes import Greeks as MathGreeks
from app.pricing.black_scholes import (
    black_scholes_call,
    black_scholes_call_greeks,
    black_scholes_put,
    black_scholes_put_greeks,
)
from app.pricing.monte_carlo import monte_carlo_call, monte_carlo_put

router = APIRouter(prefix="/api", tags=["pricing"])

PricingModel = Literal["black_scholes", "binomial", "monte_carlo"]

# Determinism: a fixed seed makes the Monte Carlo branch deterministic for
# the same request payload. This lets the frontend show stable results
# under typing churn and lets the test suite pin exact values.
_MC_SEED = 4242
_MC_PATHS = 100_000
_BINOMIAL_STEPS = 500


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
    model: PricingModel = Field(
        default="black_scholes",
        description="Pricing model: black_scholes, binomial, or monte_carlo.",
    )


class GreeksDisplay(BaseModel):
    """Greeks scaled for display friendly units.

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
    model: PricingModel
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


def _price_call_put(
    model: PricingModel,
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> tuple[float, float]:
    if model == "black_scholes":
        return black_scholes_call(S, K, T, r, sigma), black_scholes_put(S, K, T, r, sigma)
    if model == "binomial":
        return (
            binomial_call(S, K, T, r, sigma, steps=_BINOMIAL_STEPS),
            binomial_put(S, K, T, r, sigma, steps=_BINOMIAL_STEPS),
        )
    return (
        monte_carlo_call(S, K, T, r, sigma, paths=_MC_PATHS, seed=_MC_SEED),
        monte_carlo_put(S, K, T, r, sigma, paths=_MC_PATHS, seed=_MC_SEED),
    )


@router.post("/price", response_model=PriceResponse)
def price(payload: PriceRequest) -> PriceResponse:
    call, put = _price_call_put(
        payload.model, payload.S, payload.K, payload.T, payload.r, payload.sigma
    )
    call_g = black_scholes_call_greeks(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    put_g = black_scholes_put_greeks(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    return PriceResponse(
        call=call,
        put=put,
        model=payload.model,
        call_greeks=_to_display(call_g),
        put_greeks=_to_display(put_g),
    )
