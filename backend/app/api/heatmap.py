"""``POST /api/heatmap``: 2D grid of call and put values across volatility
and spot price shocks.

Strict Pydantic validation enforces the threat model T12 cap (21 by 21
cells), bounds on the shock ranges, and ``extra='forbid'``. The actual
math runs through :mod:`app.pricing.black_scholes_vec`, which is
verified cell for cell against the scalar pricer.
"""

from __future__ import annotations

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.pricing.black_scholes_vec import black_scholes_call_vec, black_scholes_put_vec

router = APIRouter(prefix="/api", tags=["heatmap"])

MAX_DIMENSION = 21


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
    vol_shock: list[float] = Field(
        min_length=2, max_length=2, description="[min, max] vol shock as fraction of sigma."
    )
    spot_shock: list[float] = Field(
        min_length=2, max_length=2, description="[min, max] spot shock as fraction of S."
    )
    rows: int = Field(ge=1, le=MAX_DIMENSION, description="Number of vol axis points.")
    cols: int = Field(ge=1, le=MAX_DIMENSION, description="Number of spot axis points.")

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
    sigma_axis: list[float]
    spot_axis: list[float]


def _is_finite(x: float) -> bool:
    return x == x and x not in (float("inf"), float("-inf"))


@router.post("/heatmap", response_model=HeatmapResponse)
def heatmap(payload: HeatmapRequest) -> HeatmapResponse:
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

    call = black_scholes_call_vec(spot_axis, payload.K, payload.T, payload.r, sigma_axis)
    put = black_scholes_put_vec(spot_axis, payload.K, payload.T, payload.r, sigma_axis)

    return HeatmapResponse(
        call=call.tolist(),
        put=put.tolist(),
        sigma_axis=sigma_axis.tolist(),
        spot_axis=spot_axis.tolist(),
    )
