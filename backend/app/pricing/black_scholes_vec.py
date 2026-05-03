"""Vectorized Black Scholes pricing for option grids.

Operates on a 1D ``S`` axis and a 1D ``sigma`` axis and returns a 2D
ndarray with rows indexed by ``sigma`` and columns indexed by ``S``,
matching the heat map layout in ``docs/design/wireframes.md``.

Mathematical conventions, edge cases, and the canonical formula are
documented in ``docs/math/black-scholes.md``. This module mirrors the
scalar implementation in :mod:`app.pricing.black_scholes` cell for
cell; the matching is enforced by ``test_black_scholes_vec.py``.
"""

from __future__ import annotations

import math
from typing import cast

import numpy as np
from numpy.typing import NDArray

_SIGMA_DETERMINISTIC_THRESHOLD = 1e-12

FloatArray = NDArray[np.floating]


def _validate(S_axis: FloatArray, K: float, T: float, sigma_axis: FloatArray) -> None:
    if K <= 0:
        raise ValueError(f"K must be strictly positive, got K={K}")
    if T < 0:
        raise ValueError(f"T must be non negative, got T={T}")
    if np.any(S_axis < 0):
        raise ValueError("S axis contains a negative value, which is not supported.")
    if np.any(sigma_axis < 0):
        raise ValueError("sigma axis contains a negative value, which is not supported.")


def _norm_cdf(x: FloatArray) -> FloatArray:
    # Using the error function so the implementation is identical to
    # the scalar module; keeps the cell for cell match within fp noise.
    sqrt2 = math.sqrt(2.0)
    erf_vec = np.frompyfunc(math.erf, 1, 1)
    return cast(FloatArray, 0.5 * (1.0 + erf_vec(x / sqrt2).astype(np.float64)))


def _grid(S_axis: FloatArray, sigma_axis: FloatArray) -> tuple[FloatArray, FloatArray]:
    # sigma as column, S as row, so the result has shape (rows, cols)
    # = (sigma_axis.size, S_axis.size).
    sigma = sigma_axis.reshape(-1, 1).astype(np.float64, copy=False)
    S = S_axis.reshape(1, -1).astype(np.float64, copy=False)
    return S, sigma


def black_scholes_call_vec(
    S_axis: FloatArray | list[float],
    K: float,
    T: float,
    r: float,
    sigma_axis: FloatArray | list[float],
) -> FloatArray:
    s_arr = np.asarray(S_axis, dtype=np.float64)
    sig_arr = np.asarray(sigma_axis, dtype=np.float64)
    _validate(s_arr, K, T, sig_arr)

    S, sigma = _grid(s_arr, sig_arr)

    if T == 0.0:
        return cast(FloatArray, np.maximum(S - K, 0.0) + np.zeros_like(sigma))

    discounted_strike = K * math.exp(-r * T)
    deterministic = np.maximum(S - discounted_strike, 0.0)
    deterministic = np.where(S == 0.0, 0.0, deterministic)

    sqrt_t = math.sqrt(T)
    sigma_safe = np.where(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, 1.0, sigma)
    S_safe = np.where(S == 0.0, 1.0, S)
    d1 = (np.log(S_safe / K) + (r + 0.5 * sigma_safe * sigma_safe) * T) / (sigma_safe * sqrt_t)
    d2 = d1 - sigma_safe * sqrt_t
    bs_value = S_safe * _norm_cdf(d1) - discounted_strike * _norm_cdf(d2)

    out = np.broadcast_to(bs_value, (sig_arr.size, s_arr.size)).copy()
    sigma_zero = np.broadcast_to(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, out.shape)
    s_zero = np.broadcast_to(S == 0.0, out.shape)
    deterministic_grid = np.broadcast_to(deterministic, out.shape)
    return cast(FloatArray, np.where(sigma_zero | s_zero, deterministic_grid, out))


def black_scholes_put_vec(
    S_axis: FloatArray | list[float],
    K: float,
    T: float,
    r: float,
    sigma_axis: FloatArray | list[float],
) -> FloatArray:
    s_arr = np.asarray(S_axis, dtype=np.float64)
    sig_arr = np.asarray(sigma_axis, dtype=np.float64)
    _validate(s_arr, K, T, sig_arr)

    S, sigma = _grid(s_arr, sig_arr)

    if T == 0.0:
        return cast(FloatArray, np.maximum(K - S, 0.0) + np.zeros_like(sigma))

    discounted_strike = K * math.exp(-r * T)
    deterministic = np.maximum(discounted_strike - S, 0.0)
    deterministic = np.where(S == 0.0, discounted_strike, deterministic)

    sqrt_t = math.sqrt(T)
    sigma_safe = np.where(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, 1.0, sigma)
    S_safe = np.where(S == 0.0, 1.0, S)
    d1 = (np.log(S_safe / K) + (r + 0.5 * sigma_safe * sigma_safe) * T) / (sigma_safe * sqrt_t)
    d2 = d1 - sigma_safe * sqrt_t
    bs_value = discounted_strike * _norm_cdf(-d2) - S_safe * _norm_cdf(-d1)

    out = np.broadcast_to(bs_value, (sig_arr.size, s_arr.size)).copy()
    sigma_zero = np.broadcast_to(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, out.shape)
    s_zero = np.broadcast_to(S == 0.0, out.shape)
    deterministic_grid = np.broadcast_to(deterministic, out.shape)
    return cast(FloatArray, np.where(sigma_zero | s_zero, deterministic_grid, out))
