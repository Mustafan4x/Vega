"""Greeks correctness tests.

Reference values come from Hull (10th ed.) and verified by hand at the
canonical reference inputs S=100, K=100, T=1, r=0.05, sigma=0.20. See
``docs/risk/sanity-cases.md`` Case 1 for the call and put values that
already passed the Risk Reviewer in Phase 1.

Property tests exercise: put call parity, delta bounds, gamma sign and
identity across call/put, vega sign and identity across call/put.
"""

from __future__ import annotations

import math

import pytest

from app.pricing.black_scholes import (
    black_scholes_call,
    black_scholes_call_greeks,
    black_scholes_put,
    black_scholes_put_greeks,
)

# ── Reference values at S=K=100, T=1, r=0.05, sigma=0.20 ──────────────────
# Computed by hand (and reverified analytically): d1 = 0.35, d2 = 0.15.
# N(0.35) ≈ 0.6368, N(0.15) ≈ 0.5596, phi(0.35) ≈ 0.3752.

REF_INPUTS = (100.0, 100.0, 1.0, 0.05, 0.20)
REF_CALL_DELTA = 0.6368
REF_PUT_DELTA = -0.3632
REF_GAMMA = 0.01876
REF_VEGA = 37.52
REF_CALL_THETA = -6.414
REF_PUT_THETA = -1.658
REF_CALL_RHO = 53.232
REF_PUT_RHO = -41.890


def test_call_delta_at_reference() -> None:
    g = black_scholes_call_greeks(*REF_INPUTS)
    assert g.delta == pytest.approx(REF_CALL_DELTA, abs=1e-3)


def test_put_delta_at_reference() -> None:
    g = black_scholes_put_greeks(*REF_INPUTS)
    assert g.delta == pytest.approx(REF_PUT_DELTA, abs=1e-3)


def test_gamma_at_reference_matches_call_and_put() -> None:
    call_g = black_scholes_call_greeks(*REF_INPUTS)
    put_g = black_scholes_put_greeks(*REF_INPUTS)
    assert call_g.gamma == pytest.approx(REF_GAMMA, abs=1e-4)
    assert put_g.gamma == pytest.approx(REF_GAMMA, abs=1e-4)


def test_vega_at_reference_matches_call_and_put() -> None:
    call_g = black_scholes_call_greeks(*REF_INPUTS)
    put_g = black_scholes_put_greeks(*REF_INPUTS)
    assert call_g.vega == pytest.approx(REF_VEGA, abs=1e-2)
    assert put_g.vega == pytest.approx(REF_VEGA, abs=1e-2)


def test_call_theta_at_reference() -> None:
    g = black_scholes_call_greeks(*REF_INPUTS)
    assert g.theta == pytest.approx(REF_CALL_THETA, abs=1e-2)


def test_put_theta_at_reference() -> None:
    g = black_scholes_put_greeks(*REF_INPUTS)
    assert g.theta == pytest.approx(REF_PUT_THETA, abs=1e-2)


def test_call_rho_at_reference() -> None:
    g = black_scholes_call_greeks(*REF_INPUTS)
    assert g.rho == pytest.approx(REF_CALL_RHO, abs=1e-2)


def test_put_rho_at_reference() -> None:
    g = black_scholes_put_greeks(*REF_INPUTS)
    assert g.rho == pytest.approx(REF_PUT_RHO, abs=1e-2)


# ── Property tests ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "S,K,T,r,sigma",
    [
        (90.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 1.0, 0.05, 0.2),
        (110.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 0.5, 0.03, 0.4),
        (50.0, 100.0, 2.0, 0.07, 0.6),
    ],
)
def test_put_call_parity_for_call_price(
    S: float, K: float, T: float, r: float, sigma: float
) -> None:
    # C - P = S - K * e^(-r T)
    call = black_scholes_call(S, K, T, r, sigma)
    put = black_scholes_put(S, K, T, r, sigma)
    expected = S - K * math.exp(-r * T)
    assert call - put == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize(
    "S,K,T,r,sigma",
    [
        (90.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 1.0, 0.05, 0.2),
        (110.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 0.5, 0.03, 0.4),
    ],
)
def test_put_call_delta_relationship(S: float, K: float, T: float, r: float, sigma: float) -> None:
    # delta_call - delta_put = 1 (no dividends)
    call_g = black_scholes_call_greeks(S, K, T, r, sigma)
    put_g = black_scholes_put_greeks(S, K, T, r, sigma)
    assert call_g.delta - put_g.delta == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize(
    "S,K,T,r,sigma",
    [
        (90.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 1.0, 0.05, 0.2),
        (110.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 0.5, 0.03, 0.4),
        (50.0, 100.0, 2.0, 0.07, 0.6),
    ],
)
def test_call_delta_in_zero_one(S: float, K: float, T: float, r: float, sigma: float) -> None:
    g = black_scholes_call_greeks(S, K, T, r, sigma)
    assert 0.0 <= g.delta <= 1.0


@pytest.mark.parametrize(
    "S,K,T,r,sigma",
    [
        (90.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 1.0, 0.05, 0.2),
        (110.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 0.5, 0.03, 0.4),
        (50.0, 100.0, 2.0, 0.07, 0.6),
    ],
)
def test_put_delta_in_minus_one_zero(S: float, K: float, T: float, r: float, sigma: float) -> None:
    g = black_scholes_put_greeks(S, K, T, r, sigma)
    assert -1.0 <= g.delta <= 0.0


@pytest.mark.parametrize(
    "S,K,T,r,sigma",
    [
        (90.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 1.0, 0.05, 0.2),
        (110.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 0.5, 0.03, 0.4),
    ],
)
def test_gamma_non_negative_and_call_put_identical(
    S: float, K: float, T: float, r: float, sigma: float
) -> None:
    call_g = black_scholes_call_greeks(S, K, T, r, sigma)
    put_g = black_scholes_put_greeks(S, K, T, r, sigma)
    assert call_g.gamma >= 0.0
    assert put_g.gamma >= 0.0
    assert call_g.gamma == pytest.approx(put_g.gamma, abs=1e-12)


@pytest.mark.parametrize(
    "S,K,T,r,sigma",
    [
        (90.0, 100.0, 1.0, 0.05, 0.2),
        (100.0, 100.0, 1.0, 0.05, 0.2),
        (110.0, 100.0, 1.0, 0.05, 0.2),
    ],
)
def test_vega_non_negative_and_call_put_identical(
    S: float, K: float, T: float, r: float, sigma: float
) -> None:
    call_g = black_scholes_call_greeks(S, K, T, r, sigma)
    put_g = black_scholes_put_greeks(S, K, T, r, sigma)
    assert call_g.vega >= 0.0
    assert put_g.vega >= 0.0
    assert call_g.vega == pytest.approx(put_g.vega, abs=1e-12)


def test_greeks_at_T_zero_are_zero() -> None:
    call_g = black_scholes_call_greeks(100.0, 100.0, 0.0, 0.05, 0.2)
    put_g = black_scholes_put_greeks(100.0, 100.0, 0.0, 0.05, 0.2)
    for g in (call_g, put_g):
        assert g.delta == 0.0
        assert g.gamma == 0.0
        assert g.theta == 0.0
        assert g.vega == 0.0
        assert g.rho == 0.0


def test_greeks_at_sigma_zero_are_zero() -> None:
    call_g = black_scholes_call_greeks(100.0, 100.0, 1.0, 0.05, 0.0)
    assert call_g.delta == 0.0
    assert call_g.gamma == 0.0


def test_greeks_reject_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="K"):
        black_scholes_call_greeks(100.0, 0.0, 1.0, 0.05, 0.2)
    with pytest.raises(ValueError, match="sigma"):
        black_scholes_put_greeks(100.0, 100.0, 1.0, 0.05, -0.1)
