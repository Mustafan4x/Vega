"""Reference value tests for Black Scholes call and put pricing.

Authored by the Quant Domain Validator agent (Phase 1) before the Backend
Developer implements ``app.pricing.black_scholes``. This is the canonical
Test Driven Development red state: every test in this file will currently
fail with ``ModuleNotFoundError`` because ``app.pricing.black_scholes`` does
not yet exist. The Backend Developer's job in Phase 1 is to make these tests
pass without modifying any of the assertions or tolerances.

Conventions verified by these tests are documented in
``/home/mustafa/src/vega/docs/math/black-scholes.md``:

* ``T`` is in years.
* ``sigma`` is decimal annualized standard deviation.
* ``r`` is decimal continuously compounded.
* No dividends in v1.
* European exercise.

Reference value sources:

* Hull, *Options, Futures and Other Derivatives*, 10th ed., Ch. 15.
* Wilmott, *Paul Wilmott Introduces Quantitative Finance*, 2nd ed., Ch. 8.
* Natenberg, *Option Volatility and Pricing*, 2nd ed., Ch. 6.
* Closed form derivations from the math doc for boundary cases.
"""

from __future__ import annotations

import math

import pytest

from app.pricing.black_scholes import black_scholes_call, black_scholes_put

REL_TOL = 1e-4
PARITY_TOL = 1e-9


# =============================================================================
# Hull, 10th edition, Chapter 15
# =============================================================================


def test_hull_example_15_6_call() -> None:
    """Hull, *Options, Futures and Other Derivatives*, 10th ed., Example 15.6.

    Inputs: S=42, K=40, r=0.10, sigma=0.20, T=0.5.
    Hull prints the call price as 4.76; the closed form is 4.7594.
    """
    price = black_scholes_call(S=42.0, K=40.0, T=0.5, r=0.10, sigma=0.20)
    assert price == pytest.approx(4.7594, abs=REL_TOL)


def test_hull_example_15_6_put() -> None:
    """Hull, 10th ed., Example 15.6 (put leg).

    Inputs: S=42, K=40, r=0.10, sigma=0.20, T=0.5.
    Hull prints the put price as 0.81; the closed form is 0.8086.
    """
    price = black_scholes_put(S=42.0, K=40.0, T=0.5, r=0.10, sigma=0.20)
    assert price == pytest.approx(0.8086, abs=REL_TOL)


def test_hull_practice_problem_15_13_call() -> None:
    """Hull, 10th ed., Practice Problem 15.13 (a slightly ITM call).

    Inputs: S=52, K=50, r=0.12, sigma=0.30, T=0.25.
    Closed form call price: 5.0574.
    """
    price = black_scholes_call(S=52.0, K=50.0, T=0.25, r=0.12, sigma=0.30)
    assert price == pytest.approx(5.0574, abs=REL_TOL)


def test_hull_practice_problem_15_13_put() -> None:
    """Hull, 10th ed., Practice Problem 15.13 (put leg).

    Inputs: S=52, K=50, r=0.12, sigma=0.30, T=0.25.
    Closed form put price: 1.5797.
    """
    price = black_scholes_put(S=52.0, K=50.0, T=0.25, r=0.12, sigma=0.30)
    assert price == pytest.approx(1.5797, abs=REL_TOL)


# =============================================================================
# Wilmott, 2nd edition, Chapter 8: canonical ATM 1y benchmark
# =============================================================================


def test_wilmott_atm_one_year_call() -> None:
    """Wilmott, *Paul Wilmott Introduces Quantitative Finance*, 2nd ed., Ch. 8.

    The canonical at the money one year benchmark, also reproduced in
    Natenberg Ch. 6 and many other texts.

    Inputs: S=100, K=100, r=0.05, sigma=0.20, T=1.0.
    Closed form call price: 10.4506.
    """
    price = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    assert price == pytest.approx(10.4506, abs=REL_TOL)


def test_wilmott_atm_one_year_put() -> None:
    """Wilmott, 2nd ed., Ch. 8 (put leg of the canonical ATM benchmark).

    Inputs: S=100, K=100, r=0.05, sigma=0.20, T=1.0.
    Closed form put price: 5.5735.
    """
    price = black_scholes_put(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    assert price == pytest.approx(5.5735, abs=REL_TOL)


# =============================================================================
# Natenberg style ITM / OTM cases on S=100 (closed form, cross checked
# against Natenberg, *Option Volatility and Pricing*, 2nd ed., Ch. 6 and
# Hull Ch. 15 worked examples).
# =============================================================================


def test_deep_itm_call() -> None:
    """Deep in the money call: S=120, K=100, r=0.05, sigma=0.20, T=1.0.

    Closed form call price: 26.1690. Reference value derived from the
    closed form in ``docs/math/black-scholes.md`` and cross checked against
    Hull Ch. 15 worked examples.
    """
    price = black_scholes_call(S=120.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    assert price == pytest.approx(26.1690, abs=REL_TOL)


def test_deep_otm_call() -> None:
    """Deep out of the money call: S=80, K=100, r=0.05, sigma=0.20, T=1.0.

    Closed form call price: 1.8594.
    """
    price = black_scholes_call(S=80.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    assert price == pytest.approx(1.8594, abs=REL_TOL)


def test_deep_itm_put() -> None:
    """Deep in the money put: S=80, K=100, r=0.05, sigma=0.20, T=1.0.

    Closed form put price: 16.9824.
    """
    price = black_scholes_put(S=80.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    assert price == pytest.approx(16.9824, abs=REL_TOL)


def test_deep_otm_put() -> None:
    """Deep out of the money put: S=120, K=100, r=0.05, sigma=0.20, T=1.0.

    Closed form put price: 1.2920.
    """
    price = black_scholes_put(S=120.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    assert price == pytest.approx(1.2920, abs=REL_TOL)


def test_short_dated_atm_call() -> None:
    """Short dated ATM call: S=100, K=100, r=0.05, sigma=0.25, T=1/12.

    Closed form call price: 3.0852.
    """
    price = black_scholes_call(S=100.0, K=100.0, T=1.0 / 12.0, r=0.05, sigma=0.25)
    assert price == pytest.approx(3.0852, abs=REL_TOL)


def test_long_dated_low_vol_call() -> None:
    """Long dated low volatility OTM call: S=100, K=110, r=0.03, sigma=0.15, T=2.0.

    Closed form call price: 6.9201.
    """
    price = black_scholes_call(S=100.0, K=110.0, T=2.0, r=0.03, sigma=0.15)
    assert price == pytest.approx(6.9201, abs=REL_TOL)


def test_zero_rate_atm_symmetric() -> None:
    """Zero rate ATM: S=100, K=100, r=0.0, sigma=0.20, T=1.0.

    With r=0 and S=K, call and put are equal by put call parity. Closed
    form value: 7.9656.
    """
    call = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.0, sigma=0.20)
    put = black_scholes_put(S=100.0, K=100.0, T=1.0, r=0.0, sigma=0.20)
    assert call == pytest.approx(7.9656, abs=REL_TOL)
    assert put == pytest.approx(7.9656, abs=REL_TOL)


# =============================================================================
# Edge cases from docs/math/black-scholes.md
# =============================================================================


def test_t_zero_call_intrinsic_itm() -> None:
    """T=0 ITM call returns intrinsic value max(S-K, 0)."""
    assert black_scholes_call(S=110.0, K=100.0, T=0.0, r=0.05, sigma=0.20) == pytest.approx(
        10.0, abs=PARITY_TOL
    )


def test_t_zero_call_intrinsic_otm() -> None:
    """T=0 OTM call returns 0."""
    assert black_scholes_call(S=90.0, K=100.0, T=0.0, r=0.05, sigma=0.20) == pytest.approx(
        0.0, abs=PARITY_TOL
    )


def test_t_zero_put_intrinsic_itm() -> None:
    """T=0 ITM put returns intrinsic value max(K-S, 0)."""
    assert black_scholes_put(S=90.0, K=100.0, T=0.0, r=0.05, sigma=0.20) == pytest.approx(
        10.0, abs=PARITY_TOL
    )


def test_t_zero_put_intrinsic_otm() -> None:
    """T=0 OTM put returns 0."""
    assert black_scholes_put(S=110.0, K=100.0, T=0.0, r=0.05, sigma=0.20) == pytest.approx(
        0.0, abs=PARITY_TOL
    )


def test_sigma_zero_call_deterministic_forward_itm() -> None:
    """sigma=0 ITM call: deterministic forward F=S*exp(r*T) above K.

    With S=110, K=100, r=0.05, T=1: F=115.6831, intrinsic discounted is
    max(S - K*exp(-r*T), 0) = 110 - 100*exp(-0.05) = 14.8771.
    """
    expected = 110.0 - 100.0 * math.exp(-0.05 * 1.0)
    price = black_scholes_call(S=110.0, K=100.0, T=1.0, r=0.05, sigma=0.0)
    assert price == pytest.approx(expected, abs=PARITY_TOL)


def test_sigma_zero_call_deterministic_forward_otm() -> None:
    """sigma=0 deeply OTM call returns 0 when forward < K.

    With S=80, K=100, r=0.05, T=1: F=84.10, below K, so call worth 0.
    """
    price = black_scholes_call(S=80.0, K=100.0, T=1.0, r=0.05, sigma=0.0)
    assert price == pytest.approx(0.0, abs=PARITY_TOL)


def test_sigma_zero_put_deterministic_forward_itm() -> None:
    """sigma=0 ITM put: max(K*exp(-r*T) - S, 0)."""
    expected = max(100.0 * math.exp(-0.05 * 1.0) - 80.0, 0.0)
    price = black_scholes_put(S=80.0, K=100.0, T=1.0, r=0.05, sigma=0.0)
    assert price == pytest.approx(expected, abs=PARITY_TOL)


def test_sigma_zero_put_deterministic_forward_otm() -> None:
    """sigma=0 OTM put returns 0 when forward > K."""
    price = black_scholes_put(S=110.0, K=100.0, T=1.0, r=0.05, sigma=0.0)
    assert price == pytest.approx(0.0, abs=PARITY_TOL)


def test_s_zero_call_is_zero() -> None:
    """S=0 call is worth 0 (closed form limit, see math doc)."""
    assert black_scholes_call(S=0.0, K=100.0, T=1.0, r=0.05, sigma=0.20) == pytest.approx(
        0.0, abs=PARITY_TOL
    )


def test_s_zero_put_is_discounted_strike() -> None:
    """S=0 put is worth K*exp(-r*T) (closed form limit, see math doc)."""
    expected = 100.0 * math.exp(-0.05 * 1.0)
    price = black_scholes_put(S=0.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    assert price == pytest.approx(expected, abs=PARITY_TOL)


def test_very_small_sigma_numerically_stable() -> None:
    """Tiny sigma (1e-8) must not produce NaN, inf, or overflow.

    The price should be extremely close to the deterministic forward
    intrinsic, since sigma -> 0+ collapses the lognormal to a point mass.
    """
    price = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.05, sigma=1e-8)
    expected = max(100.0 - 100.0 * math.exp(-0.05 * 1.0), 0.0)
    assert math.isfinite(price)
    assert price == pytest.approx(expected, abs=1e-4)


def test_very_large_sigma_no_overflow() -> None:
    """Very large sigma (5.0 = 500 percent) returns a finite price.

    N(d1) and N(d2) are bounded on [0, 1]; the spot term is bounded by S
    and the discounted strike term is bounded by K*exp(-r*T), so the
    output must be finite.
    """
    price = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.05, sigma=5.0)
    assert math.isfinite(price)
    assert 0.0 <= price <= 100.0


# =============================================================================
# Negative input rejection (ValueError at module entry)
# =============================================================================


@pytest.mark.parametrize(
    "S, K, T, r, sigma",
    [
        (-1.0, 100.0, 1.0, 0.05, 0.20),
        (100.0, -1.0, 1.0, 0.05, 0.20),
        (100.0, 100.0, -0.1, 0.05, 0.20),
        (100.0, 100.0, 1.0, 0.05, -0.20),
        (100.0, 0.0, 1.0, 0.05, 0.20),
    ],
)
def test_call_rejects_invalid_inputs(S: float, K: float, T: float, r: float, sigma: float) -> None:
    """Negative S, K, T, sigma and zero strike all raise ValueError."""
    with pytest.raises(ValueError):
        black_scholes_call(S=S, K=K, T=T, r=r, sigma=sigma)


@pytest.mark.parametrize(
    "S, K, T, r, sigma",
    [
        (-1.0, 100.0, 1.0, 0.05, 0.20),
        (100.0, -1.0, 1.0, 0.05, 0.20),
        (100.0, 100.0, -0.1, 0.05, 0.20),
        (100.0, 100.0, 1.0, 0.05, -0.20),
        (100.0, 0.0, 1.0, 0.05, 0.20),
    ],
)
def test_put_rejects_invalid_inputs(S: float, K: float, T: float, r: float, sigma: float) -> None:
    """Negative S, K, T, sigma and zero strike all raise ValueError."""
    with pytest.raises(ValueError):
        black_scholes_put(S=S, K=K, T=T, r=r, sigma=sigma)


# =============================================================================
# Continuous dividend yield (q != 0): Hull 10e Chapter 17 reference values
# =============================================================================


@pytest.mark.parametrize(
    "S, K, T, r, sigma, q, expected_call, expected_put",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.03, 8.6525, 6.7309),
        (42.0, 40.0, 0.5, 0.10, 0.20, 0.02, 4.4383, 0.9054),
        (100.0, 110.0, 0.25, 0.05, 0.30, 0.05, 2.4692, 12.3450),
        (80.0, 70.0, 2.0, 0.04, 0.25, -0.01, 20.8842, 3.8862),
    ],
)
def test_call_put_with_dividend_yield(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float,
    expected_call: float,
    expected_put: float,
) -> None:
    """Hull 10e Chapter 17 closed-form values with continuous dividend yield."""
    call = black_scholes_call(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
    put = black_scholes_put(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
    assert call == pytest.approx(expected_call, abs=1e-4)
    assert put == pytest.approx(expected_put, abs=1e-4)


def test_q_zero_matches_no_dividend_path() -> None:
    """q == 0.0 is bit-identical to omitting q (default value preserved)."""
    no_q = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    with_q_zero = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, q=0.0)
    assert no_q == with_q_zero


# =============================================================================
# Put call parity: C - P == S - K * exp(-r*T)
# =============================================================================


@pytest.mark.parametrize(
    "S, K, T, r, sigma",
    [
        (42.0, 40.0, 0.5, 0.10, 0.20),
        (100.0, 100.0, 1.0, 0.05, 0.20),
        (52.0, 50.0, 0.25, 0.12, 0.30),
    ],
)
def test_put_call_parity(S: float, K: float, T: float, r: float, sigma: float) -> None:
    """Put call parity: C - P == S - K*exp(-r*T) within 1e-9.

    This invariant must hold for every Black Scholes implementation.
    Three diverse parameter sets are checked.
    """
    call = black_scholes_call(S=S, K=K, T=T, r=r, sigma=sigma)
    put = black_scholes_put(S=S, K=K, T=T, r=r, sigma=sigma)
    expected = S - K * math.exp(-r * T)
    assert (call - put) == pytest.approx(expected, abs=PARITY_TOL)
