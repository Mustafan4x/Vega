# Vega

**Live demo: <https://vega-2rd.pages.dev/>**

The backend runs on Render's free tier and sleeps after about 15 minutes of inactivity, so the first calculation after a long idle period can take 30 to 60 seconds while the container wakes up. After that, requests are instant.

A full stack Black Scholes options pricer built as a quant interview pet project. The app prices European calls and puts from five inputs (asset price, strike, time to expiry, risk free rate, volatility), renders heat maps of value and P&L over volatility and price shocks, exposes the Greeks, looks up live prices via yfinance, compares Black Scholes against a binomial tree and a Monte Carlo pricer, and runs simple option strategy backtests over historical data.

## Visual theme

**Oxblood**: a dark surfaced theme with oxblood `#C03A3A` as primary, sea green `#34D399` as accent, IBM Plex Serif italic for display, Newsreader for numerics, Manrope for UI text, and JetBrains Mono for code. The canonical visual ground truth is a single self contained HTML file at [`docs/design/claude-design-output.html`](docs/design/claude-design-output.html); open it in any browser to see all five screens (Pricing, Heat Map, Model Comparison, Backtest, History) rendered live.

## Tech stack at a glance

| Layer | Choice |
|---|---|
| Frontend | React 18 plus Vite plus TypeScript plus Tailwind, hosted on Cloudflare Pages |
| Backend | FastAPI on Python 3.12, hosted on Render |
| Database | Postgres on Neon (production), SQLite (local dev) |
| Migrations | SQLAlchemy 2.x plus Alembic |
| Package managers | `uv` (Python), `pnpm` (JS) |
| CI/CD | GitHub Actions |
| Market data | `yfinance` |

## Entry points

* [`SPEC.md`](SPEC.md): the full project spec, agent roster, and 11 phase build plan.
* [`CLAUDE.md`](CLAUDE.md): the auto loaded brief for any Claude Code session opened in this directory.
* [`STATUS.md`](STATUS.md): single source of truth for which phase is in flight.
* [`docs/plan.md`](docs/plan.md): per phase implementation plan written by the Project Manager.
* [`docs/architecture.md`](docs/architecture.md): high level system diagram and component descriptions.
* [`docs/setup-guide.md`](docs/setup-guide.md): user facing deployment guide (Cloudflare, Render, Neon, custom domain).
* [`docs/design/claude-design-output.html`](docs/design/claude-design-output.html): canonical Oxblood visual reference, openable in a browser.
* [`docs/adr/`](docs/adr/): Architecture Decision Records for the non obvious calls (React over Streamlit, Postgres over MySQL, Cloudflare Pages over Vercel, Oxblood as v1 visual).

## How to run locally

The DevOps Engineer agent owns the full local development walkthrough at [`docs/devops.md`](docs/devops.md) (created in Phase 0 alongside this README). That file covers `uv sync` for the backend, `pnpm install` for the frontend, and the `docker compose up` flow once it lands.

For the abridged version, see "Local development setup" in [`docs/setup-guide.md`](docs/setup-guide.md).

## Status

v1 is unauthenticated by design (every visitor sees the same calculation history). The deferred per user history plan is captured in [`docs/future-ideas.md`](docs/future-ideas.md).
