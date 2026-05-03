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

## Cross references

* `docs/math/black-scholes.md`: the Quant Domain Validator's formula and derivation reference. The conventions in this file must agree with that one.
* `docs/risk/sanity-cases.md`: hand calculated reference cases that the pricing module must reproduce to two decimal places.
* `docs/future-ideas.md`: where the dividend yield extension will be captured if added.
