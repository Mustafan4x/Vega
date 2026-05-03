"""Black Scholes call and put pricing for European options on a non dividend paying stock.

Canonical math reference: ``/home/mustafa/src/trader/docs/math/black-scholes.md``.
Project conventions reference: ``/home/mustafa/src/trader/docs/risk/conventions.md``.

Pure module: no I/O, no global state, no logging. Stdlib only.
"""

from __future__ import annotations

import math

_SIGMA_DETERMINISTIC_THRESHOLD = 1e-12


def _validate_inputs(S: float, K: float, T: float, sigma: float) -> None:
    if S < 0:
        raise ValueError(f"S must be non negative, got S={S}")
    if K <= 0:
        raise ValueError(f"K must be strictly positive (the formula divides by K), got K={K}")
    if T < 0:
        raise ValueError(f"T must be non negative, got T={T}")
    if sigma < 0:
        raise ValueError(f"sigma must be non negative, got sigma={sigma}")


def _norm_cdf(x: float) -> float:
    """Standard normal CDF computed from the error function.

    N(x) = 0.5 * (1 + erf(x / sqrt(2))). Bounded on [0, 1]; uses stdlib only.
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Price a European call option under the Black Scholes model.

    See ``docs/math/black-scholes.md`` for the formula, conventions, and edge cases.
    """
    _validate_inputs(S, K, T, sigma)

    if T == 0.0:
        return max(S - K, 0.0)

    discounted_strike = K * math.exp(-r * T)

    if S == 0.0:
        return 0.0

    if sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return max(S - discounted_strike, 0.0)

    sigma_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return S * _norm_cdf(d1) - discounted_strike * _norm_cdf(d2)


def black_scholes_put(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Price a European put option under the Black Scholes model.

    See ``docs/math/black-scholes.md`` for the formula, conventions, and edge cases.
    """
    _validate_inputs(S, K, T, sigma)

    if T == 0.0:
        return max(K - S, 0.0)

    discounted_strike = K * math.exp(-r * T)

    if S == 0.0:
        return discounted_strike

    if sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return max(discounted_strike - S, 0.0)

    sigma_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return discounted_strike * _norm_cdf(-d2) - S * _norm_cdf(-d1)
