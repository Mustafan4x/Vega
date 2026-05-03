"""Contract tests for ``POST /api/price``.

Covers happy path, validation failures, edge cases the pricing module must
handle, and error body shape (no stack traces, no internal field leakage).
"""

from __future__ import annotations

import math

import pytest
from fastapi.testclient import TestClient

VALID_PAYLOAD = {
    "S": 100.0,
    "K": 100.0,
    "T": 1.0,
    "r": 0.05,
    "sigma": 0.2,
}


def test_price_happy_path_returns_call_and_put(client: TestClient) -> None:
    response = client.post("/api/price", json=VALID_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"call", "put", "call_greeks", "put_greeks"}
    assert isinstance(body["call"], float)
    assert isinstance(body["put"], float)
    assert math.isfinite(body["call"])
    assert math.isfinite(body["put"])
    assert body["call"] > 0
    assert body["put"] > 0


def test_price_response_includes_greeks_in_display_units(client: TestClient) -> None:
    response = client.post("/api/price", json=VALID_PAYLOAD)

    body = response.json()
    for key in ("call_greeks", "put_greeks"):
        g = body[key]
        assert set(g.keys()) == {"delta", "gamma", "theta_per_day", "vega_per_pct", "rho_per_pct"}
        for v in g.values():
            assert math.isfinite(v)

    # Reference inputs S=K=100, T=1, r=0.05, sigma=0.20:
    # call delta ≈ 0.6368, put delta ≈ -0.3632.
    assert body["call_greeks"]["delta"] == pytest.approx(0.6368, abs=1e-3)
    assert body["put_greeks"]["delta"] == pytest.approx(-0.3632, abs=1e-3)
    # Vega per 1% ≈ 0.3752 (math vega 37.52 scaled by 0.01).
    assert body["call_greeks"]["vega_per_pct"] == pytest.approx(0.3752, abs=1e-3)
    # Theta per day ≈ math theta / 365.
    assert body["call_greeks"]["theta_per_day"] == pytest.approx(-6.414 / 365.0, abs=1e-4)


def test_price_greeks_zero_at_expiry(client: TestClient) -> None:
    response = client.post(
        "/api/price",
        json={**VALID_PAYLOAD, "T": 0.0},
    )

    body = response.json()
    for key in ("call_greeks", "put_greeks"):
        g = body[key]
        assert g["delta"] == 0.0
        assert g["gamma"] == 0.0
        assert g["theta_per_day"] == 0.0
        assert g["vega_per_pct"] == 0.0
        assert g["rho_per_pct"] == 0.0


def test_price_atm_call_greater_than_put_when_r_positive(client: TestClient) -> None:
    response = client.post("/api/price", json=VALID_PAYLOAD)

    body = response.json()
    assert body["call"] > body["put"]


def test_price_t_zero_returns_intrinsic_call(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "T": 0.0, "S": 110.0, "K": 100.0}

    response = client.post("/api/price", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["call"] == pytest.approx(10.0)
    assert body["put"] == pytest.approx(0.0)


def test_price_sigma_zero_returns_deterministic_payoff(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "sigma": 0.0}

    response = client.post("/api/price", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert math.isfinite(body["call"])
    assert math.isfinite(body["put"])


@pytest.mark.parametrize(
    "field, value",
    [
        ("S", -1.0),
        ("K", 0.0),
        ("K", -1.0),
        ("T", -0.5),
        ("sigma", -0.1),
    ],
)
def test_price_rejects_out_of_range_values(client: TestClient, field: str, value: float) -> None:
    payload = {**VALID_PAYLOAD, field: value}

    response = client.post("/api/price", json=payload)

    assert response.status_code == 422
    body = response.json()
    assert "detail" in body


@pytest.mark.parametrize("field", ["S", "K", "T", "r", "sigma"])
def test_price_rejects_missing_fields(client: TestClient, field: str) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != field}

    response = client.post("/api/price", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    ["S", "K", "T", "r", "sigma"],
)
def test_price_rejects_non_finite(client: TestClient, field: str) -> None:
    for sentinel in ("Infinity", "-Infinity", "NaN"):
        payload = dict(VALID_PAYLOAD)
        payload[field] = sentinel  # type: ignore[assignment]
        raw = (
            "{"
            + ",".join(f'"{k}":{v if k != field else sentinel}' for k, v in payload.items())
            + "}"
        )

        response = client.post(
            "/api/price",
            content=raw,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422, (
            f"expected 422 for non finite {field}={sentinel}, got {response.status_code}: "
            f"{response.text}"
        )


def test_price_rejects_extra_fields(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "model": "binomial"}

    response = client.post("/api/price", json=payload)

    assert response.status_code == 422


def test_price_rejects_string_for_numeric_field(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "sigma": "high"}

    response = client.post("/api/price", json=payload)

    assert response.status_code == 422


def test_price_error_body_does_not_leak_internals(client: TestClient) -> None:
    response = client.post("/api/price", json={**VALID_PAYLOAD, "S": -5.0})

    assert response.status_code == 422
    body = response.text.lower()
    assert "traceback" not in body
    assert "/home/" not in body
    assert "site-packages" not in body


def test_price_rejects_oversized_body(client: TestClient) -> None:
    big_blob = "a" * (33 * 1024)
    payload = {**VALID_PAYLOAD, "_pad": big_blob}

    response = client.post("/api/price", json=payload)

    assert response.status_code in (413, 422)


def test_price_returns_textbook_value_at_known_inputs(client: TestClient) -> None:
    response = client.post(
        "/api/price",
        json={"S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.2},
    )

    body = response.json()
    assert body["call"] == pytest.approx(10.4506, abs=1e-3)
    assert body["put"] == pytest.approx(5.5735, abs=1e-3)
