"""Contract tests for ``POST /api/calculations`` and ``GET
/api/calculations/{id}``.

Validates the persistence layer: the write path produces a row in
``calculation_inputs`` plus N rows in ``calculation_outputs`` linked
by ``calculation_id``, and the read path reconstructs the grid bit
identical to what the write path returned.
"""

from __future__ import annotations

import math
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import CalculationInput, CalculationOutput, get_session_factory

VALID_PAYLOAD = {
    "S": 100.0,
    "K": 100.0,
    "T": 1.0,
    "r": 0.05,
    "sigma": 0.2,
    "vol_shock": [-0.5, 0.5],
    "spot_shock": [-0.3, 0.3],
    "rows": 5,
    "cols": 5,
}


def test_create_calculation_returns_201_with_uuid(client: TestClient) -> None:
    response = client.post("/api/calculations", json=VALID_PAYLOAD)

    assert response.status_code == 201, response.text
    body = response.json()
    assert "calculation_id" in body
    parsed = uuid.UUID(body["calculation_id"])
    assert str(parsed) == body["calculation_id"]


def test_create_calculation_returns_grid(client: TestClient) -> None:
    response = client.post("/api/calculations", json=VALID_PAYLOAD)

    body = response.json()
    assert len(body["call"]) == 5
    assert all(len(row) == 5 for row in body["call"])
    assert len(body["put"]) == 5
    assert len(body["sigma_axis"]) == 5
    assert len(body["spot_axis"]) == 5


def test_create_calculation_persists_input_row(client: TestClient) -> None:
    response = client.post("/api/calculations", json=VALID_PAYLOAD)
    calc_id = response.json()["calculation_id"]

    factory = get_session_factory()
    with factory() as session:
        record = session.get(CalculationInput, calc_id)
        assert record is not None
        assert record.s == VALID_PAYLOAD["S"]
        assert record.k == VALID_PAYLOAD["K"]
        assert record.rows == VALID_PAYLOAD["rows"]
        assert record.cols == VALID_PAYLOAD["cols"]
        assert record.created_at is not None


def test_create_calculation_persists_n_output_rows(client: TestClient) -> None:
    response = client.post("/api/calculations", json=VALID_PAYLOAD)
    calc_id = response.json()["calculation_id"]
    expected_count = VALID_PAYLOAD["rows"] * VALID_PAYLOAD["cols"]

    factory = get_session_factory()
    with factory() as session:
        rows = (
            session.execute(
                select(CalculationOutput).where(CalculationOutput.calculation_id == calc_id)
            )
            .scalars()
            .all()
        )
        assert len(rows) == expected_count
        for row in rows:
            assert math.isfinite(row.call_value)
            assert math.isfinite(row.put_value)
            assert row.call_value >= 0
            assert row.put_value >= 0


def test_get_calculation_returns_persisted_grid(client: TestClient) -> None:
    create = client.post("/api/calculations", json=VALID_PAYLOAD)
    calc_id = create.json()["calculation_id"]
    written_call = create.json()["call"]

    response = client.get(f"/api/calculations/{calc_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["calculation_id"] == calc_id
    assert body["s"] == VALID_PAYLOAD["S"]
    assert body["rows"] == VALID_PAYLOAD["rows"]
    assert body["call"] == written_call


def test_get_calculation_returns_404_for_unknown_uuid(client: TestClient) -> None:
    response = client.get(f"/api/calculations/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_calculation_returns_404_for_non_uuid(client: TestClient) -> None:
    response = client.get("/api/calculations/not-a-uuid")

    assert response.status_code == 404


def test_get_calculation_resists_path_injection_payloads(client: TestClient) -> None:
    # SQL injection patterns in the path parameter must be rejected at
    # the UUID gate, never reach the ORM. Per threat model T1.
    for payload in ("1' OR '1'='1", "abc; DROP TABLE calculation_inputs;--"):
        response = client.get(f"/api/calculations/{payload}")
        assert response.status_code == 404


def test_create_calculation_rejects_oversized_grid(client: TestClient) -> None:
    bad = {**VALID_PAYLOAD, "rows": 22, "cols": 22}

    response = client.post("/api/calculations", json=bad)

    assert response.status_code == 422


def test_create_calculation_rejects_extra_field(client: TestClient) -> None:
    # Phase 9 added `model` as a real field; use a genuinely unknown
    # one to exercise extra="forbid".
    bad = {**VALID_PAYLOAD, "shenanigans": True}

    response = client.post("/api/calculations", json=bad)

    assert response.status_code == 422


def test_create_calculation_two_writes_have_different_ids(client: TestClient) -> None:
    a = client.post("/api/calculations", json=VALID_PAYLOAD).json()["calculation_id"]
    b = client.post("/api/calculations", json=VALID_PAYLOAD).json()["calculation_id"]

    assert a != b


@pytest.mark.parametrize(
    "calc_id_attempt",
    [
        "../../etc/passwd",
        "%2e%2e/etc/passwd",
    ],
)
def test_get_calculation_rejects_path_traversal_attempt(
    client: TestClient, calc_id_attempt: str
) -> None:
    response = client.get(f"/api/calculations/{calc_id_attempt}")
    assert response.status_code in (404, 422)
