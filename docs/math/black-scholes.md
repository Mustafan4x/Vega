# Black Scholes pricing for Trader

## Scope

This document fixes the mathematical model and the numerical conventions used by the project's pricing core. It is the canonical reference for any agent working on `app.pricing.black_scholes` and any downstream module that consumes its outputs (Greeks, heat map, P&L, persistence, backtest).

The model implemented in v1 is the standard Black Scholes formula for European call and put options on a non dividend paying underlying. Dividend yield is not modeled in v1; see `docs/future-ideas.md` for the deferred plan.

## The formula

For a European option on a non dividend paying stock:

```
C = S * N(d1) - K * exp(-r * T) * N(d2)
P = K * exp(-r * T) * N(-d2) - S * N(-d1)
```

where

```
d1 = ( ln(S / K) + (r + 0.5 * sigma^2) * T ) / ( sigma * sqrt(T) )
d2 = d1 - sigma * sqrt(T)
```

and `N(x)` is the cumulative distribution function of the standard normal distribution:

```
N(x) = 0.5 * ( 1 + erf( x / sqrt(2) ) )
```

In Python, `N(x)` is computed as `0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))`. This avoids any external dependency for the core calculator.

## Inputs and valid ranges

The five inputs and their valid ranges:

| Symbol | Meaning | Type | Valid range |
|---|---|---|---|
| `S` | Spot price of the underlying | float | `S > 0` (with documented behavior at `S = 0`) |
| `K` | Strike price | float | `K > 0` |
| `T` | Time to expiry, in years | float | `T >= 0` |
| `r` | Risk free rate, continuously compounded, decimal | float | typical sanity band `[-0.10, 0.20]`; the function does not enforce a band |
| `sigma` | Volatility of the underlying, annualized standard deviation, decimal | float | `sigma >= 0` |

The function rejects `S < 0`, `K < 0`, `T < 0`, or `sigma < 0` with `ValueError` at module entry. `K = 0` is also rejected since the formula divides by `K` inside `ln(S/K)`. `r` is unconstrained mathematically (negative real rates are valid).

## Project conventions (locked for v1)

These are the project wide conventions. The Risk and Financial Correctness Reviewer mirrors the same conventions in `docs/risk/conventions.md`. If there is any drift between the two files, the PM reconciles.

1. **Time `T` is in years.** `T = 0.25` means three calendar months. `T = 1.0` means one calendar year.
2. **Day count is calendar (365 days per year).** When the API or UI translates a calendar date to `T`, it uses `T = (expiry_date - today) / 365.0`. Trading day counts (252) and ACT/360 are NOT used in v1.
3. **Continuous compounding.** The risk free rate `r` is the continuously compounded rate. A bond yield quoted under any other convention must be converted before being passed in.
4. **`sigma` is decimal, annualized.** `sigma = 0.20` means 20 percent annualized volatility. The UI accepts a percent value for ergonomic reasons but converts to decimal at the API boundary.
5. **`r` is decimal.** `r = 0.05` means 5 percent. Same percent to decimal convention applies at the API boundary.
6. **No dividends in v1.** The non dividend paying stock formula is used. Dividend yield `q` is a future addition.
7. **European exercise only.** Black Scholes assumes European exercise. American style early exercise is not modeled here; a future binomial tree model handles it.
8. **No bid/ask, no transaction costs, no taxes.** Single price output.

## Function signatures

```python
def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float: ...
def black_scholes_put(S: float, K: float, T: float, r: float, sigma: float) -> float: ...
```

Both live in `app.pricing.black_scholes`. Inputs are positional or keyword. Output is a single float price in the same currency unit as `S` and `K`. Both functions raise `ValueError` on negative inputs (`S`, `K`, `T`, or `sigma` strictly less than zero, and `K` equal to zero).

## Edge case behavior

The implementation handles the following edge cases without falling into `log(0)`, division by zero, or `inf` arithmetic.

### `T == 0` (expiry)

Return the intrinsic value:

```
C = max(S - K, 0)
P = max(K - S, 0)
```

This matches the limit of the formula as `T -> 0+` and is the value the option is worth the instant before expiry.

### `sigma == 0` (deterministic forward)

The underlying is deterministic; its forward price at expiry is `F = S * exp(r * T)`. The option payoff is the discounted intrinsic of the forward:

```
C = exp(-r * T) * max(F - K, 0) = max(S - K * exp(-r * T), 0)
P = exp(-r * T) * max(K - F, 0) = max(K * exp(-r * T) - S, 0)
```

This is the closed form limit of the Black Scholes formula as `sigma -> 0+`.

### `S == 0`

A worthless underlying makes the call worthless and the put worth the discounted strike:

```
C = 0
P = K * exp(-r * T)
```

Although `S = 0` is on the boundary of the input domain, it is a useful limit case (e.g., a defaulted issuer) and the formula above is the closed form limit as `S -> 0+`.

### Very small `sigma` (numerical stability)

`sigma` values down to `1e-8` are handled by branching to the deterministic forward path when `sigma` is at or below a small threshold, OR by the formula directly with care that `sigma * sqrt(T)` does not underflow. The chosen approach is implementation detail; the test suite asserts numerical stability either way.

### Very large `sigma` (no overflow)

`sigma` values up to `5.0` (500 percent) are handled without overflow. `N(d1)` and `N(d2)` are bounded on `[0, 1]`, so the discounted strike term and the spot term are both finite. Tests assert finite output for `sigma = 5.0`.

### Deep ITM and deep OTM

Deep in the money: `S = 1000, K = 100`. Deep out of the money: `S = 1, K = 100`. Tests assert finite output, no NaN, and intuitive bounds (ITM call near `S - K * exp(-r * T)`, OTM call near zero).

### Negative inputs

`S < 0`, `K < 0`, `T < 0`, or `sigma < 0` raise `ValueError` with a message naming the offending parameter. `K = 0` also raises (formula undefined at strike zero). `r < 0` is allowed (real world negative rates).

## Put call parity (sanity invariant)

For the same `S, K, T, r` and any `sigma`:

```
C - P = S - K * exp(-r * T)
```

The test suite verifies this invariant within `1e-9` for at least three diverse parameter sets. Any implementation that does not satisfy parity is wrong.

## Reference values used in the test suite

The reference values in `backend/tests/pricing/test_black_scholes_math.py` are sourced from the following texts. Each test docstring cites its source.

* John C. Hull, *Options, Futures and Other Derivatives*, 10th edition, Chapter 15 (Black Scholes Merton model). Example 15.6 (`S = 42, K = 40, r = 0.10, sigma = 0.20, T = 0.5` gives `C = 4.7594, P = 0.8086`) and Practice Problem 15.13 (`S = 52, K = 50, r = 0.12, sigma = 0.30, T = 0.25`).
* Sheldon Natenberg, *Option Volatility and Pricing*, 2nd edition, Chapter 6 (theoretical pricing model). The textbook prices canonical ATM, ITM, and OTM cases on `S = 100`.
* Paul Wilmott, *Paul Wilmott Introduces Quantitative Finance*, 2nd edition, Chapter 8. The canonical `S = 100, K = 100, r = 0.05, sigma = 0.20, T = 1` benchmark (`C = 10.4506, P = 5.5735`) appears in many sources and matches the closed form to better than `1e-4`.

Where a reference value is computed from the closed form (e.g., `S = 0` boundary, `sigma = 0` deterministic forward), the docstring labels it as derived from the closed form in this document rather than from a textbook page.

## Tolerances

* Reference value tests: absolute tolerance `1e-4` (four decimal places). Textbook values are typically printed to four decimal places.
* Put call parity: absolute tolerance `1e-9`.
* Property based tests (added in Phase 7): tolerances vary; documented per test.

## Testing strategy

Phase 1 ships pure unit tests on `black_scholes_call` and `black_scholes_put`. Phase 7 adds:

1. Greeks tests (delta, gamma, theta, vega, rho) with reference values.
2. Property based tests using `hypothesis` for monotonicity.
3. Numerical Greeks via finite differences of the price function as a cross check.

## Out of scope for v1

The following are explicitly NOT implemented in v1 and are tracked in `docs/future-ideas.md`:

* Dividend yield `q` (continuous or discrete).
* American exercise.
* Implied volatility solver.
* Volatility surface.
* Stochastic volatility models.
* Local volatility models.
* Jump diffusion.
