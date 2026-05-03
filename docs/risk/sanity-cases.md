# Black Scholes sanity cases

This document is the canonical set of hand calculated reference values for the Trader pricing service. The Backend Developer's pricing module must reproduce every price below to within one cent (two decimal places) when given the same inputs. The Quant Domain Validator's test suite uses these values directly.

All cases assume the textbook Black Scholes model on a non dividend paying stock, with the conventions documented in `docs/risk/conventions.md`:
* T in years.
* sigma annualized standard deviation, decimal.
* r continuously compounded, decimal.
* No dividends.
* Day count: 365 calendar days per year.

## Formulas in use

For each case, d1 and d2 are computed as:

```
d1 = ( ln(S / K) + (r + sigma^2 / 2) * T ) / ( sigma * sqrt(T) )
d2 = d1 - sigma * sqrt(T)
```

Call and put prices:

```
C = S * N(d1) - K * exp(-r * T) * N(d2)
P = K * exp(-r * T) * N(-d2) - S * N(-d1)
```

Put call parity (used as a cross check on every case):

```
C - P = S - K * exp(-r * T)
```

N(x) values used below come from a standard normal CDF table to five decimal places. For the negative arguments, N(-x) = 1 - N(x).

## Case 1: at the money, one year, base case

**Inputs**: S = 100, K = 100, T = 1.0, r = 0.05, sigma = 0.20.

Step by step:
* sigma * sqrt(T) = 0.20 * 1.0 = 0.20.
* ln(S / K) = ln(1) = 0.
* (r + sigma^2 / 2) * T = (0.05 + 0.02) * 1.0 = 0.07.
* d1 = (0 + 0.07) / 0.20 = 0.35.
* d2 = 0.35 - 0.20 = 0.15.
* N(0.35) = 0.63683.
* N(0.15) = 0.55962.
* exp(-r * T) = exp(-0.05) = 0.95123.
* C = 100 * 0.63683 - 100 * 0.95123 * 0.55962 = 63.683 - 53.232 = **10.45**.
* N(-0.35) = 0.36317.
* N(-0.15) = 0.44038.
* P = 100 * 0.95123 * 0.44038 - 100 * 0.36317 = 41.890 - 36.317 = **5.57**.
* Parity check: C - P = 4.88; S - K * exp(-r * T) = 100 - 95.123 = 4.88. Agrees.

**Expected prices**: C = 10.45, P = 5.57.

**Intuition checks**:
* Call delta is N(d1) = 0.64, which is greater than 0.5 because r is positive and the forward S * exp(rT) sits above K.
* Call price exceeds put price for the same reason (positive cost of carry).
* Both prices are well above intrinsic (which is zero here), as expected for at the money options with a year to run.

## Case 2: in the money call, out of the money put, six months

**Inputs**: S = 110, K = 100, T = 0.5, r = 0.05, sigma = 0.25.

Step by step:
* sigma * sqrt(T) = 0.25 * sqrt(0.5) = 0.25 * 0.70711 = 0.17678.
* ln(S / K) = ln(1.1) = 0.09531.
* (r + sigma^2 / 2) * T = (0.05 + 0.03125) * 0.5 = 0.040625.
* d1 = (0.09531 + 0.040625) / 0.17678 = 0.135935 / 0.17678 = 0.76896.
* d2 = 0.76896 - 0.17678 = 0.59218.
* N(0.769) = 0.77897.
* N(0.592) = 0.72313.
* exp(-r * T) = exp(-0.025) = 0.97531.
* C = 110 * 0.77897 - 100 * 0.97531 * 0.72313 = 85.687 - 70.527 = **15.16**.
* N(-0.769) = 0.22103.
* N(-0.592) = 0.27687.
* P = 100 * 0.97531 * 0.27687 - 110 * 0.22103 = 27.005 - 24.313 = **2.69**.
* Parity check: C - P = 12.47; S - K * exp(-r * T) = 110 - 97.531 = 12.47. Agrees.

**Expected prices**: C = 15.16, P = 2.69.

**Intuition checks**:
* Call delta is N(d1) = 0.78; a deep in the money call should have a delta well above 0.5 and trending toward 1, which it is.
* Intrinsic value of the call is S - K = 10.00; the call price 15.16 sits comfortably above intrinsic, with the difference being time value.
* Put price is small but nonzero, consistent with the put being out of the money but not far out.

## Case 3: out of the money call, in the money put, three months

**Inputs**: S = 90, K = 100, T = 0.25, r = 0.05, sigma = 0.30.

Step by step:
* sigma * sqrt(T) = 0.30 * 0.5 = 0.15.
* ln(S / K) = ln(0.9) = -0.10536.
* (r + sigma^2 / 2) * T = (0.05 + 0.045) * 0.25 = 0.02375.
* d1 = (-0.10536 + 0.02375) / 0.15 = -0.08161 / 0.15 = -0.54407.
* d2 = -0.54407 - 0.15 = -0.69407.
* N(-0.544) = 0.29314.
* N(-0.694) = 0.24380.
* exp(-r * T) = exp(-0.0125) = 0.98758.
* C = 90 * 0.29314 - 100 * 0.98758 * 0.24380 = 26.383 - 24.077 = **2.31**.
* N(0.544) = 0.70686.
* N(0.694) = 0.75620.
* P = 100 * 0.98758 * 0.75620 - 90 * 0.70686 = 74.682 - 63.617 = **11.06**.
* Parity check: C - P = -8.75; S - K * exp(-r * T) = 90 - 98.758 = -8.76. Agrees within rounding.

**Expected prices**: C = 2.31, P = 11.06.

**Intuition checks**:
* Call delta is N(d1) = 0.29; an out of the money call has a delta well below 0.5, trending toward 0 as it goes further out, which it is.
* Intrinsic value of the put is K - S = 10.00; the put price 11.06 sits just above intrinsic, with the small difference being time value.
* Call price is small and represents almost pure time value, since the call is out of the money and expiry is only three months away.

## Case 4: at expiry, T = 0 (intrinsic value)

This case confirms the pricing module returns intrinsic value when there is no time left.

### Case 4a: in the money call at expiry

**Inputs**: S = 110, K = 100, T = 0.0, r = 0.05, sigma = 0.20.

The Black Scholes formula degenerates at T = 0. The pricing module must handle this by short circuiting to intrinsic value:
* C = max(S - K, 0) = max(10, 0) = **10.00**.
* P = max(K - S, 0) = max(-10, 0) = **0.00**.

### Case 4b: out of the money call at expiry

**Inputs**: S = 90, K = 100, T = 0.0, r = 0.05, sigma = 0.20.

* C = max(S - K, 0) = max(-10, 0) = **0.00**.
* P = max(K - S, 0) = max(10, 0) = **10.00**.

**Intuition checks**:
* Neither r nor sigma should affect the price at T = 0; the only thing that matters is intrinsic value.
* The pricing module should not throw a divide by zero error when sigma * sqrt(T) is zero in the d1 denominator. Either short circuit on T = 0, or use a numerically safe convention (delta_call = 1 if S greater than K, else 0; delta_put = -1 if S less than K, else 0).

## Case 5: zero volatility, deterministic forward

This case confirms the pricing module returns the discounted intrinsic value of the forward when there is no uncertainty.

### Case 5a: forward above strike, sigma = 0

**Inputs**: S = 100, K = 100, T = 1.0, r = 0.05, sigma = 0.0.

With sigma = 0, the asset evolves deterministically: at expiry, S_T = S * exp(r * T) = 100 * exp(0.05) = 105.127. The call ends in the money by 5.127; the put ends worthless.
* C = (S * exp(r * T) - K) * exp(-r * T) = S - K * exp(-r * T) = 100 - 95.123 = **4.88**.
* P = max(K * exp(-r * T) - S, 0) = max(95.123 - 100, 0) = **0.00**.
* Parity check: C - P = 4.88; S - K * exp(-r * T) = 4.88. Agrees.

### Case 5b: forward below strike, sigma = 0

**Inputs**: S = 95, K = 100, T = 1.0, r = 0.05, sigma = 0.0.

Forward = 95 * exp(0.05) = 99.871, below the strike.
* C = max(S - K * exp(-r * T), 0) = max(95 - 95.123, 0) = **0.00**.
* P = (K - S * exp(r * T)) * exp(-r * T) = K * exp(-r * T) - S = 95.123 - 95 = **0.12**.
* Parity check: C - P = -0.12; S - K * exp(-r * T) = -0.12. Agrees.

**Intuition checks**:
* When sigma = 0 and the forward exceeds the strike, the call is worth exactly the discounted forward intrinsic and the put is worthless.
* When sigma = 0 and the forward is below the strike, the call is worthless and the put is worth the discounted forward intrinsic.
* As with T = 0, the pricing module must avoid a divide by zero at sigma = 0. Short circuit to the deterministic forward result, or handle it via a numerically safe limit.

### Case 6: cross model agreement at canonical Wilmott inputs

**Inputs**: S = 100, K = 100, T = 1.0, r = 0.05, sigma = 0.20.

All three pricers must agree on the call and put values to within the published tolerances:

| Model | Call | Put | Tolerance vs Black Scholes |
|---|---|---|---|
| Black Scholes (closed form) | 10.4506 | 5.5735 | reference |
| Binomial CRR, 500 steps | ~10.45 | ~5.57 | absolute < 0.05 |
| Monte Carlo, 100k paths, antithetic, seed=4242 | ~10.48 | ~5.60 | absolute < 0.10 |

Greeks are identical across the three models because they are always computed from the closed form Black Scholes formula. See `docs/risk/conventions.md` (pricing model selection and Greeks convention).

### Case 7: model divergence regime, deep OTM call near expiry

**Inputs**: S = 100, K = 120, T = 0.05, r = 0.05, sigma = 0.40.

This is the stress region where the three pricers' approximations are most visible to a user toggling models on the same trade ticket. The closed form gives a small price (around 0.05 to 0.15 dollar depending on rounding); binomial at 500 steps oscillates around the closed form by a few percent; Monte Carlo at 100k paths has relative error around 5 to 10 percent because the small absolute price amplifies the standard error. None of this is a correctness bug; it is the inherent convergence behavior of each method (binomial's O(1/n) with oscillation around the strike crossing, MC's O(1/sqrt(n)) standard error growing with payoff variance).

The convention is: when the user picks a non Black Scholes model on a deep OTM near expiry input, expect a visibly different number, and treat the closed form as the reference if a single number is required.

## Tolerance

The pricing module must reproduce all expected prices in this document (Cases 1 to 5b) to within one cent (absolute tolerance of 0.01). This tolerance accommodates rounding in the N(x) lookups and the small differences between table values and high precision floating point.

The Quant Domain Validator's test suite asserts these tolerances explicitly. Any drift beyond one cent is treated as a regression and blocks the phase.

For the Phase 9 multi model cases (6 and 7) the tolerance widens to the per model bounds in Case 6.

## Cross references

* `docs/risk/conventions.md`: the conventions every input here is expressed in.
* `docs/math/black-scholes.md`: the Quant Domain Validator's formula derivation. The values here must reconcile with that document.
