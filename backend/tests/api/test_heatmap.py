"""Contract tests for ``POST /api/heatmap``.

Strict Pydantic validation, dimension caps from the threat model
(T12: heat map grid capped at 21 by 21), happy path, edge cases, and
a soft performance assertion so a regression that turns the path
quadratic stops being green silently.
"""

from __future__ import annotations

import math
import time

import pytest
from fastapi.testclient import TestClient

VALID_PAYLOAD = {
    "S": 100.0,
    "K": 100.0,
    "T": 1.0,
    "r": 0.05,
    "sigma": 0.2,
    "vol_shock": [-0.5, 0.5],
    "spot_shock": [-0.3, 0.3],
    "rows": 9,
    "cols": 9,
}


def test_heatmap_happy_path_returns_two_grids(client: TestClient) -> None:
    response = client.post("/api/heatmap", json=VALID_PAYLOAD)

    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body.keys()) == {"call", "put", "model", "sigma_axis", "spot_axis"}
    assert body["model"] == "black_scholes"

    call = body["call"]
    put = body["put"]
    assert isinstance(call, list)
    assert len(call) == 9
    assert all(len(row) == 9 for row in call)
    assert len(put) == 9
    assert all(len(row) == 9 for row in put)

    assert len(body["sigma_axis"]) == 9
    assert len(body["spot_axis"]) == 9


def test_heatmap_axes_span_the_requested_shocks(client: TestClient) -> None:
    response = client.post("/api/heatmap", json=VALID_PAYLOAD)

    body = response.json()
    sigma_axis = body["sigma_axis"]
    spot_axis = body["spot_axis"]

    assert sigma_axis[0] == pytest.approx(0.2 * (1 + -0.5))
    assert sigma_axis[-1] == pytest.approx(0.2 * (1 + 0.5))
    assert spot_axis[0] == pytest.approx(100.0 * (1 + -0.3))
    assert spot_axis[-1] == pytest.approx(100.0 * (1 + 0.3))


def test_heatmap_values_are_finite_and_non_negative(client: TestClient) -> None:
    response = client.post("/api/heatmap", json=VALID_PAYLOAD)

    body = response.json()
    for grid in (body["call"], body["put"]):
        for row in grid:
            for cell in row:
                assert math.isfinite(cell)
                assert cell >= 0


@pytest.mark.parametrize("dim", ["rows", "cols"])
def test_heatmap_rejects_dimension_above_cap(client: TestClient, dim: str) -> None:
    payload = {**VALID_PAYLOAD, dim: 22}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("dim", ["rows", "cols"])
def test_heatmap_rejects_zero_dimension(client: TestClient, dim: str) -> None:
    payload = {**VALID_PAYLOAD, dim: 0}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 422


def test_heatmap_accepts_minimum_one_by_one(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "rows": 1, "cols": 1}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert len(body["call"]) == 1
    assert len(body["call"][0]) == 1


def test_heatmap_rejects_inverted_shock_range(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "vol_shock": [0.5, -0.5]}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 422


def test_heatmap_rejects_extreme_shock(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "vol_shock": [-2.0, 2.0]}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field, bad_value",
    [
        ("r", -10.0),
        ("r", 10.0),
        ("T", 1000.0),
        ("S", 1e12),
        ("sigma", 100.0),
    ],
)
def test_heatmap_rejects_out_of_bound_scalar_inputs(
    client: TestClient, field: str, bad_value: float
) -> None:
    payload = {**VALID_PAYLOAD, field: bad_value}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field", ["S", "K", "T", "r", "sigma", "vol_shock", "spot_shock", "rows", "cols"]
)
def test_heatmap_rejects_missing_field(client: TestClient, field: str) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != field}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 422


def test_heatmap_rejects_extra_fields(client: TestClient) -> None:
    # Phase 9 added `model` as a real field; use a genuinely unknown
    # one to exercise extra="forbid".
    payload = {**VALID_PAYLOAD, "shenanigans": True}

    response = client.post("/api/heatmap", json=payload)

    assert response.status_code == 422


def test_heatmap_defaults_model_to_black_scholes(client: TestClient) -> None:
    response = client.post("/api/heatmap", json=VALID_PAYLOAD)

    assert response.json()["model"] == "black_scholes"


def test_heatmap_binomial_grid_close_to_black_scholes(client: TestClient) -> None:
    bs_payload = {**VALID_PAYLOAD, "model": "black_scholes", "rows": 5, "cols": 5}
    bn_payload = {**VALID_PAYLOAD, "model": "binomial", "rows": 5, "cols": 5}
    bs_default = client.post(
        "/api/heatmap", json={**VALID_PAYLOAD, "model": "black_scholes"}
    ).json()
    binom = client.post("/api/heatmap", json=bn_payload).json()
    bs_5 = client.post("/api/heatmap", json=bs_payload).json()

    assert binom["model"] == "binomial"
    for ri, row in enumerate(binom["call"]):
        for ci, cell in enumerate(row):
            assert abs(cell - bs_5["call"][ri][ci]) < 0.5, (
                f"binomial cell ({ri},{ci}) differs from BS by too much"
            )
    assert len(bs_default["call"]) == 9  # original 9x9 still works


def test_heatmap_monte_carlo_grid_close_to_black_scholes(client: TestClient) -> None:
    mc_payload = {**VALID_PAYLOAD, "model": "monte_carlo", "rows": 5, "cols": 5}
    bs_payload = {**VALID_PAYLOAD, "model": "black_scholes", "rows": 5, "cols": 5}
    mc = client.post("/api/heatmap", json=mc_payload).json()
    bs_5 = client.post("/api/heatmap", json=bs_payload).json()

    assert mc["model"] == "monte_carlo"
    # MC at 20k paths per cell: per cell tolerance under 1.0 dollar
    # for the canonical centered grid.
    for ri, row in enumerate(mc["call"]):
        for ci, cell in enumerate(row):
            assert abs(cell - bs_5["call"][ri][ci]) < 1.0


def test_heatmap_rejects_unknown_model(client: TestClient) -> None:
    response = client.post("/api/heatmap", json={**VALID_PAYLOAD, "model": "heston"})

    assert response.status_code == 422


def test_heatmap_rejects_non_finite_inputs(client: TestClient) -> None:
    raw = (
        '{"S":100,"K":100,"T":1,"r":0.05,"sigma":Infinity,'
        '"vol_shock":[-0.5,0.5],"spot_shock":[-0.3,0.3],"rows":5,"cols":5}'
    )
    response = client.post(
        "/api/heatmap",
        content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422


def test_heatmap_call_grid_increases_with_spot(client: TestClient) -> None:
    response = client.post("/api/heatmap", json=VALID_PAYLOAD)

    call = response.json()["call"]
    middle_row = call[len(call) // 2]
    for left, right in zip(middle_row, middle_row[1:], strict=False):
        assert right >= left - 1e-9


def test_heatmap_performance_21_by_21_under_500_ms(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "rows": 21, "cols": 21}

    start = time.perf_counter()
    response = client.post("/api/heatmap", json=payload)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert response.status_code == 200
    assert elapsed_ms < 500, f"21x21 heatmap took {elapsed_ms:.1f} ms, expected < 500 ms"
