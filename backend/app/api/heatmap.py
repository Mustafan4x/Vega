"""``POST /api/heatmap``: 2D grid of call and put values across volatility
and spot price shocks.

Strict Pydantic validation enforces the threat model T12 cap (21 by 21
cells), bounds on the shock ranges, and ``extra='forbid'``. The actual
math runs through one of three pricers based on the ``model`` field:

* ``black_scholes``: vectorized closed form (``black_scholes_vec``).
  ~1ms for the full 21x21 grid.
* ``binomial``: CRR tree, scalar per cell with reduced step count
  (``_HEATMAP_BINOMIAL_STEPS``). ~150ms for the full grid.
* ``monte_carlo``: GBM with antithetic variates, scalar per cell with
  reduced path count (``_HEATMAP_MC_PATHS``) and a deterministic seed
  per cell. ~250ms for the full grid.

The reduced step / path counts versus the price endpoint trade some
accuracy for responsiveness, since the heatmap is a visualization
(the user reads color, not the exact dollar) and the per cell budget
in a 21x21 grid is 50x tighter than the per request budget at
``/api/price``.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.requests import Request

from app.core.rate_limit import limiter
from app.pricing.binomial import binomial_call, binomial_put
from app.pricing.black_scholes_vec import black_scholes_call_vec, black_scholes_put_vec
from app.pricing.monte_carlo import monte_carlo_call, monte_carlo_put

router = APIRouter(prefix="/api", tags=["heatmap"])

MAX_DIMENSION = 21

# Per route cap. Tighter than the default per IP cap because the heat map
# does up to 441 cell prices on the binomial / Monte Carlo paths and is
# the most computationally expensive endpoint that does not hit yfinance.
HEATMAP_RATE_LIMIT = "12/minute"

PricingModel = Literal["black_scholes", "binomial", "monte_carlo"]

# Reduced parameters for the heatmap path. See module docstring.
_HEATMAP_BINOMIAL_STEPS = 100
_HEATMAP_MC_PATHS = 20_000
_HEATMAP_MC_SEED = 4242


class HeatmapRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Sane upper bounds keep the math finite. See threat model T12 and the
    # matching bounds on PriceRequest.
    S: float = Field(ge=0, le=1e9, allow_inf_nan=False, description="Base asset price.")
    K: float = Field(gt=0, le=1e9, allow_inf_nan=False, description="Strike price.")
    T: float = Field(ge=0, le=100, allow_inf_nan=False, description="Time to expiry in years.")
    r: float = Field(
        ge=-1.0, le=1.0, allow_inf_nan=False, description="Risk free rate (annualized, continuous)."
    )
    sigma: float = Field(
        ge=0, le=10, allow_inf_nan=False, description="Base volatility (annualized)."
    )
    q: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        allow_inf_nan=False,
        description="Continuous dividend yield (annualized, continuous).",
    )
    vol_shock: list[float] = Field(
        min_length=2, max_length=2, description="[min, max] vol shock as fraction of sigma."
    )
    spot_shock: list[float] = Field(
        min_length=2, max_length=2, description="[min, max] spot shock as fraction of S."
    )
    rows: int = Field(ge=1, le=MAX_DIMENSION, description="Number of vol axis points.")
    cols: int = Field(ge=1, le=MAX_DIMENSION, description="Number of spot axis points.")
    model: PricingModel = Field(
        default="black_scholes",
        description="Pricing model: black_scholes, binomial, or monte_carlo.",
    )

    @model_validator(mode="after")
    def _validate_shocks(self) -> HeatmapRequest:
        for label, pair in (("vol_shock", self.vol_shock), ("spot_shock", self.spot_shock)):
            for v in pair:
                if not _is_finite(v):
                    raise ValueError(f"{label} contains a non finite value.")
                if v < -0.95 or v > 1.0:
                    raise ValueError(f"{label} out of supported range [-0.95, 1.0].")
            if pair[0] > pair[1]:
                raise ValueError(f"{label} min must be less than or equal to max.")
        return self


class HeatmapResponse(BaseModel):
    call: list[list[float]]
    put: list[list[float]]
    model: PricingModel
    sigma_axis: list[float]
    spot_axis: list[float]


def _is_finite(x: float) -> bool:
    return x == x and x not in (float("inf"), float("-inf"))


def _grid_black_scholes(
    spot_axis: np.ndarray, sigma_axis: np.ndarray, K: float, T: float, r: float, q: float
) -> tuple[np.ndarray, np.ndarray]:
    call = black_scholes_call_vec(spot_axis, K, T, r, sigma_axis, q=q)
    put = black_scholes_put_vec(spot_axis, K, T, r, sigma_axis, q=q)
    return call, put


def _grid_binomial(
    spot_axis: np.ndarray, sigma_axis: np.ndarray, K: float, T: float, r: float, q: float
) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = sigma_axis.size, spot_axis.size
    call = np.zeros((rows, cols))
    put = np.zeros((rows, cols))
    for i in range(rows):
        for j in range(cols):
            call[i, j] = binomial_call(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                steps=_HEATMAP_BINOMIAL_STEPS,
            )
            put[i, j] = binomial_put(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                steps=_HEATMAP_BINOMIAL_STEPS,
            )
    return call, put


def _grid_monte_carlo(
    spot_axis: np.ndarray, sigma_axis: np.ndarray, K: float, T: float, r: float, q: float
) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = sigma_axis.size, spot_axis.size
    call = np.zeros((rows, cols))
    put = np.zeros((rows, cols))
    for i in range(rows):
        for j in range(cols):
            cell_seed = _HEATMAP_MC_SEED + i * MAX_DIMENSION + j
            call[i, j] = monte_carlo_call(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                paths=_HEATMAP_MC_PATHS,
                seed=cell_seed,
            )
            put[i, j] = monte_carlo_put(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                paths=_HEATMAP_MC_PATHS,
                seed=cell_seed,
            )
    return call, put


def _grid_for_model(
    model: PricingModel,
    spot_axis: np.ndarray,
    sigma_axis: np.ndarray,
    K: float,
    T: float,
    r: float,
    q: float,
) -> tuple[np.ndarray, np.ndarray]:
    if model == "black_scholes":
        return _grid_black_scholes(spot_axis, sigma_axis, K, T, r, q)
    if model == "binomial":
        return _grid_binomial(spot_axis, sigma_axis, K, T, r, q)
    return _grid_monte_carlo(spot_axis, sigma_axis, K, T, r, q)


@router.post("/heatmap", response_model=HeatmapResponse)
@limiter.limit(HEATMAP_RATE_LIMIT)
def heatmap(request: Request, payload: HeatmapRequest) -> HeatmapResponse:
    sigma_lo = payload.sigma * (1.0 + payload.vol_shock[0])
    sigma_hi = payload.sigma * (1.0 + payload.vol_shock[1])
    spot_lo = payload.S * (1.0 + payload.spot_shock[0])
    spot_hi = payload.S * (1.0 + payload.spot_shock[1])

    sigma_axis = (
        np.linspace(sigma_lo, sigma_hi, payload.rows)
        if payload.rows > 1
        else np.array([0.5 * (sigma_lo + sigma_hi)])
    )
    spot_axis = (
        np.linspace(spot_lo, spot_hi, payload.cols)
        if payload.cols > 1
        else np.array([0.5 * (spot_lo + spot_hi)])
    )

    sigma_axis = np.maximum(sigma_axis, 0.0)
    spot_axis = np.maximum(spot_axis, 0.0)

    call, put = _grid_for_model(
        payload.model, spot_axis, sigma_axis, payload.K, payload.T, payload.r, payload.q
    )

    return HeatmapResponse(
        call=call.tolist(),
        put=put.tolist(),
        model=payload.model,
        sigma_axis=sigma_axis.tolist(),
        spot_axis=spot_axis.tolist(),
    )
