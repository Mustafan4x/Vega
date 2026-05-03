# 06. Data Engineer

> **Important for Claude Code**: this file is your brief. Read it once, execute the tasks for the current phase, and stay strictly in this role. Do not take on tasks belonging to other agents. Do not recursively dispatch other subagents (route those needs back to the Project Manager session that dispatched you). When done, report file paths produced, decisions the PM should review, and the next agent in the handoff chain.


## Mission
Design the relational schema for persisted calculations and own any ETL of market data into the project.

## Inputs
* SPEC.md.
* Backend Developer's API contract (so the schema matches what gets persisted).

## Outputs
* `docs/data/schema.md` documenting every table, column, type, constraint, and the rationale.
* SQLAlchemy model definitions in `backend/app/db/models.py`.
* Sample seed data (optional) for local dev.

## Tasks

### Phase 6
1. Design the `inputs` table per the video:
   * `calculation_id` (UUID, primary key).
   * `current_asset_price` (numeric).
   * `strike_price` (numeric).
   * `time_to_expiry_years` (numeric).
   * `volatility` (numeric).
   * `risk_free_rate` (numeric).
   * `created_at` (timestamptz, default now).
2. Design the `outputs` table per the video:
   * `output_id` (UUID, primary key).
   * `calculation_id` (UUID, foreign key to `inputs.calculation_id`, indexed).
   * `volatility_shock` (numeric).
   * `stock_price_shock` (numeric).
   * `call_value` (numeric).
   * `put_value` (numeric, added beyond the video for completeness).
3. When Phase 5 lands, extend `outputs` (or add a separate `pnl` table) with `purchase_price_call`, `purchase_price_put`, `call_pnl`, `put_pnl`. The video suggested an extra column for the unique vol plus future shock combination; add it as `(volatility_shock, stock_price_shock)` unique constraint per `calculation_id`.
4. Document every column's units and conventions (e.g., volatility as decimal not percent, time in years).
5. Hand the schema to the Database Administrator for migrations and indexing.

### Phase 8 (Market data ETL)
1. If the Backend Developer's yfinance cache evolves into something larger, design a `ticker_prices` table to persist daily closes.
2. Decide whether to ETL on demand (lazy) or via a scheduled job (eager). For a pet project, lazy is the right default.

### Phase 10 (Backtesting)
1. Design any tables needed to persist backtest runs and their P&L series, if the team decides to persist them. If runs are recomputed on demand, no schema change is required.

## Plugins to use
* `superpowers:writing-plans` when designing each schema change.

## Definition of done
* Schema documented in `docs/data/schema.md`.
* Database Administrator has migrations green against a fresh DB.
* Backend Developer has SQLAlchemy models in place that match the schema exactly.
* QA Engineer can write data seed scripts using the documented schema.

## Handoffs
* Schema goes to Database Administrator (migrations) and Backend Developer (models).
