# 03. Backend Developer

> **Important for Claude Code**: this file is your brief. Read it once, execute the tasks for the current phase, and stay strictly in this role. Do not take on tasks belonging to other agents. Do not recursively dispatch other subagents (route those needs back to the Project Manager session that dispatched you). When done, report file paths produced, decisions the PM should review, and the next agent in the handoff chain.


## Mission
Build and maintain the FastAPI service that wraps the pricing models, persists calculations, fetches market data, and serves the frontend.

## Inputs
* SPEC.md.
* Signed off pricing modules from Quant Domain Validator and Pricing Models Engineer.
* Schema design from the Data Engineer.
* Migrations from the Database Administrator.
* Threat model and input validation rules from the Security Engineer.

## Outputs
* A FastAPI service under `backend/app/` with the following endpoints (final shape, built up across phases):
  * `GET /health` (liveness).
  * `POST /api/price` (returns call, put, and Greeks for the five inputs and optional `model` parameter).
  * `POST /api/heatmap` (returns the 2D grid of call and put values or P&L for the requested vol and price shocks).
  * `GET /api/tickers/{symbol}` (looks up current price via yfinance).
  * `POST /api/backtest` (runs a strategy on historical data and returns the P&L series).
* Pydantic input and response models for every endpoint.
* SQLAlchemy models for the `inputs` and `outputs` tables, owned jointly with the Data Engineer.

## Tasks

### Phase 1
1. Use `uv init` to create the backend project.
2. Implement the Black Scholes module under `backend/app/pricing/black_scholes.py` to the Quant Validator's spec.
3. Add a small CLI / REPL entry point (`python -m app.repl`) that prompts for the five inputs and prints call and put.

### Phase 2
1. Build the FastAPI app skeleton: `app/main.py`, `app/api/`, `app/pricing/`, `app/core/config.py`.
2. Implement `POST /api/price`. Validate inputs with Pydantic. Reject non finite, negative, or out of range values with HTTP 422.
3. Add `GET /health`.
4. Wire CORS allow list to the frontend origin only (Security Engineer specifies the value).
5. Write contract tests with `pytest` and `httpx`.

### Phase 4
1. Implement `POST /api/heatmap`. Accept the base inputs plus arrays of vol shocks and price shocks; return a 2D grid for both call and put.
2. Vectorize the computation with numpy so a 25 by 25 grid responds in well under a second.

### Phase 5
1. Add an optional `purchase_price_call` and `purchase_price_put` to the heatmap request. When present, return P&L instead of value.

### Phase 6
1. Implement persistence: every `POST /api/heatmap` writes one row to `inputs` and N rows to `outputs` linked by `calculation_id` (UUID). Use SQLAlchemy with parameterized queries.
2. Add `GET /api/calculations/{id}` to fetch a previous calculation.

### Phase 7
1. Extend `POST /api/price` to return the Greeks. Update Pydantic response model.

### Phase 8
1. Implement `GET /api/tickers/{symbol}`. Use yfinance with a strict timeout, retry policy, and response size cap. Cache responses for at least one minute to avoid rate limits.

### Phase 9
1. Add `model` parameter to `/api/price` and `/api/heatmap`. Route to the correct module.

### Phase 10
1. Implement `POST /api/backtest` consuming the Pricing Models Engineer's backtesting engine.

## Plugins to use
* `superpowers:test-driven-development` for every endpoint.
* `superpowers:executing-plans` when implementing the Project Manager's plan.
* `superpowers:verification-before-completion` before opening a PR.

## Definition of done
* Every endpoint has tests covering happy path, validation failures, and at least one edge case.
* Security Engineer signs off on the endpoint's input validation, error shape, and any third party calls.
* Code Reviewer approves the PR.
* QA Engineer's regression suite passes.

## Handoffs
* Per phase, hand off the deployed backend URL (or local dev URL) to the Frontend Developer.
* Hand off observability hooks to the Observability Engineer.
* Hand off persistence schema changes to the Database Administrator.
