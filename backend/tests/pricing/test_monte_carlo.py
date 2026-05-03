"""Tests for the Monte Carlo pricer (geometric Brownian motion).

The MC pricer simulates terminal asset prices ``S_T = S_0 * exp((r -
sigma^2 / 2) * T + sigma * sqrt(T) * Z)`` for ``Z ~ N(0, 1)`` and
discounts the average payoff. Antithetic variates halve the standard
error.

All tests use a fixed seed so the assertions are deterministic. The
tolerance is the 95% Monte Carlo confidence radius: with antithetic
variates and 200_000 paths the standard error at the canonical
Wilmott inputs is well under 0.05 for both legs.

Reference: Glasserman, *Monte Carlo Methods in Financial Engineering*,
Chs. 3 and 4.
"""

from __future__ import annotations

import math

import pytest

from app.pricing.black_scholes import black_scholes_call, black_scholes_put
from app.pricing.monte_carlo import monte_carlo_call, monte_carlo_put

# Canonical Wilmott / Natenberg / Hull inputs.
S0, K0, T0, R0, SIGMA0 = 100.0, 100.0, 1.0, 0.05, 0.20

# 95% MC error bar at 200k paths with antithetic variates.
MC_TOL = 0.10


def test_monte_carlo_call_converges_to_black_scholes() -> None:
    bs = black_scholes_call(S0, K0, T0, R0, SIGMA0)
    mc = monte_carlo_call(S0, K0, T0, R0, SIGMA0, paths=200_000, seed=42)
    assert mc == pytest.approx(bs, abs=MC_TOL)


def test_monte_carlo_put_converges_to_black_scholes() -> None:
    bs = black_scholes_put(S0, K0, T0, R0, SIGMA0)
    mc = monte_carlo_put(S0, K0, T0, R0, SIGMA0, paths=200_000, seed=42)
    assert mc == pytest.approx(bs, abs=MC_TOL)


def test_monte_carlo_satisfies_put_call_parity() -> None:
    # With the same seed the call and put paths share the same
    # antithetic structure, so parity holds within MC error.
    call = monte_carlo_call(S0, K0, T0, R0, SIGMA0, paths=200_000, seed=7)
    put = monte_carlo_put(S0, K0, T0, R0, SIGMA0, paths=200_000, seed=7)
    parity_lhs = call - put
    parity_rhs = S0 - K0 * math.exp(-R0 * T0)
    assert parity_lhs == pytest.approx(parity_rhs, abs=MC_TOL)


def test_monte_carlo_is_deterministic_for_fixed_seed() -> None:
    a = monte_carlo_call(S0, K0, T0, R0, SIGMA0, paths=10_000, seed=1234)
    b = monte_carlo_call(S0, K0, T0, R0, SIGMA0, paths=10_000, seed=1234)
    assert a == b


def test_monte_carlo_different_seeds_give_different_results() -> None:
    a = monte_carlo_call(S0, K0, T0, R0, SIGMA0, paths=10_000, seed=1)
    b = monte_carlo_call(S0, K0, T0, R0, SIGMA0, paths=10_000, seed=2)
    assert a != b


def test_monte_carlo_zero_time_to_expiry_returns_intrinsic_call() -> None:
    assert monte_carlo_call(120.0, 100.0, 0.0, 0.05, 0.2, paths=1000, seed=0) == pytest.approx(20.0)
    assert monte_carlo_call(80.0, 100.0, 0.0, 0.05, 0.2, paths=1000, seed=0) == pytest.approx(0.0)


def test_monte_carlo_zero_time_to_expiry_returns_intrinsic_put() -> None:
    assert monte_carlo_put(80.0, 100.0, 0.0, 0.05, 0.2, paths=1000, seed=0) == pytest.approx(20.0)
    assert monte_carlo_put(120.0, 100.0, 0.0, 0.05, 0.2, paths=1000, seed=0) == pytest.approx(0.0)


def test_monte_carlo_zero_volatility_returns_deterministic_call() -> None:
    expected = max(100.0 - 100.0 * math.exp(-0.05 * 1.0), 0.0)
    assert monte_carlo_call(100.0, 100.0, 1.0, 0.05, 0.0, paths=1000, seed=0) == pytest.approx(
        expected, abs=1e-6
    )


def test_monte_carlo_zero_underlying_call_is_zero() -> None:
    assert monte_carlo_call(0.0, 100.0, 1.0, 0.05, 0.2, paths=1000, seed=0) == pytest.approx(0.0)


def test_monte_carlo_rejects_negative_S() -> None:
    with pytest.raises(ValueError):
        monte_carlo_call(-1.0, 100.0, 1.0, 0.05, 0.2, paths=1000)


def test_monte_carlo_rejects_non_positive_K() -> None:
    with pytest.raises(ValueError):
        monte_carlo_call(100.0, 0.0, 1.0, 0.05, 0.2, paths=1000)


def test_monte_carlo_rejects_negative_T() -> None:
    with pytest.raises(ValueError):
        monte_carlo_call(100.0, 100.0, -0.1, 0.05, 0.2, paths=1000)


def test_monte_carlo_rejects_negative_sigma() -> None:
    with pytest.raises(ValueError):
        monte_carlo_call(100.0, 100.0, 1.0, 0.05, -0.1, paths=1000)


def test_monte_carlo_rejects_non_positive_paths() -> None:
    with pytest.raises(ValueError):
        monte_carlo_call(100.0, 100.0, 1.0, 0.05, 0.2, paths=0)
    with pytest.raises(ValueError):
        monte_carlo_call(100.0, 100.0, 1.0, 0.05, 0.2, paths=-1)
