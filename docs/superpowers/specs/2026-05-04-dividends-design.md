# Continuous dividend yield (q) across the pricer

**Date**: 2026-05-04. **Status**: design approved, ready for implementation plan. **Owner of merge gate**: Risk and Financial Correctness Reviewer (per `SPEC.md` coordination rule 5).

## Summary

Add a continuous dividend yield parameter `q` as a first-class input across all three pricers (Black Scholes closed form, Cox Ross Rubinstein binomial tree, Monte Carlo with antithetic variates), all four pricing endpoints (`/api/price`, `/api/heatmap`, `/api/calculations`, `/api/backtest`), the persistence schema, and every frontend form that accepts pricing inputs. Default is `q = 0.0` everywhere so all v1 behavior is preserved bit-for-bit when the field is omitted.

A sixth Greek, `psi` (the analytical derivative of option value with respect to `q`), is computed by the math layer for both call and put, exposed in the `/api/price` response, and rendered as a sixth row in the frontend Greeks panel.

The dividend yield is NOT auto-filled from the ticker autocomplete (yfinance `dividendYield` is occasionally null and reflects trailing rather than expected forward yield; auto-filling a sometimes-wrong value is worse than asking the user). A new deferred entry is added to `future-ideas.md` to revisit auto-fill later.

## Motivation

The original v1 scope assumed European options on a non-dividend-paying stock to keep the math docs, the test reference values (Hull, Wilmott, Natenberg), and the Pydantic input model small and exact. With the project shipped and live at `vega-2rd.pages.dev`, the next visible gap is that pricing AAPL or any other dividend-paying stock disagrees with market quotes by a meaningful amount. Adding `q` closes that gap and is the smallest change with the largest demo-quality payoff.

## Non-goals

- **Discrete dividends**: out of scope. The continuous-yield approximation is the textbook generalization documented across Hull, Wilmott, and Natenberg, and is what real desks use as a first-pass model. Discrete dividends require an event-driven re-pricing loop that is not justified by the demo.
- **Dividend-yield auto-fill from yfinance**: deferred to a follow-up item in `future-ideas.md`.
- **Shocking `q` on the heatmap**: out of scope. The heatmap axes stay `(sigma, S)`. `q` is a constant scalar across all cells.
- **Surfacing a per-ticker dividend timeline in the backtest**: out of scope. The backtest takes `q` as a constant scalar across the replay window.
- **"Pricing screen fits without scrolling" layout work**: tracked separately in `future-ideas.md`. Adding `q` and `psi` does push harder against single-viewport rendering, but the layout fix stays its own ticket.

## Settled choices

| Choice | Selected | Why |
|---|---|---|
| Scope | Full surface (math, all four endpoints, persistence, all frontend forms) | Partial coverage would surface as inconsistent prices across screens, which reads as a bug to a viewer. |
| Greek for `q` | Add `psi` and display it (sixth panel row) | User selected option B during brainstorming. Makes the Greeks panel structurally complete. |
| Backtest semantics | Constant `q` across the replay window | Threading a real dividend timeline is a much larger feature; constant `q` matches the way `r` and `sigma` are already treated in the backtest. |
| Persistence migration strategy | Backfill existing rows with `q = 0.0` (no truncation) | The pre-migration rows were priced under the v1 assumption `q = 0`. Backfilling with 0 does not lie. Contrast with Phase 12, where `user_id` had no honest backfill. |
| Ticker autocomplete | Do NOT auto-fill `q` from yfinance | Trailing dividend yield is occasionally null and stale. Silent wrong-feeling auto-fill is worse than typing one number. |
| Validation range for `q` | `[-1.0, 1.0]` matching `r` | Negative `q` is meaningful for FX-style cost-of-carry differentials. Symmetric with `r` keeps the schemas uniform. |
| Greek name | `psi` (Hull convention) | Project's math docs already cite Hull. |
| Default value everywhere | `q = 0.0` | Preserves v1 behavior bit-for-bit when the field is omitted. Existing test fixtures continue to pass without modification. |
| API/UI unit convention | API decimal, UI percent, conversion at the form boundary | Identical to `r` and `sigma`. |
| Pricing-screen field placement | Immediately below `r`, suffix `%` | The two rates live together. |
| History summary card | Include `q` in `CalculationSummary` | Avoid lying about saved inputs in the list view. |

## Math layer changes

All four kernels in `backend/app/pricing/` gain a required `q: float` parameter on every public function. The validation helper `_validate_inputs` is extended to require `q` finite (range checking is at the API layer, not in the kernel; the kernel trusts validated inputs).

### Closed-form Black Scholes (`black_scholes.py`)

The substitution is `S → S * exp(-q*T)` in `d1` and `d2`, and the same factor multiplies the bare `S` term in the call/put price.

```
d1 = (ln(S/K) + (r - q + 0.5 * sigma^2) * T) / (sigma * sqrt(T))
d2 = d1 - sigma * sqrt(T)
call = S * exp(-q*T) * N(d1) - K * exp(-r*T) * N(d2)
put  = K * exp(-r*T) * N(-d2) - S * exp(-q*T) * N(-d1)
```

Edge-case branches keep the same shape:

- `T == 0`: `max(S - K, 0)` and `max(K - S, 0)` (`q` has no effect when `T = 0`).
- `S == 0`: `0` for the call, `K * exp(-r*T)` for the put (unchanged; `q` has no effect when `S = 0`).
- `sigma == 0` (deterministic): `max(S * exp(-q*T) - K * exp(-r*T), 0)` for the call, symmetric for the put.

### Greeks (`black_scholes.py`)

The `Greeks` dataclass gains `psi: float`. All five existing Greeks pick up the dividend factor where appropriate. Textbook units (math layer):

```
psi_call  = -T * S * exp(-q*T) * N(d1)
psi_put   =  T * S * exp(-q*T) * N(-d1)

delta_call = exp(-q*T) * N(d1)
delta_put  = exp(-q*T) * (N(d1) - 1)
gamma      = exp(-q*T) * N'(d1) / (S * sigma * sqrt(T))
vega       = S * exp(-q*T) * sqrt(T) * N'(d1)
theta_call = -S * exp(-q*T) * N'(d1) * sigma / (2 * sqrt(T))
             - r * K * exp(-r*T) * N(d2)
             + q * S * exp(-q*T) * N(d1)
theta_put  = -S * exp(-q*T) * N'(d1) * sigma / (2 * sqrt(T))
             + r * K * exp(-r*T) * N(-d2)
             - q * S * exp(-q*T) * N(-d1)
rho_call   =  T * K * exp(-r*T) * N(d2)    (unchanged)
rho_put    = -T * K * exp(-r*T) * N(-d2)   (unchanged)
```

Zero-greek branches (`T == 0`, `S == 0`, `sigma <= threshold`) return all zeros including `psi`.

### Vectorized Black Scholes (`black_scholes_vec.py`)

Same substitution applied with NumPy broadcasting. `q` is a scalar (the heatmap does not vary `q` across cells).

### Binomial CRR (`binomial.py`)

Up/down probability in the risk-neutral measure becomes:

```
p = (exp((r - q) * dt) - d) / (u - d)
```

Discount per step remains `exp(-r * dt)`. One-line change at the probability computation.

### Monte Carlo with antithetic variates (`monte_carlo.py`)

GBM step under the risk-neutral measure becomes:

```
S_T = S * exp((r - q - 0.5 * sigma^2) * T + sigma * sqrt(T) * Z)
```

One-line change at the drift term.

## API surface

Four request models gain `q`. All four use the identical Pydantic field, copying the existing `r` style:

```python
q: float = Field(
    default=0.0,
    ge=-1.0,
    le=1.0,
    allow_inf_nan=False,
    description="Continuous dividend yield (annualized, continuous).",
)
```

The `default=0.0` is load-bearing: it preserves backwards compatibility for any client that omits `q`, including every existing test fixture. The bound check rejects NaN, Infinity, and out-of-range values at the API edge before the kernel sees them.

### `POST /api/price`

- `PriceRequest` gains `q`.
- `_price_call_put` threads `q` to `black_scholes_call`, `black_scholes_put`, `binomial_call`, `binomial_put`, `monte_carlo_call`, `monte_carlo_put`.
- `black_scholes_call_greeks` and `black_scholes_put_greeks` are called with `q`.
- `GreeksDisplay` gains `psi_per_pct: float`.
- `_to_display` adds `psi_per_pct=g.psi * 0.01` (textbook units are per unit `q`; multiplying by 0.01 converts to per 1% q, matching the existing `vega_per_pct` and `rho_per_pct` convention).

### `POST /api/heatmap`

- `HeatmapRequest` gains `q`.
- The three `_grid_*` helpers and `_grid_for_model` thread `q` to the underlying pricer.
- The heatmap does NOT shock `q`: `q` is constant across all cells (axes stay `sigma` and `S`).
- `HeatmapResponse` shape is unchanged (the response already echoes `sigma_axis` and `spot_axis`; there is no `q_axis` because there are no `q` shocks).

### `POST /api/calculations`

- The save path captures `q` from the request payload and writes it to the new `q` column on `calculation_inputs`.
- `CalculationDetail` and `CalculationSummary` gain `q: float`.
- The list and detail endpoints echo `q` so the frontend can render it in the history view.

### `POST /api/backtest`

- `BacktestPayload` (Pydantic) gains `q` with the standard field definition.
- `BacktestRequest` (dataclass) gains `q: float = 0.0`.
- `_validate` checks the `q` bound (`-1.0 <= q <= 1.0`).
- `_leg_value` signature gains `q` and passes it to `black_scholes_call` and `black_scholes_put`.
- `run_backtest` threads `q` through the entry-basis computation and every per-step revaluation in the replay loop.

### Cross-endpoint constraints

- The Greeks always come from the analytical Black Scholes formula, regardless of which pricer produced the call/put values. This is per `docs/risk/conventions.md` and does not change. `psi` is computed analytically alongside the other five.
- The "auto-fill `S` from ticker" path stays unchanged. `q` is not touched by ticker autocomplete.
- No new endpoint, no new path, no new auth surface.

## Persistence

### Schema change

`backend/app/db/models.py` adds one column to `CalculationInput`:

```python
q: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")
```

### Alembic migration

A new migration adds the `q` column with `nullable=False` and `server_default='0.0'`. The server default makes existing rows backfill atomically without a Python loop. The `server_default` stays in place after the migration (cheap, harmless) so future `INSERT` statements that omit `q` keep working at the DB layer.

No truncation. The pre-migration rows are preserved with `q = 0.0`, which is exactly the assumption under which they were priced.

### Read paths

`GET /api/calculations` (list) and `GET /api/calculations/{id}` (detail) include `q` in their responses.

### Privacy implications

None new. The row was already gated by `user_id` from Phase 12; adding a single float column does not change the access surface.

## Frontend

### `lib/api.ts`

The four request types (`PriceRequest`, `HeatmapRequest`, `BacktestRequest`, and the calculation save shape) gain `q?: number` (optional, decimal). The optional marker lets existing test fixtures omit `q`; the backend default fills in `0`.

The two response types (`PriceResponse.GreeksDisplay`, `CalculationDetail`, `CalculationSummary`) gain the relevant `q`-derived fields (`psi_per_pct` on `GreeksDisplay`; `q: number` on the calculation shapes).

### `components/InputForm.tsx`

A sixth `NumField` for `q`, immediately below the `r` field, mirroring the `r` field exactly:

- `label="Dividend Yield (q)"`
- `suffix="%"`
- `value={Number((inputs.q * 100).toFixed(3))}`
- `onChange={(v) => setField('q', v / 100)}`
- `invalid={invalid.has('q')}`

### `components/HeatMapControls.tsx` and `screens/HeatMapScreen.tsx`

Same `NumField` pattern. Place `q` in the same row as `r` if the existing layout has space; otherwise immediately below `r`.

### `components/BacktestForm.tsx`

Same `NumField` pattern, positioned next to the existing `r` input.

### `components/GreeksPanel.tsx`

A sixth row labeled `psi`, suffix `"per 1% q"`, value source `call_greeks.psi_per_pct` and `put_greeks.psi_per_pct`. Same display formatter as the existing five Greeks.

### `screens/HistoryScreen.tsx`

Both the summary card list and the detail view render `q` as a percent with one decimal place (suffix `%`), positioned next to `r`. Saved rows with `q == 0` render as `0.0%` rather than being hidden, so users comparing two saved calculations can see the field even when zero.

### `components/TickerAutocomplete.tsx`

Unchanged. Confirmed in the brainstorming session.

### Layout note

The Pricing screen now has six inputs and the Greeks panel has six rows. This pushes harder against the "Pricing screen fits without scrolling" idea in `future-ideas.md` but does not address it; that work stays a separate ticket.

## Tests

Backend, ordered by phase of TDD:

- **`backend/tests/pricing/test_black_scholes_math.py`**: a parameterized block of `q != 0` reference values. Source: Hull (the chapter currently cited by the file). Plan ~6 to 8 new cases covering ITM/ATM/OTM, T near zero, `q in {0.02, 0.05, -0.01}`. Existing `q == 0` cases pass unchanged because the kernels accept `q = 0` as the default-equivalent path. Update the parity-related cases that already live in this file so the new identity `C - P = S * exp(-q*T) - K * exp(-r*T)` is asserted.
- **`backend/tests/pricing/test_greeks.py`**: new reference values for `psi` (call and put) and updated reference values for the four Greeks that change shape under `q != 0` (`delta`, `gamma`, `vega`, `theta`). Update the existing `test_put_call_parity` cases (parametrize block) so the new identity `C - P = S * exp(-q*T) - K * exp(-r*T)` is asserted across at least four diverse `(S, K, T, r, sigma, q)` cases including `q != 0`. Hypothesis is not currently a project dependency; stay with `pytest.parametrize`.
- **`backend/tests/pricing/test_binomial.py`**: at least two `q != 0` cases asserting convergence to the closed-form BS value within tolerance.
- **`backend/tests/pricing/test_monte_carlo.py`**: at least two `q != 0` cases (with the project's existing seed convention) asserting convergence to the closed-form BS value within tolerance.
- **`backend/tests/pricing/test_black_scholes_vec.py`**: vectorized version returns identical results to scalar version under `q != 0`. Two or three new parametric cases.
- **`backend/tests/api/test_price.py`**, **`test_heatmap.py`**, **`test_calculations.py`**, **`test_backtest.py`**: validation tests for `q` (out of range rejected, NaN and Infinity rejected, default-zero accepted, omitted field accepted). One smoke test per endpoint with `q != 0` exercising the happy path. One existing test extended per file to assert `q` is echoed/persisted correctly.
- **`backend/tests/db/test_*` (new file or existing migration test)**: one test that runs the Alembic migration against a fixture DB seeded with a pre-migration row and asserts the row is preserved with `q == 0.0`.
- **`backend/tests/backtest/test_*`**: at least two `q != 0` cases (a long call and a covered call) showing the P&L curve differs as expected versus `q == 0`.

Frontend:

- **`frontend/src/components/InputForm.test.tsx`**: assert the `q` field renders, percent-to-decimal conversion works, invalid state surfaces.
- **`frontend/src/components/HeatMapControls.test.tsx`** and **`BacktestForm.test.tsx`**: same minimal coverage.
- **`frontend/src/components/GreeksPanel.test.tsx`**: assert the sixth row renders with the `psi` label and value formatting; cover both call and put.
- **`frontend/src/screens/HistoryScreen.test.tsx`**: assert `q` renders in the summary card and the detail view.
- API client tests: include `q` in the request body and assert it is passed through.

Risk Reviewer sign-off is required before merge per `SPEC.md` coordination rule 5.

## Docs

- **`docs/math/black-scholes.md`**: append a "Continuous dividend yield" section documenting the substitution, the modified call/put formulas, and the modified Greeks (with explicit formula for `psi`). Cite Hull chapter and page.
- **`docs/risk/conventions.md`**: replace the "dividends assumed zero in v1" line with a paragraph stating that continuous dividend yield `q` is a first-class input, default 0 preserves the original v1 semantics, and discrete-dividend modeling remains out of scope. Document the parity identity update.
- **`docs/api.md`**: add `q` to every endpoint's request schema; add `psi_per_pct` to the `GreeksDisplay` shape; add a brief paragraph noting `q = 0` is the default for backwards compatibility.
- **`docs/adr/0005-dividends-as-continuous-yield.md`**: a new ADR documenting the choice of continuous yield over discrete dividends, the choice to expose `psi`, and the choice not to auto-fill from yfinance.
- **`docs/setup-guide.md`**: no change.
- **`future-ideas.md`** (gitignored, repo root): replace the "Dividends in the pricing model" entry with a one-line note that it shipped, plus a NEW deferred entry "Auto-fill `q` from yfinance dividend yield" capturing the brainstorming-session reasoning (trailing vs forward yield, `dividendYield` occasionally null).

## Acceptance criteria

1. All four pricing endpoints accept `q` as an optional decimal field with default 0; out-of-range or non-finite `q` is rejected with a 422.
2. With `q == 0` and an otherwise unchanged payload, every endpoint returns identical numerical results to pre-feature behavior (regression test against frozen reference values).
3. With `q != 0`, the closed-form Black Scholes price matches the published Hull reference values within 1e-6.
4. With `q != 0`, the binomial and Monte Carlo prices converge to the closed-form Black Scholes price within the project's existing convergence tolerances.
5. Put-call parity holds with the new identity `C - P = S * exp(-q*T) - K * exp(-r*T)` within 1e-9 across at least four parametrized cases including `q != 0`.
6. The Greeks panel renders six rows for both call and put; `psi` renders in the units `per 1% q`.
7. The Alembic migration adds the `q` column with `NOT NULL` and `server_default '0.0'`; existing rows are preserved with `q == 0.0`.
8. The history summary card and detail view render `q` as a percent (suffix `%`) for every saved calculation, including those backfilled from before the migration.
9. The Pricing, Heatmap, and Backtest forms each include a `q` input field positioned per the design (below or next to `r`).
10. Risk and Financial Correctness Reviewer signs off; Code Reviewer signs off; backend pytest, ruff, and mypy are clean; frontend test, lint, tsc, and build are clean; pip-audit and pnpm audit are clean.

## Out of scope (explicit)

- Discrete dividends.
- Dividend-yield auto-fill from yfinance (deferred to `future-ideas.md`).
- Heatmap shocks on `q`.
- A per-ticker dividend timeline in the backtest (constant `q` across the replay only).
- Pricing-screen layout work to fit the new field without scrolling (separate ticket in `future-ideas.md`).
