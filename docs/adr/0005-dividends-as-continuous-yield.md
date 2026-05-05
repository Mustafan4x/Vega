# ADR 0005: Dividends modeled as a continuous yield

## Status

Accepted, 2026-05-05.

## Context

The v1 build assumed European options on a non dividend paying stock. Pricing AAPL or any other dividend paying ticker therefore disagreed with market quotes by a meaningful amount. The next step is to support dividends without significantly expanding the math surface or the test reference set.

Two modeling choices were considered:

1. **Continuous dividend yield `q`** (Merton 1973 generalization of Black Scholes). One scalar parameter; the math substitution is `S → S * exp(-q * T)` in the option price and `(r - q)` in the d1 numerator. The closed form remains valid, and the binomial CRR tree and the Monte Carlo pricer take the same one line drift change. Documented in Hull, Wilmott, and Natenberg.
2. **Discrete dividends with ex dividend dates.** Re prices the underlying around each ex dividend date with a downward jump equal to the cash dividend. Requires an event driven re pricing loop, a per ticker dividend timeline, and bigger changes to the binomial and Monte Carlo paths.

A third question was whether to expose the dividend Greek (`psi`, the analytical derivative of option value with respect to `q`). Two paths: skip it, or compute and display it as a sixth row in the Greeks panel.

A fourth question was whether to auto fill `q` from yfinance's `dividendYield` when a ticker is selected.

## Decision

* Adopt the continuous dividend yield `q` as a first class input across all three pricers (Black Scholes scalar and vectorized, binomial CRR, Monte Carlo), all four endpoints (`/api/price`, `/api/heatmap`, `/api/calculations`, `/api/backtest`), the persistence schema (with backfill of existing rows to `q = 0`), and every frontend form that takes pricing inputs.
* Compute `psi` analytically and display it as a sixth row in the Greeks panel (per 1 percent q, mirroring the existing `vega_per_pct` and `rho_per_pct` convention). Add a sixth `rose` accent token to the design palette so the panel has a distinct visual marker for psi.
* Do NOT auto fill `q` from yfinance. The `dividendYield` field is occasionally null and reflects trailing rather than expected forward yield. A deferred entry in the maintainer's private notes captures this for revisit.
* Default `q = 0.0` everywhere preserves v1 behavior bit for bit when the field is omitted. Existing test fixtures continue to pass without modification; existing saved calculations are backfilled to `q = 0.0` with a server default in the Alembic migration (no truncation).

## Consequences

* The math docs gain a continuous yield section (`docs/math/black-scholes.md`); the conventions doc updates the dividend assumption (`docs/risk/conventions.md`); the api doc shows `q` and `psi_per_pct` on every relevant endpoint (`docs/api.md`).
* The persistence schema gains a `q` column with `nullable=False` and `server_default '0.0'`; the migration is reversible (`upgrade` adds the column, `downgrade` drops it via `batch_alter_table` for SQLite compatibility).
* The Pricing screen now has six inputs and the Greeks panel has six rows, pushing harder against the deferred "Pricing screen fits without scrolling" entry in the maintainer's private notes but not addressing it.
* The put call parity identity used in tests and reviews becomes `C - P = S * exp(-q * T) - K * exp(-r * T)` (reduces to the original identity when `q = 0`).
* Adding discrete dividends later remains possible: a separate `discrete_dividends: list[(date, amount)]` field could be added without breaking the existing API surface.
* The Risk and Financial Correctness Reviewer signed off this change per `SPEC.md` coordination rule 5.
