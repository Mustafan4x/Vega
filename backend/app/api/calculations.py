"""``POST /api/calculations`` and ``GET /api/calculations/{id}``.

Persists a heat map calculation: one row in ``calculation_inputs`` plus
``rows * cols`` rows in ``calculation_outputs``, in a single transaction.
The compute path reuses :mod:`app.pricing.black_scholes_vec` so the
math is identical to the pure ``POST /api/heatmap`` endpoint.

Security: all inserts go through SQLAlchemy ORM mapped attributes, so
parameters are bound by the driver. No string formatting of SQL is
used. See ``docs/security/threat-model.md`` T1.
"""

from __future__ import annotations

import re
import uuid

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload

from app.api.heatmap import HeatmapRequest, HeatmapResponse
from app.db import CalculationInput, CalculationOutput, get_session
from app.pricing.black_scholes_vec import black_scholes_call_vec, black_scholes_put_vec

router = APIRouter(prefix="/api", tags=["calculations"])

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class CalculationResponse(HeatmapResponse):
    calculation_id: str


@router.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_calculation(
    payload: HeatmapRequest,
    session: Session = Depends(get_session),
) -> CalculationResponse:
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

    calc_id = str(uuid.uuid4())
    record = CalculationInput(
        id=calc_id,
        s=payload.S,
        k=payload.K,
        t=payload.T,
        r=payload.r,
        sigma=payload.sigma,
        vol_shock_min=payload.vol_shock[0],
        vol_shock_max=payload.vol_shock[1],
        spot_shock_min=payload.spot_shock[0],
        spot_shock_max=payload.spot_shock[1],
        rows=payload.rows,
        cols=payload.cols,
    )
    session.add(record)

    rows_out: list[CalculationOutput] = []
    for ri in range(payload.rows):
        for ci in range(payload.cols):
            rows_out.append(
                CalculationOutput(
                    calculation_id=calc_id,
                    row_index=ri,
                    col_index=ci,
                    sigma_value=float(sigma_axis[ri]),
                    spot_value=float(spot_axis[ci]),
                    call_value=float(call[ri, ci]),
                    put_value=float(put[ri, ci]),
                )
            )
    session.add_all(rows_out)
    session.commit()

    return CalculationResponse(
        calculation_id=calc_id,
        call=call.tolist(),
        put=put.tolist(),
        sigma_axis=sigma_axis.tolist(),
        spot_axis=spot_axis.tolist(),
    )


class CalculationDetail(BaseModel):
    calculation_id: str
    s: float
    k: float
    t: float
    r: float
    sigma: float
    rows: int
    cols: int
    call: list[list[float]]
    put: list[list[float]]
    sigma_axis: list[float]
    spot_axis: list[float]


@router.get("/calculations/{calculation_id}", response_model=CalculationDetail)
def read_calculation(
    calculation_id: str,
    session: Session = Depends(get_session),
) -> CalculationDetail:
    if not _UUID_RE.match(calculation_id):
        raise HTTPException(status_code=404, detail="Calculation not found.")

    record: CalculationInput | None = (
        session.query(CalculationInput)
        .options(selectinload(CalculationInput.outputs))
        .filter_by(id=calculation_id)
        .one_or_none()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Calculation not found.")

    call_grid: list[list[float]] = [[0.0] * record.cols for _ in range(record.rows)]
    put_grid: list[list[float]] = [[0.0] * record.cols for _ in range(record.rows)]
    sigma_axis = [0.0] * record.rows
    spot_axis = [0.0] * record.cols
    for cell in record.outputs:
        call_grid[cell.row_index][cell.col_index] = cell.call_value
        put_grid[cell.row_index][cell.col_index] = cell.put_value
        sigma_axis[cell.row_index] = cell.sigma_value
        spot_axis[cell.col_index] = cell.spot_value

    return CalculationDetail(
        calculation_id=record.id,
        s=record.s,
        k=record.k,
        t=record.t,
        r=record.r,
        sigma=record.sigma,
        rows=record.rows,
        cols=record.cols,
        call=call_grid,
        put=put_grid,
        sigma_axis=sigma_axis,
        spot_axis=spot_axis,
    )
