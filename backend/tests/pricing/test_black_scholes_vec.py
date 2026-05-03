"""Vectorized Black Scholes correctness tests.

The contract: vector pricers produce the same value, cell for cell, as the
scalar pricers in ``app.pricing.black_scholes``. Edge cases (T = 0,
sigma = 0, S = 0) inherit the same conventions documented in
``docs/math/black-scholes.md``.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from app.pricing.black_scholes import black_scholes_call, black_scholes_put
from app.pricing.black_scholes_vec import (
    black_scholes_call_vec,
    black_scholes_put_vec,
)


def _scalar_grid(
    fn, S_axis: np.ndarray, K: float, T: float, r: float, sigma_axis: np.ndarray
) -> np.ndarray:
    return np.array([[fn(float(S), K, T, r, float(s)) for S in S_axis] for s in sigma_axis])


@pytest.mark.parametrize(
    "S_axis, sigma_axis",
    [
        (np.array([90.0, 100.0, 110.0]), np.array([0.1, 0.2, 0.3])),
        (np.linspace(50.0, 150.0, 7), np.linspace(0.05, 0.6, 5)),
    ],
)
def test_call_vec_matches_scalar_grid(S_axis: np.ndarray, sigma_axis: np.ndarray) -> None:
    K, T, r = 100.0, 1.0, 0.05

    actual = black_scholes_call_vec(S_axis, K, T, r, sigma_axis)
    expected = _scalar_grid(black_scholes_call, S_axis, K, T, r, sigma_axis)

    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
    assert actual.shape == (sigma_axis.size, S_axis.size)


@pytest.mark.parametrize(
    "S_axis, sigma_axis",
    [
        (np.array([90.0, 100.0, 110.0]), np.array([0.1, 0.2, 0.3])),
        (np.linspace(50.0, 150.0, 5), np.linspace(0.05, 0.6, 4)),
    ],
)
def test_put_vec_matches_scalar_grid(S_axis: np.ndarray, sigma_axis: np.ndarray) -> None:
    K, T, r = 100.0, 1.0, 0.05

    actual = black_scholes_put_vec(S_axis, K, T, r, sigma_axis)
    expected = _scalar_grid(black_scholes_put, S_axis, K, T, r, sigma_axis)

    np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)


def test_vec_handles_T_zero_returns_intrinsic_grid() -> None:
    S_axis = np.array([80.0, 100.0, 120.0])
    sigma_axis = np.array([0.1, 0.5])

    call = black_scholes_call_vec(S_axis, 100.0, 0.0, 0.05, sigma_axis)
    put = black_scholes_put_vec(S_axis, 100.0, 0.0, 0.05, sigma_axis)

    np.testing.assert_array_equal(call, np.tile([0.0, 0.0, 20.0], (2, 1)))
    np.testing.assert_array_equal(put, np.tile([20.0, 0.0, 0.0], (2, 1)))


def test_vec_handles_sigma_zero_row_is_deterministic() -> None:
    S_axis = np.array([80.0, 100.0, 120.0])
    sigma_axis = np.array([0.0, 0.2])

    call = black_scholes_call_vec(S_axis, 100.0, 1.0, 0.05, sigma_axis)

    expected_zero_row = [max(S - 100.0 * math.exp(-0.05), 0.0) for S in S_axis]
    np.testing.assert_allclose(call[0], expected_zero_row, rtol=1e-12)
    assert all(call[1] > 0)


def test_vec_handles_S_zero_column() -> None:
    S_axis = np.array([0.0, 50.0, 100.0])
    sigma_axis = np.array([0.2])

    call = black_scholes_call_vec(S_axis, 100.0, 1.0, 0.05, sigma_axis)
    put = black_scholes_put_vec(S_axis, 100.0, 1.0, 0.05, sigma_axis)

    assert call[0, 0] == pytest.approx(0.0)
    assert put[0, 0] == pytest.approx(100.0 * math.exp(-0.05), rel=1e-12)


def test_vec_rejects_invalid_strike() -> None:
    with pytest.raises(ValueError, match="K"):
        black_scholes_call_vec(np.array([100.0]), 0.0, 1.0, 0.05, np.array([0.2]))


def test_vec_rejects_negative_T() -> None:
    with pytest.raises(ValueError, match="T"):
        black_scholes_call_vec(np.array([100.0]), 100.0, -0.1, 0.05, np.array([0.2]))


def test_vec_rejects_negative_S_in_axis() -> None:
    with pytest.raises(ValueError, match="S"):
        black_scholes_call_vec(np.array([-1.0, 100.0]), 100.0, 1.0, 0.05, np.array([0.2]))


def test_vec_rejects_negative_sigma_in_axis() -> None:
    with pytest.raises(ValueError, match="sigma"):
        black_scholes_call_vec(np.array([100.0]), 100.0, 1.0, 0.05, np.array([-0.1, 0.2]))


def test_vec_atm_grid_is_finite_and_positive() -> None:
    S_axis = np.linspace(80.0, 120.0, 9)
    sigma_axis = np.linspace(0.05, 0.6, 5)

    call = black_scholes_call_vec(S_axis, 100.0, 1.0, 0.05, sigma_axis)
    put = black_scholes_put_vec(S_axis, 100.0, 1.0, 0.05, sigma_axis)

    assert np.all(np.isfinite(call))
    assert np.all(np.isfinite(put))
    assert np.all(call >= 0)
    assert np.all(put >= 0)
