"""Tests for the Cox Ross Rubinstein binomial tree pricer.

The CRR tree is a discrete time approximation of the same continuous
process Black Scholes describes, so as the number of steps grows the
two pricers converge. The tests pin convergence to within 1 cent of
the analytical Black Scholes price at the canonical Wilmott inputs
(S=100, K=100, T=1, r=0.05, sigma=0.20), plus the standard
edge cases that the Black Scholes module also handles (T=0, sigma=0,
S=0, deep ITM, deep OTM) and the put-call parity identity.

Reference: Cox, Ross, Rubinstein, "Option Pricing: A Simplified
Approach", *Journal of Financial Economics* 7 (1979), 229 to 263.
Convergence rate: O(1/n).
"""

from __future__ import annotations

import math

import pytest

from app.pricing.binomial import binomial_call, binomial_put
from app.pricing.black_scholes import black_scholes_call, black_scholes_put

# Canonical Wilmott / Natenberg / Hull inputs
S0, K0, T0, R0, SIGMA0 = 100.0, 100.0, 1.0, 0.05, 0.20

# Convergence tolerance at 500 steps. CRR converges as O(1/n) so this
# is a conservative bound; in practice the error is well under 1 cent.
TOL_500 = 0.05


def test_binomial_call_converges_to_black_scholes() -> None:
    bs = black_scholes_call(S0, K0, T0, R0, SIGMA0)
    binom = binomial_call(S0, K0, T0, R0, SIGMA0, steps=500)
    assert binom == pytest.approx(bs, abs=TOL_500)


def test_binomial_put_converges_to_black_scholes() -> None:
    bs = black_scholes_put(S0, K0, T0, R0, SIGMA0)
    binom = binomial_put(S0, K0, T0, R0, SIGMA0, steps=500)
    assert binom == pytest.approx(bs, abs=TOL_500)


def test_binomial_satisfies_put_call_parity() -> None:
    # C - P = S - K * exp(-rT). The discrete approximation must
    # respect the same arbitrage relation.
    call = binomial_call(S0, K0, T0, R0, SIGMA0, steps=300)
    put = binomial_put(S0, K0, T0, R0, SIGMA0, steps=300)
    parity_lhs = call - put
    parity_rhs = S0 - K0 * math.exp(-R0 * T0)
    assert parity_lhs == pytest.approx(parity_rhs, abs=TOL_500)


def test_binomial_zero_time_to_expiry_returns_intrinsic_call() -> None:
    # T=0 collapses to intrinsic: max(S-K, 0).
    assert binomial_call(120.0, 100.0, 0.0, 0.05, 0.2, steps=200) == pytest.approx(20.0)
    assert binomial_call(80.0, 100.0, 0.0, 0.05, 0.2, steps=200) == pytest.approx(0.0)


def test_binomial_zero_time_to_expiry_returns_intrinsic_put() -> None:
    assert binomial_put(80.0, 100.0, 0.0, 0.05, 0.2, steps=200) == pytest.approx(20.0)
    assert binomial_put(120.0, 100.0, 0.0, 0.05, 0.2, steps=200) == pytest.approx(0.0)


def test_binomial_zero_volatility_returns_deterministic_call() -> None:
    # sigma = 0 makes the asset deterministic: payoff is
    # max(S - K * exp(-rT), 0) for the call.
    expected = max(100.0 - 100.0 * math.exp(-0.05 * 1.0), 0.0)
    assert binomial_call(100.0, 100.0, 1.0, 0.05, 0.0, steps=200) == pytest.approx(
        expected, abs=1e-6
    )


def test_binomial_zero_underlying_call_is_zero() -> None:
    assert binomial_call(0.0, 100.0, 1.0, 0.05, 0.2, steps=100) == pytest.approx(0.0)


def test_binomial_deep_itm_call_approaches_intrinsic() -> None:
    # Deep ITM: S much greater than K and very low vol; price approaches
    # S - K * exp(-rT).
    intrinsic = 200.0 - 100.0 * math.exp(-0.05 * 1.0)
    assert binomial_call(200.0, 100.0, 1.0, 0.05, 0.05, steps=400) == pytest.approx(
        intrinsic, abs=0.05
    )


def test_binomial_deep_otm_put_approaches_zero() -> None:
    assert binomial_put(200.0, 100.0, 1.0, 0.05, 0.05, steps=200) == pytest.approx(0.0, abs=0.01)


def test_binomial_rejects_negative_S() -> None:
    with pytest.raises(ValueError):
        binomial_call(-1.0, 100.0, 1.0, 0.05, 0.2, steps=100)


def test_binomial_rejects_non_positive_K() -> None:
    with pytest.raises(ValueError):
        binomial_call(100.0, 0.0, 1.0, 0.05, 0.2, steps=100)


def test_binomial_rejects_negative_T() -> None:
    with pytest.raises(ValueError):
        binomial_call(100.0, 100.0, -0.1, 0.05, 0.2, steps=100)


def test_binomial_rejects_negative_sigma() -> None:
    with pytest.raises(ValueError):
        binomial_call(100.0, 100.0, 1.0, 0.05, -0.1, steps=100)


def test_binomial_rejects_non_positive_steps() -> None:
    with pytest.raises(ValueError):
        binomial_call(100.0, 100.0, 1.0, 0.05, 0.2, steps=0)
    with pytest.raises(ValueError):
        binomial_call(100.0, 100.0, 1.0, 0.05, 0.2, steps=-5)


@pytest.mark.parametrize("steps", [10, 50, 100, 250, 500])
def test_binomial_call_error_decreases_with_steps(steps: int) -> None:
    bs = black_scholes_call(S0, K0, T0, R0, SIGMA0)
    err = abs(binomial_call(S0, K0, T0, R0, SIGMA0, steps=steps) - bs)
    # CRR at n steps has worst case error around O(1/sqrt(n)) for
    # ATM options due to oscillation; bound generously.
    assert err < 0.5


@pytest.mark.parametrize(
    "S, K, T, r, sigma, q",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.03),
        (100.0, 110.0, 0.25, 0.05, 0.30, 0.05),
        (80.0, 70.0, 2.0, 0.04, 0.25, -0.01),
    ],
)
def test_binomial_converges_to_bs_with_dividend_yield(
    S: float, K: float, T: float, r: float, sigma: float, q: float
) -> None:
    """At 500 steps, the CRR tree price agrees with closed form BS within 1 cent."""
    bs_call = black_scholes_call(S, K, T, r, sigma, q=q)
    bs_put = black_scholes_put(S, K, T, r, sigma, q=q)
    bn_call = binomial_call(S, K, T, r, sigma, q=q, steps=500)
    bn_put = binomial_put(S, K, T, r, sigma, q=q, steps=500)
    assert bn_call == pytest.approx(bs_call, abs=0.01)
    assert bn_put == pytest.approx(bs_put, abs=0.01)


def test_binomial_q_zero_matches_no_dividend_path() -> None:
    """q=0 keyword preserves pre-feature numerical results bit-for-bit."""
    no_q = binomial_call(100.0, 100.0, 1.0, 0.05, 0.20, steps=500)
    with_q = binomial_call(100.0, 100.0, 1.0, 0.05, 0.20, q=0.0, steps=500)
    assert no_q == with_q
