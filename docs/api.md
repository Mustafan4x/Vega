# Trader API

Reference for the FastAPI service that powers the Trader frontend. Generated from the FastAPI OpenAPI schema at `/openapi.json` (development only) and edited for readability. The live OpenAPI document is the authoritative source; this page summarizes the surface for humans.

## Base URL

| Environment | URL |
|---|---|
| Local dev | `http://localhost:8000` |
| Production | `https://trader-backend.onrender.com` (set by Render at first deploy) |

## Authentication

None for v1. Every endpoint is public. The frontend talks to the backend with `credentials: 'omit'` and the backend's CORS allow list is restricted to the configured frontend origin.

## Content type

All request and response bodies are JSON. Send `Content-Type: application/json`. Responses set `Content-Type: application/json; charset=utf-8`.

## Rate limits

Two layers of limits:

| Layer | Default | Header on 429 |
|---|---|---|
| Application wide (per IP, across all endpoints) | `60/minute` | `Retry-After` |
| Per route, on the heaviest endpoints | see table below | `Retry-After` |

| Endpoint | Per route limit | Reason |
|---|---|---|
| `POST /api/price` | inherits global | Cheap closed form math; ~1 ms server cost. |
| `POST /api/heatmap` | `12/minute` | Heaviest pure compute; up to 441 cell prices on the binomial / Monte Carlo paths. |
| `POST /api/calculations` | inherits global | Same compute as `/api/heatmap` plus a DB write of `rows * cols` rows. |
| `GET  /api/calculations/{id}` | inherits global | Single indexed read. |
| `GET  /api/tickers/{symbol}` | `30/minute` | Each cache miss issues a yfinance call. |
| `POST /api/backtest` | `10/minute` | Up to 5 years of daily prices fetched plus engine run. |

429 response body: `{"detail":"Rate limit exceeded."}`.

## Error response shape

| Status | Shape | When |
|---|---|---|
| `400` | `{"detail":"<message>"}` | Malformed request (rare; FastAPI handles most as 422). |
| `404` | `{"detail":"<message>"}` | Unknown calculation id, unknown ticker. |
| `413` | `{"detail":"Request body too large."}` | Content-Length exceeds 32 KB. |
| `422` | `{"detail":[{loc, msg, type}, ...]}` | Pydantic validation failure. The `detail` array carries field paths and error types but never echoes the offending input. |
| `429` | `{"detail":"Rate limit exceeded."}` | Either rate limit layer triggered. |
| `502` | `{"detail":"<message>"}` | yfinance returned an unexpected error. |
| `504` | `{"detail":"<message>"}` | yfinance call exceeded the hard timeout. |

Error responses never include stack traces, library names, internal IDs, or DB structure (threat model T11, T13).

## Endpoints

### `GET /health`

Liveness probe. No request body. Response: `{"status":"ok"}` with status 200. Used by Render's health check; never throttled.

### `POST /api/price`

Compute call and put values plus Greeks for a single set of inputs.

**Request**

| Field | Type | Range | Notes |
|---|---|---|---|
| `S` | float | `[0, 1e9]` | Current asset price. |
| `K` | float | `(0, 1e9]` | Strike price. |
| `T` | float | `[0, 100]` | Time to expiry in years. |
| `r` | float | `[-1, 1]` | Continuously compounded annual risk free rate. |
| `sigma` | float | `[0, 10]` | Annualized volatility. |
| `model` | enum | `black_scholes` (default), `binomial`, `monte_carlo` | Which pricer computes the call and put. Greeks always come from closed form Black Scholes regardless. |

Strict: extra fields rejected with 422; `Infinity` or `NaN` rejected.

**Response**

```json
{
  "call": 10.4506,
  "put": 5.5735,
  "model": "black_scholes",
  "call_greeks": {
    "delta": 0.6368,
    "gamma": 0.01876,
    "theta_per_day": -0.01757,
    "vega_per_pct": 0.3752,
    "rho_per_pct": 0.5323
  },
  "put_greeks": {
    "delta": -0.3632,
    "gamma": 0.01876,
    "theta_per_day": -0.01054,
    "vega_per_pct": 0.3752,
    "rho_per_pct": -0.4189
  }
}
```

Greeks are returned in trader friendly units: vega per 1 percent of sigma, rho per 1 percent of r, theta per calendar day. Delta and gamma are in natural units. See `docs/risk/conventions.md`.

### `POST /api/heatmap`

Compute a 2D grid of call and put values across volatility and spot shocks.

**Request**

Adds to the price request:

| Field | Type | Range | Notes |
|---|---|---|---|
| `vol_shock` | `[float, float]` | each in `[-0.95, 1.0]`, min ≤ max | Min and max vol shock as fraction of `sigma`. |
| `spot_shock` | `[float, float]` | each in `[-0.95, 1.0]`, min ≤ max | Min and max spot shock as fraction of `S`. |
| `rows` | int | `[1, 21]` | Vol axis points. |
| `cols` | int | `[1, 21]` | Spot axis points. |
| `model` | enum | as above | Pricing model for every cell. |

The 21x21 cap is threat model T12 (server cost ceiling).

**Response**

```json
{
  "call": [[ ... ]],
  "put":  [[ ... ]],
  "model": "black_scholes",
  "sigma_axis": [...],
  "spot_axis":  [...]
}
```

`call` and `put` are 2D arrays sized `rows x cols`. `sigma_axis` carries the vol values sampled along rows; `spot_axis` the spot values along columns.

### `POST /api/calculations`

Run the same heat map computation as `/api/heatmap` and persist it. Returns the heat map plus a `calculation_id` (UUID) for later retrieval. Status `201`.

Same request shape as `/api/heatmap`. Response augments the heat map response with `calculation_id`.

### `GET /api/calculations/{id}`

Reconstruct a previously persisted heat map by UUID. The path parameter is anchored regex matched; non UUID values return 404 before any DB query runs.

**Response**

```json
{
  "calculation_id": "9c8f64a8-...",
  "s": 100.0, "k": 100.0, "t": 1.0, "r": 0.05, "sigma": 0.2,
  "rows": 9, "cols": 9,
  "call": [[ ... ]], "put": [[ ... ]],
  "sigma_axis": [...], "spot_axis": [...]
}
```

### `GET /api/tickers/{symbol}`

Look up the current price for a ticker via yfinance. The symbol path parameter is gated by `^[A-Z0-9.-]{1,10}$` at the FastAPI boundary; invalid symbols return 422 before any upstream call runs (threat model T6).

**Response (200)**

```json
{ "symbol": "AAPL", "name": "Apple Inc.", "price": 199.5, "currency": "USD" }
```

**Errors**

* `404` ticker not found.
* `502` upstream returned an error.
* `504` upstream exceeded the 5 second timeout.

Cached server side: 60 second TTL, 256 entry LRU. Repeated lookups within the TTL never hit yfinance.

### `POST /api/backtest`

Replay a strategy against historical prices and return the daily P&L curve.

**Request**

| Field | Type | Range | Notes |
|---|---|---|---|
| `symbol` | str | `^[A-Z0-9.-]{1,10}$` | Ticker symbol. |
| `strategy` | enum | `long_call`, `long_put`, `straddle` | Strategy to replay. |
| `start_date` | date | ISO 8601 | First entry date (inclusive). |
| `end_date` | date | ISO 8601 | Last mark date (inclusive). Range capped at 5 years. |
| `sigma` | float | `(0, 10]` | Implied vol the position was opened against, held constant for every mark. |
| `r` | float | `[-1, 1]` | Risk free rate. |
| `dte_days` | int | `(0, 365]` | Days to expiry from the entry date. |

**Response**

```json
{
  "symbol": "AAPL",
  "strategy": "long_call",
  "dates": ["2026-01-02", ...],
  "spot":  [270.76, ...],
  "position_value": [9.83, ...],
  "pnl":   [0.0, ...],
  "strike": 270.76,
  "entry_basis": 9.83,
  "entry_date": "2026-01-02",
  "expiry_date": "2026-02-01",
  "legs": [{"sign": 1, "kind": "call"}]
}
```

Convention: long only basis sign, ATM at entry, calendar day expiry, close to close marking. See `docs/risk/conventions.md`.

**Errors**

* `404` ticker not found.
* `422` insufficient price data (fewer than 2 marks).
* `502` upstream error.
* `504` upstream timeout.

## OpenAPI schema (machine readable)

In development, browse the live spec:

* Swagger UI: <http://localhost:8000/docs>
* OpenAPI JSON: <http://localhost:8000/openapi.json>

In production both are disabled to reduce attack surface fingerprinting. To dump the schema locally:

```bash
cd backend
uv run python -c "from app.main import build_app; import json; print(json.dumps(build_app().openapi(), indent=2))" > /tmp/openapi.json
```
