# Finance conventions for the Trader project

This document is the canonical reference for the financial conventions used throughout the Trader pricing service. Every agent that touches pricing math, P&L, or the user facing input form must follow these conventions exactly. Disagreements are resolved by the Risk Reviewer in coordination with the Quant Domain Validator before code lands.

The conventions here track the textbook Black Scholes model on a non dividend paying stock. They are deliberately conservative and standard so that hand calculations from any options textbook reproduce the service's outputs to two decimal places.

## Day count convention

**365 calendar days per year.** Time fractions are computed as (calendar days to expiry) divided by 365.

Examples:
* Six months to expiry: T = 182.5 / 365 = 0.5.
* One year to expiry: T = 365 / 365 = 1.0.
* Thirty days to expiry: T = 30 / 365 ≈ 0.08219.

Why 365 and not ACT/365 or ACT/360 or business day counts: this is a pet project, not a trading desk. Real desks pick the convention that matches the funding currency (ACT/360 for USD money market, ACT/365 for GBP, business day counts for some exchange traded products). The Trader project does not need that distinction. Picking 365 calendar days keeps every computation reproducible from a wall clock and avoids a dependency on a holiday calendar. If a future phase introduces multi currency support or trading day discounting, this decision is revisited and recorded as an ADR.

## Dividends

**Assumed zero in v1.** The pricing module computes prices under the textbook no dividend assumption. The user facing form does not collect a dividend yield. The backend does not compute or persist a dividend value. Greeks are computed under the same no dividend assumption.

**Greeks at the deterministic limits.** When `T = 0`, `sigma = 0`, or `S = 0`, the closed form Greeks are not well defined (delta is a step function in those limits, gamma and vega blow up or vanish). The implementation returns zero for all five Greeks at these inputs by design. The price functions still return the correct deterministic forward intrinsic at those inputs (e.g., `max(S - K, 0)` at `T = 0`); only the Greeks short circuit. A user who needs sensitivity at these limits should perturb the inputs slightly and inspect the resulting Greeks numerically.

This is an explicit modeling choice, not a bug. It is the simplest assumption that lets the whole project ship and is consistent with the source video transcript.

If a future phase adds dividends, the change is captured as a new entry in `docs/future-ideas.md` and surfaces as an ADR. The expected route is to add a `q` field (continuous dividend yield) to the request payload, switch to the Black Scholes Merton form (multiply S by exp(-qT) inside the d1 numerator and the call value), and update both the conventions doc and the sanity cases.

## Volatility convention

**Annualized standard deviation, expressed as a decimal.**

* sigma = 0.20 means 20 percent annualized volatility.
* sigma = 1.00 means 100 percent annualized volatility (typical for highly volatile single names or short dated crypto).
* sigma = 0.05 means 5 percent annualized volatility (typical for index futures over a short window).

The pricing module accepts sigma as a decimal float. It does not accept percent. The frontend form accepts percent as a UI affordance and divides by 100 before sending. See "UI input units" below.

## Risk free rate convention

**Continuously compounded, expressed as a decimal.**

* r = 0.05 means a 5 percent continuously compounded annual rate.
* r = 0.00 is permitted and represents a zero rate environment.
* r is allowed to be negative (some currencies have had negative rates); the math still works.

The pricing module accepts r as a decimal float. Discounting uses exp(-rT). The frontend form accepts percent as a UI affordance and divides by 100 before sending. See "UI input units" below.

If a user supplies an annually compounded rate r_annual instead of the continuously compounded rate, the conversion is r = ln(1 + r_annual). The form does not perform this conversion; the user is expected to enter a continuously compounded rate. The form's help text must say "continuously compounded" to remove ambiguity.

## Expiry semantics

**T is in years and must be a non negative finite float.**

* T = 0 means at expiry. The pricing module returns intrinsic value: call = max(S minus K, 0); put = max(K minus S, 0).
* T = 1 means one year out.
* T = 0.5 means six months out under the 365 day convention.
* T must satisfy T greater than or equal to 0. The backend rejects negative T with a 422 validation error.
* T has no hard upper bound in the math, but the API enforces a reasonable cap (e.g., T less than or equal to 100 years) to prevent unreasonable inputs and to keep numerical behavior bounded.

Edge cases for T = 0 are tested explicitly. See `docs/risk/sanity-cases.md` for the at expiry scenarios.

## UI input units (Phase 3 anticipates this)

The React form will collect volatility and rate as **percent values** because that is what users type and what every options textbook displays. The Frontend Developer is responsible for the conversion to decimal before the API call.

| UI field | UI display | UI value | Conversion before POST | Backend field |
|---|---|---|---|---|
| Volatility | "20" with a percent suffix | number 20 | divide by 100 | `sigma`, decimal 0.20 |
| Risk free rate | "5" with a percent suffix | number 5 | divide by 100 | `r`, decimal 0.05 |
| Spot price | "100" with currency prefix | number 100 | none | `S`, decimal 100.00 |
| Strike price | "100" with currency prefix | number 100 | none | `K`, decimal 100.00 |
| Time to expiry | "1" with year suffix, or a date picker | number 1.0 (or computed days / 365) | none if already in years | `T`, decimal 1.0 |

The conversion is a single division by 100 in the API client layer of the frontend. It must be covered by a unit test that asserts: input "20" arrives at the backend as `0.20`. This eliminates the most common bug class (sigma off by a factor of 100) before it can ship.

The backend Pydantic model rejects values that look like percent (e.g., sigma greater than 5.0 with a warning, since 500 percent annualized vol is implausible) but does not silently rescale. Silent rescaling is forbidden because it hides the unit mismatch.

## Sign conventions for P&L (Phase 5 anticipates this)

P&L is always reported from the **owner's perspective** and is defined as **current value minus purchase price** for a long position.

Long call P&L:
* P&L = current call value minus call purchase price.
* At expiry, current call value = max(S minus K, 0).
* Profit when current value greater than purchase price; loss when lower.

Long put P&L:
* P&L = current put value minus put purchase price.
* At expiry, current put value = max(K minus S, 0).

Short positions invert the sign: short call P&L = call purchase price minus current call value. Short positions are not in scope for v1 and not displayed in the heat map.

Heat map color convention (anticipates Phase 5):
* Positive P&L is colored on the green side of the scale.
* Negative P&L is colored on the red side of the scale.
* The mid color (zero P&L) sits at the breakeven point. The breakeven for a long call is the strike plus the call purchase price; for a long put, the strike minus the put purchase price.

A higher purchase price moves the breakeven outward (further from at the money) and therefore shifts the green region of the heat map outward. The Risk Reviewer hand checks this in Phase 5.

## Symbol reference

To keep notation consistent with the sanity cases doc and the pricing module:

| Symbol | Meaning | Units |
|---|---|---|
| S | Spot price of the underlying | currency |
| K | Strike price | currency |
| T | Time to expiry | years (decimal) |
| r | Continuously compounded risk free rate | decimal (0.05 means 5 percent) |
| sigma | Annualized standard deviation of returns | decimal (0.20 means 20 percent) |
| N(x) | Standard normal cumulative distribution function | dimensionless, in [0, 1] |
| d1, d2 | Black Scholes intermediate quantities | dimensionless |
| C | Call price | currency |
| P | Put price | currency |

## Pricing model selection and Greeks convention (Phase 9)

The Trader service exposes three pricing models on the price and heatmap endpoints, selected by the `model` field: `black_scholes` (closed form), `binomial` (Cox Ross Rubinstein tree), and `monte_carlo` (geometric Brownian motion with antithetic variates). The choice affects the call and put values; **Greeks are always returned from the closed form Black Scholes formula regardless of the chosen pricer.** This matches market practice: dealers quote vanilla Greeks off the closed form even when their internal book runs a tree, a PDE solver, or a stochastic vol Monte Carlo. For European vanilla on a non dividend stock, the three pricers target the same underlying GBM dynamics, so the Black Scholes Greeks are the correct sensitivities of the contract the user is pricing.

**Tolerances for sign off** (canonical centered inputs S=K=100, T=1, r=0.05, sigma=0.20):

* Binomial CRR at 500 steps: absolute error against the closed form < 0.05 dollar.
* Monte Carlo at 100k paths with antithetic variates and a fixed seed: absolute error against the closed form < 0.10 dollar.

**Determinism for UI stability.** The price endpoint pins a deterministic Monte Carlo seed (`_MC_SEED = 4242` in `app/api/price.py`) so the same request payload returns the same number under repeat. This makes the result stable while the user is typing. The heatmap endpoint uses a per cell seed (`base + i * 21 + j`) so the grid is stable under repeat without making neighboring cells correlated; numpy's `default_rng` (PCG64) decorrelates well across adjacent seeds.

**Reduced parameters for the heatmap path.** The heatmap endpoint runs binomial at 100 steps and Monte Carlo at 20k paths per cell, lower than the price endpoint's 500 / 100k. This is acceptable because the heatmap is a visualization (the user reads color, not the exact dollar) and the per cell budget in a 21 by 21 grid is 50x tighter than the per request budget at `/api/price`.

**Numerical safety fallbacks.** When the binomial tree's risk neutral probability `p = (exp(r * dt) - d) / (u - d)` falls outside `(0, 1)` due to extreme inputs (very low sigma combined with high `|r|` over a long horizon), the binomial pricer falls back to the deterministic discounted forward, which is the correct sigma-collapses-to-zero limit. The Monte Carlo pricer rounds odd path counts up to the next even number so antithetic pairing is exact; this preserves the unbiased estimator property. Both fallbacks are intentional and tested.

## Backtest engine assumptions (Phase 10)

The backtest engine in `backend/app/backtest/engine.py` makes a small set of explicit simplifications so the curve it produces is unambiguous and reproducible. Each assumption is documented below; future enhancements (per leg IV, intraday marking, multi-strike spreads, short legs) will require extending one or more of these conventions.

* **Strike at entry spot (ATM at entry).** The engine sets the strike equal to the entry day's close, so every backtested trade is exactly at the money on entry. The entry premium is therefore pure time value; intrinsic at entry is zero by construction. The `strike` field in the response reports this value.

* **Constant implied vol over the life of the trade.** The user supplied `sigma` is interpreted as the implied vol the position was opened against and is held constant for every daily mark. The engine does not observe realized vol from the close series and does not refresh the IV surface day to day. This is a v1 simplification; a future enhancement would mark each day at that day's actual IV.

* **Close to close marking.** The position is marked once per day at the close. The P&L curve is therefore close to close; intraday excursions are not visible.

* **Calendar day expiry.** The expiry date is computed as `entry_date + timedelta(days=dte_days)` and is a calendar date, not a trading date. This is consistent with the project's 365 calendar day count convention. If the expiry falls on a non trading day, the engine marks the position on the last trading day in the series that falls on or before expiry; once the date is at or past expiry, `T = 0` and the BS formula collapses to the intrinsic payoff.

* **Long only basis sign.** Every v1 strategy is long only, so the entry basis is always positive (premium paid). The P&L formula `position_value - entry_basis` therefore reads naturally: positive P&L means the marked position has risen above the cost. When short legs are introduced (covered call, cash secured put, vertical credit spreads), the basis convention must extend so a net credit position records a negative basis and the same `position_value - entry_basis` formula continues to give a P&L that increases as the position becomes more profitable.

* **Daily mark uses the same closed form Black Scholes module as `/api/price`.** Sigma collapse to zero, T collapse to zero, and S collapse to zero all short circuit to the deterministic limits documented in the main conventions section.

## Cross references

* `docs/math/black-scholes.md`: the Quant Domain Validator's formula and derivation reference. The conventions in this file must agree with that one.
* `docs/risk/sanity-cases.md`: hand calculated reference cases that the pricing module must reproduce to two decimal places. Cases 6 and 7 cover model comparison and divergence regimes; Case 8 covers the backtest engine.
* `docs/future-ideas.md`: where the dividend yield extension will be captured if added.
