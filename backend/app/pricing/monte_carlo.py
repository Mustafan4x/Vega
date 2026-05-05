"""Monte Carlo pricer for European options under geometric Brownian motion.

Reference: Glasserman, *Monte Carlo Methods in Financial Engineering*,
Chs. 3 (random number generation, antithetic variates) and 4 (option
pricing).

Under GBM the terminal asset price is
``S_T = S_0 * exp((r - sigma^2 / 2) * T + sigma * sqrt(T) * Z)``
for ``Z ~ N(0, 1)``. The discounted expectation of the payoff is the
arbitrage free price.

Antithetic variates (pairing each ``Z`` with ``-Z``) cut the standard
error roughly in half for symmetric payoffs without changing the
expectation. The pricer always uses an even path count (rounded up
internally) so antithetic pairing is exact.

Pure module: numpy plus stdlib only, no I/O. Determinism is sealed by
``numpy.random.default_rng(seed)``; tests pin expected values with a
seed.

Edge cases mirror ``app.pricing.black_scholes`` and
``app.pricing.binomial`` so a model swap at the API boundary does not
surprise the user:

* ``T == 0`` returns the intrinsic payoff.
* ``sigma == 0`` returns the deterministic discounted payoff.
* ``S == 0`` returns 0 for the call, ``K * exp(-rT)`` for the put.
"""

from __future__ import annotations

import math

import numpy as np

DEFAULT_PATHS = 100_000


def _validate(S: float, K: float, T: float, sigma: float, paths: int) -> None:
    if S < 0:
        raise ValueError(f"S must be non negative, got S={S}")
    if K <= 0:
        raise ValueError(f"K must be strictly positive, got K={K}")
    if T < 0:
        raise ValueError(f"T must be non negative, got T={T}")
    if sigma < 0:
        raise ValueError(f"sigma must be non negative, got sigma={sigma}")
    if paths <= 0:
        raise ValueError(f"paths must be strictly positive, got paths={paths}")


def _mc_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    paths: int,
    seed: int | None,
    is_call: bool,
    q: float = 0.0,
) -> float:
    _validate(S, K, T, sigma, paths)

    if T == 0.0:
        return _intrinsic(S, K, is_call)

    if S == 0.0:
        return 0.0 if is_call else K * math.exp(-r * T)

    if sigma <= 1e-12:
        forward = S * math.exp((r - q) * T)
        intrinsic = forward - K if is_call else K - forward
        return max(intrinsic, 0.0) * math.exp(-r * T)

    # Round up to an even path count so antithetic pairing is exact.
    half = (paths + 1) // 2
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(half)
    z_full = np.concatenate([z, -z])

    drift = (r - q - 0.5 * sigma * sigma) * T
    diffusion = sigma * math.sqrt(T)
    s_t = S * np.exp(drift + diffusion * z_full)

    payoff = np.maximum(s_t - K, 0.0) if is_call else np.maximum(K - s_t, 0.0)
    discounted = math.exp(-r * T) * float(np.mean(payoff))
    return discounted


def _intrinsic(S: float, K: float, is_call: bool) -> float:
    if is_call:
        return max(S - K, 0.0)
    return max(K - S, 0.0)


def monte_carlo_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    paths: int = DEFAULT_PATHS,
    seed: int | None = None,
    q: float = 0.0,
) -> float:
    """Price a European call by Monte Carlo (GBM, antithetic variates)."""
    return _mc_price(S, K, T, r, sigma, paths, seed, is_call=True, q=q)


def monte_carlo_put(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    paths: int = DEFAULT_PATHS,
    seed: int | None = None,
    q: float = 0.0,
) -> float:
    """Price a European put by Monte Carlo (GBM, antithetic variates)."""
    return _mc_price(S, K, T, r, sigma, paths, seed, is_call=False, q=q)
