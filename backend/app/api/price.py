"""``POST /api/price``: Black Scholes call and put pricing.

Strict Pydantic validation per ``docs/security/threat-model.md`` T4 and T9:
no extra fields, no infinity or NaN, mathematical bounds enforced before the
pricing module is called.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.pricing.black_scholes import black_scholes_call, black_scholes_put

router = APIRouter(prefix="/api", tags=["pricing"])


class PriceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    S: float = Field(ge=0, allow_inf_nan=False, description="Current asset price.")
    K: float = Field(gt=0, allow_inf_nan=False, description="Strike price.")
    T: float = Field(ge=0, allow_inf_nan=False, description="Time to expiry in years.")
    r: float = Field(allow_inf_nan=False, description="Risk free rate (annualized, continuous).")
    sigma: float = Field(ge=0, allow_inf_nan=False, description="Volatility (annualized).")


class PriceResponse(BaseModel):
    call: float
    put: float


@router.post("/price", response_model=PriceResponse)
def price(payload: PriceRequest) -> PriceResponse:
    call = black_scholes_call(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    put = black_scholes_put(payload.S, payload.K, payload.T, payload.r, payload.sigma)
    return PriceResponse(call=call, put=put)
