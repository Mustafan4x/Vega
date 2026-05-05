"""Cox Ross Rubinstein binomial tree pricer for European options.

Reference: Cox, Ross, Rubinstein, "Option Pricing: A Simplified
Approach", *Journal of Financial Economics* 7 (1979), 229 to 263.

The CRR tree discretizes time into ``steps`` intervals of length
``dt = T / steps``. At each step the underlying moves up by a factor
``u = exp(sigma * sqrt(dt))`` or down by ``d = 1 / u`` with risk
neutral probability ``p = (exp(r * dt) - d) / (u - d)``. The terminal
payoff is rolled back to the present by discounting at ``r`` on each
step.

Pure module: numpy plus stdlib only, no I/O. Vectorized terminal
payoff and rollback so a 500 step tree prices in well under a
millisecond.

Edge cases mirror ``app.pricing.black_scholes`` so the model can be
swapped at the API boundary without surprising the user:

* ``T == 0`` returns the intrinsic payoff.
* ``sigma == 0`` returns the deterministic discounted payoff.
* ``S == 0`` returns 0 for the call, ``K * exp(-rT)`` for the put.

Convergence: the CRR tree is O(1/n) for European options with
oscillation around the analytical price (see e.g., Tian's smoothing
technique). For 500 steps the error at the canonical Wilmott inputs
(S=100, K=100, T=1, r=0.05, sigma=0.20) is well under 1 cent.
"""

from __future__ import annotations

import math

import numpy as np

DEFAULT_STEPS = 500


def _validate(S: float, K: float, T: float, sigma: float, steps: int) -> None:
    if S < 0:
        raise ValueError(f"S must be non negative, got S={S}")
    if K <= 0:
        raise ValueError(f"K must be strictly positive, got K={K}")
    if T < 0:
        raise ValueError(f"T must be non negative, got T={T}")
    if sigma < 0:
        raise ValueError(f"sigma must be non negative, got sigma={sigma}")
    if steps <= 0:
        raise ValueError(f"steps must be strictly positive, got steps={steps}")


def _crr_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    steps: int,
    is_call: bool,
    q: float = 0.0,
) -> float:
    _validate(S, K, T, sigma, steps)

    if T == 0.0:
        return _intrinsic(S, K, is_call)

    if S == 0.0:
        return 0.0 if is_call else K * math.exp(-r * T)

    if sigma <= 1e-12:
        forward = S * math.exp((r - q) * T)
        intrinsic = forward - K if is_call else K - forward
        return max(intrinsic, 0.0) * math.exp(-r * T)

    dt = T / steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1.0 / u
    a = math.exp((r - q) * dt)
    p = (a - d) / (u - d)
    if not (0.0 < p < 1.0):
        forward = S * math.exp((r - q) * T)
        intrinsic = forward - K if is_call else K - forward
        return max(intrinsic, 0.0) * math.exp(-r * T)

    discount = math.exp(-r * dt)

    j = np.arange(steps + 1)
    terminal = S * (u ** (steps - j)) * (d**j)
    if is_call:
        values = np.maximum(terminal - K, 0.0)
    else:
        values = np.maximum(K - terminal, 0.0)

    for _ in range(steps):
        values = discount * (p * values[:-1] + (1.0 - p) * values[1:])

    return float(values[0])


def _intrinsic(S: float, K: float, is_call: bool) -> float:
    if is_call:
        return max(S - K, 0.0)
    return max(K - S, 0.0)


def binomial_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    steps: int = DEFAULT_STEPS,
    q: float = 0.0,
) -> float:
    """Price a European call under the CRR binomial tree."""
    return _crr_price(S, K, T, r, sigma, steps, is_call=True, q=q)


def binomial_put(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    steps: int = DEFAULT_STEPS,
    q: float = 0.0,
) -> float:
    """Price a European put under the CRR binomial tree."""
    return _crr_price(S, K, T, r, sigma, steps, is_call=False, q=q)
