"""``POST /api/calculations``, ``GET /api/calculations``, and ``GET /api/calculations/{id}``.

Persists a heat map calculation: one row in ``calculation_inputs`` plus
``rows * cols`` rows in ``calculation_outputs``, in a single transaction.
The compute path reuses :mod:`app.pricing.black_scholes_vec` so the
math is identical to the pure ``POST /api/heatmap`` endpoint.

The list endpoint (``GET /api/calculations``) is paginated and orders
by ``created_at desc`` so the History screen can show the most recent
calculations first. Per route rate limits match the heat map endpoint
(``POST`` is the same compute plus a DB write; ``GET /{id}`` and the
list are cheap reads).

Security: all queries go through SQLAlchemy ORM mapped attributes, so
parameters are bound by the driver. No string formatting of SQL is
used. See ``docs/security/threat-model.md`` T1.
"""

from __future__ import annotations

import re
import uuid

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from starlette.requests import Request

from app.api.heatmap import HeatmapRequest, HeatmapResponse
from app.core.auth import require_user
from app.core.rate_limit import limiter
from app.db import CalculationInput, CalculationOutput, get_session
from app.pricing.black_scholes_vec import black_scholes_call_vec, black_scholes_put_vec

router = APIRouter(prefix="/api", tags=["calculations"])

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

# Per route caps. Writes mirror the heat map cap (same compute cost
# plus a DB write). Reads are cheap but list scans benefit from a per
# IP cap to deter scraping.
CALCULATIONS_WRITE_RATE_LIMIT = "12/minute"
CALCULATIONS_READ_RATE_LIMIT = "60/minute"

# Pagination cap. Matches `MAX_DIMENSION` from heatmap so the response
# size stays bounded; a future History screen can paginate further.
LIST_LIMIT_MAX = 50
LIST_LIMIT_DEFAULT = 20


class CalculationResponse(HeatmapResponse):
    calculation_id: str


@router.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(CALCULATIONS_WRITE_RATE_LIMIT)
def create_calculation(
    request: Request,
    payload: HeatmapRequest,
    user_id: str = Depends(require_user),
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

    call = black_scholes_call_vec(
        spot_axis, payload.K, payload.T, payload.r, sigma_axis, q=payload.q
    )
    put = black_scholes_put_vec(spot_axis, payload.K, payload.T, payload.r, sigma_axis, q=payload.q)

    calc_id = str(uuid.uuid4())
    record = CalculationInput(
        id=calc_id,
        s=payload.S,
        k=payload.K,
        t=payload.T,
        r=payload.r,
        sigma=payload.sigma,
        q=payload.q,
        vol_shock_min=payload.vol_shock[0],
        vol_shock_max=payload.vol_shock[1],
        spot_shock_min=payload.spot_shock[0],
        spot_shock_max=payload.spot_shock[1],
        rows=payload.rows,
        cols=payload.cols,
        user_id=user_id,
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
        model=payload.model,
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
    q: float
    rows: int
    cols: int
    call: list[list[float]]
    put: list[list[float]]
    sigma_axis: list[float]
    spot_axis: list[float]


class CalculationSummary(BaseModel):
    calculation_id: str
    created_at: str
    s: float
    k: float
    t: float
    r: float
    sigma: float
    q: float
    rows: int
    cols: int


class CalculationListResponse(BaseModel):
    items: list[CalculationSummary]
    total: int
    limit: int
    offset: int


@router.get("/calculations", response_model=CalculationListResponse)
@limiter.limit(CALCULATIONS_READ_RATE_LIMIT)
def list_calculations(
    request: Request,
    limit: int = Query(LIST_LIMIT_DEFAULT, ge=1, le=LIST_LIMIT_MAX, description="Page size."),
    offset: int = Query(0, ge=0, le=10_000, description="Number of items to skip."),
    user_id: str = Depends(require_user),
    session: Session = Depends(get_session),
) -> CalculationListResponse:
    total = int(
        session.execute(
            select(func.count(CalculationInput.id)).where(CalculationInput.user_id == user_id)
        ).scalar_one()
    )
    rows = (
        session.execute(
            select(CalculationInput)
            .where(CalculationInput.user_id == user_id)
            .order_by(CalculationInput.created_at.desc(), CalculationInput.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    items = [
        CalculationSummary(
            calculation_id=row.id,
            created_at=row.created_at.isoformat() if row.created_at is not None else "",
            s=row.s,
            k=row.k,
            t=row.t,
            r=row.r,
            sigma=row.sigma,
            q=row.q,
            rows=row.rows,
            cols=row.cols,
        )
        for row in rows
    ]
    return CalculationListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/calculations/{calculation_id}", response_model=CalculationDetail)
@limiter.limit(CALCULATIONS_READ_RATE_LIMIT)
def read_calculation(
    request: Request,
    calculation_id: str,
    user_id: str = Depends(require_user),
    session: Session = Depends(get_session),
) -> CalculationDetail:
    if not _UUID_RE.match(calculation_id):
        raise HTTPException(status_code=404, detail="Calculation not found.")

    record: CalculationInput | None = (
        session.query(CalculationInput)
        .options(selectinload(CalculationInput.outputs))
        .filter_by(id=calculation_id, user_id=user_id)
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
        q=record.q,
        rows=record.rows,
        cols=record.cols,
        call=call_grid,
        put=put_grid,
        sigma_axis=sigma_axis,
        spot_axis=spot_axis,
    )
