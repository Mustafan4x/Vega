"""Black Scholes call and put pricing for European options on a non dividend paying stock.

Canonical math reference: ``/home/mustafa/src/vega/docs/math/black-scholes.md``.
Project conventions reference: ``/home/mustafa/src/vega/docs/risk/conventions.md``.

Pure module: no I/O, no global state, no logging. Stdlib only.

Greeks are returned in mathematical (textbook) units:

* delta: dimensionless, dollar change in option price per dollar change in S.
* gamma: per dollar of S squared.
* theta: per year (positive convention is time-to-expiry; theta is typically negative).
* vega:  per unit sigma (so a vega of 37.5 means the value moves $37.5 if sigma
         goes from 0.20 to 1.20). The API layer scales to "per 1 percent sigma"
         for display friendly units.
* rho:   per unit r (a rho of 53 means $53 move if r goes from 0.05 to 1.05).
         The API layer scales to "per 1 percent r" for display.

This separation keeps the math layer unambiguous and the conversion to display
units explicit in one place.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_SIGMA_DETERMINISTIC_THRESHOLD = 1e-12


@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


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


def _norm_pdf(x: float) -> float:
    """Standard normal PDF: phi(x) = exp(-x^2 / 2) / sqrt(2 pi)."""
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


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


def _greeks_components(
    S: float, K: float, T: float, r: float, sigma: float
) -> tuple[float, float, float, float]:
    """Return (d1, d2, N'(d1), discounted_strike). Used by the call/put Greek functions."""
    sigma_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return d1, d2, _norm_pdf(d1), K * math.exp(-r * T)


def _zero_greeks() -> Greeks:
    return Greeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0)


def black_scholes_call_greeks(S: float, K: float, T: float, r: float, sigma: float) -> Greeks:
    """Closed form Greeks for a European call. Math units (see module docstring)."""
    _validate_inputs(S, K, T, sigma)
    if T == 0.0 or S == 0.0 or sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return _zero_greeks()

    d1, d2, npdf_d1, discounted_strike = _greeks_components(S, K, T, r, sigma)
    sqrt_t = math.sqrt(T)

    delta = _norm_cdf(d1)
    gamma = npdf_d1 / (S * sigma * sqrt_t)
    vega = S * sqrt_t * npdf_d1
    theta = -S * npdf_d1 * sigma / (2.0 * sqrt_t) - r * discounted_strike * _norm_cdf(d2)
    rho = T * discounted_strike * _norm_cdf(d2)
    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)


def black_scholes_put_greeks(S: float, K: float, T: float, r: float, sigma: float) -> Greeks:
    """Closed form Greeks for a European put. Math units (see module docstring)."""
    _validate_inputs(S, K, T, sigma)
    if T == 0.0 or S == 0.0 or sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return _zero_greeks()

    d1, d2, npdf_d1, discounted_strike = _greeks_components(S, K, T, r, sigma)
    sqrt_t = math.sqrt(T)

    delta = _norm_cdf(d1) - 1.0
    gamma = npdf_d1 / (S * sigma * sqrt_t)
    vega = S * sqrt_t * npdf_d1
    theta = -S * npdf_d1 * sigma / (2.0 * sqrt_t) + r * discounted_strike * _norm_cdf(-d2)
    rho = -T * discounted_strike * _norm_cdf(-d2)
    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)
