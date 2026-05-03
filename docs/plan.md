# Trader: implementation plan

This is the per phase implementation plan, derived from `SPEC.md`. It is owned by the Project Manager and updated at every phase boundary. For "which phase is next" status, read `STATUS.md` (the single source of truth). This file is the longer plan: who does what, what ships, and what gates a phase before it closes.

**Currently in flight**: Phase 3 (React frontend MVP) reserved for the next window. Phases 0, 1, and 2 are complete.

## How this plan is used

* The PM session reads `STATUS.md` to find the current phase, then reads the corresponding section here for the deliverable and gating detail.
* When a phase closes, the PM checks the box on each deliverable in this file, marks the phase done, and runs the mandatory check-in protocol from `CLAUDE.md`.
* When a phase pauses mid window, the PM writes a Resume note in `STATUS.md` (not here).
* If a phase reveals new work that does not fit, it goes to `docs/future-ideas.md` with the format prescribed there.

## Cross phase quality gates

A phase is not closed until every applicable gate has passed:

* **QA Engineer**: regression suite green, new tests added for the phase's features.
* **Security Engineer**: no open critical or high severity findings; sign off on input validation, error responses, third party calls, and secrets.
* **Code Reviewer**: every PR in the phase is reviewed and approved.
* **Risk and Financial Correctness Reviewer**: signs off on every phase that touches pricing math or P&L. Phases 1, 5, 7, 9, 10.
* **Documentation Engineer**: `docs/` reflects the phase's changes; setup guide updated where applicable.
* **Project Manager**: runs the mandatory user check-in described in `CLAUDE.md` ("Pacing rule") before opening the next phase.

---

## Phase 0: Foundations [IN FLIGHT]

**Owner**: PM session, with four specialist subagents dispatched in parallel.

**Window cost**: ~95% of one Max 5x window.

### PM deliverables (this session)

* [ ] `docs/plan.md` (this file) written.
* [ ] `STATUS.md` flipped to `in progress` for Phase 0.
* [ ] Four specialist subagents dispatched in parallel (UI/UX Designer, Security Engineer, DevOps Engineer, Documentation Engineer).
* [ ] Each subagent's output reviewed against its agent file's Definition of done.
* [ ] `STATUS.md` flipped to `completed`, "Next phase" set to Phase 1 (likely bundled with Phase 2).
* [ ] Mandatory user check-in run; explicit user response received.

### UI/UX Designer subagent deliverables

Input: `docs/design/claude-design-output.html` (Oxblood theme; canonical) plus `design/*.webp` (user mood board).

* [ ] `docs/design/tokens.md` summarizing the Oxblood design tokens for human reference (colors, type scale, spacing, radii, shadows, motion).
* [ ] Draft Tailwind config extension (the contents of `tailwindSketch.theme.extend` from the design manifest), saved as a snippet the DevOps Engineer can drop into `frontend/tailwind.config.ts`.
* [ ] `docs/design/wireframes.md` describing each of the five screens (Pricing, Heat Map, Model Comparison, Backtest, History) with grids, breakpoints, and component anatomy.
* [ ] Heat map color scale spec for value mode and P&L mode (exact hex values at min, midpoint, max; how the midpoint is set).
* [ ] Open design questions reported back to the PM.

### Security Engineer subagent deliverables

Input: `SPEC.md`, `agents/08-security-engineer.md`.

* [ ] `docs/security/threat-model.md`: assets, threats, controls, accepted residual risks. Covers OWASP top 10 plus SSRF (yfinance), supply chain, sensitive data exposure.
* [ ] `docs/security/checklist.md`: per phase hardening checklist.
* [ ] `docs/security/secrets.md` (stub): every secret to be introduced, where it will live, who has access, rotation policy.
* [ ] Recommendations to PM: branch protection rules, CI scan tools (Dependabot, gitleaks, bandit, semgrep, CodeQL), CSP starting point, rate limit thresholds.

### DevOps Engineer subagent deliverables

Input: `SPEC.md`, `agents/09-devops-engineer.md`, `docs/design/claude-design-output.html`.

* [ ] `git init` in `/home/mustafa/src/trader/`.
* [ ] `.gitignore` covering Python (`__pycache__`, `.venv`, `*.pyc`), Node (`node_modules`, `dist`), OS (`.DS_Store`), editor (`.idea`, `.vscode`), env files (`.env`, `.env.local`).
* [ ] `origin` set to `git@github.com:Mustafan4x/Trader.git` (SSH; both SSH and HTTPS auth confirmed working).
* [ ] First commit staged with the existing files (`SPEC.md`, `CLAUDE.md`, `GETTING-STARTED.md`, `STATUS.md`, `agents/`, `docs/`, `design/`) and pushed to `main`.
* [ ] `backend/` scaffolded with `uv init`, `pyproject.toml` configured for FastAPI (FastAPI, uvicorn, pydantic, pytest, httpx, ruff, mypy as initial deps).
* [ ] `frontend/` scaffolded with `pnpm create vite frontend --template react-ts`, Tailwind installed per the official Vite + Tailwind setup, `frontend/tailwind.config.ts` populated with the `tailwindSketch.theme.extend` block from the Oxblood design manifest, `frontend/src/styles/tokens.css` populated with the CSS variables from the HTML's `:root` block.
* [ ] Pre commit hooks: `ruff` (Python), `eslint` plus `prettier` (frontend), `gitleaks` (secrets).
* [ ] `.github/workflows/ci.yml`: lint, type check (`mypy` plus `tsc --noEmit`), tests on every PR. Target under five minutes for a typical PR.

### Documentation Engineer subagent deliverables

Input: `SPEC.md`, `agents/15-documentation-engineer.md`.

* [ ] `README.md`: project pitch, GitHub link, visual theme name (Oxblood), pointers to `SPEC.md`, `CLAUDE.md`, `STATUS.md`, `docs/setup-guide.md`, `docs/architecture.md`, `docs/design/claude-design-output.html`.
* [ ] `docs/architecture.md`: high level component diagram (text or mermaid) showing React (Tailwind, Oxblood) -> FastAPI -> Postgres on Neon, plus Cloudflare Pages and Render hosting.
* [ ] Initial ADRs in `docs/adr/`:
  * `0001-react-fastapi-over-streamlit.md`
  * `0002-postgres-over-mysql.md`
  * `0003-cloudflare-pages-over-vercel.md`
  * `0004-oxblood-theme-as-v1-visual.md`

### Phase 0 quality gates

* PM verifies all four subagent reports against their respective agent files.
* Security Engineer's threat model is published and the recommended branch protection rules are flagged for the user to apply on GitHub (this requires a browser click, so the user does it; the PM lists the exact settings).
* `git push` of the first commit succeeded; the `Mustafan4x/Trader` repo on GitHub now holds the spec, agents, and design.
* `frontend/` and `backend/` scaffolds are present and lint clean.

### Phase 0 user actions (the PM lists these in the end of phase summary)

These cannot be done by a subagent; they require Mustafa to click in a browser.

* Apply branch protection on `main`: require PR review, require CI green, restrict force pushes (Security Engineer recommends exact rules).
* Enable Dependabot for `pip` and `pnpm` ecosystems on the GitHub repo.
* Enable CodeQL on the GitHub repo for both Python and JavaScript/TypeScript.

---

## Phase 1: Python REPL Black Scholes

**Owners**: Quant Domain Validator, Backend Developer.

**Window cost**: ~30% alone. **Bundle candidate with Phase 2** unless the user objects at Phase 0 check-in.

### Deliverables

* `backend/app/pricing/black_scholes.py`: pure Python module computing call and put values from the five inputs (S, K, T, r, sigma). Test first per the Quant Validator's reference values.
* `backend/app/repl.py` (or equivalent `__main__`): prompts for the five inputs and prints both prices.
* `backend/tests/pricing/test_black_scholes.py`: numerical reference tests, edge case tests (T = 0, sigma = 0, deep ITM, deep OTM).
* Risk Reviewer signs off on the formula and edge case behavior.

### Gates

QA, Security, Code Review, Risk Reviewer.

---

## Phase 2: FastAPI backend [DONE]

**Owners**: Backend Developer (lead), Security Engineer (review), Observability Engineer, QA Engineer.

**Window cost**: ~60% alone, or ~95% bundled with Phase 1. Shipped solo in its own window since Phase 1 closed under budget.

### Deliverables

* [x] `backend/app/main.py` (factory `build_app`), `backend/app/api/price.py`, `backend/app/core/config.py`, `backend/app/core/logging.py`, `backend/app/middleware.py`, `backend/app/serve.py`.
* [x] `GET /health` (liveness).
* [x] `POST /api/price` accepts the five inputs, returns call and put. Pydantic models validate inputs strictly (`extra="forbid"`, `allow_inf_nan=False`, mathematical bounds enforced before the pricing module is called).
* [x] CORS allow list set to the local frontend dev origin (`http://localhost:5173`), `allow_credentials=False`, no wildcards. Production origin added in Phase 11.
* [x] HTTP security headers on every response: `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy: frame-ancestors 'none'`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`. Uvicorn `Server` header suppressed via `trader-serve`.
* [x] Application layer rate limiting via `slowapi`. Default `60/minute` per IP; override via `TRADER_RATE_LIMIT_DEFAULT`.
* [x] 32 KB body size cap at the middleware layer (rejects oversized `Content-Length` with HTTP 413).
* [x] Sanitized validation handler: 422 responses do not echo input values, library internals, or stack traces.
* [x] OpenAPI docs (`/docs`, `/openapi.json`) gated on `TRADER_ENVIRONMENT`; hidden in production, served in development.
* [x] Structured JSON access logger (`app.access`) with `request_id`, `method`, `path`, `status`, `duration_ms` per request. `X-Request-Id` echoed on every response.
* [x] 85 tests pass: contract tests on `POST /api/price` (happy path, validation failures, missing fields, extra fields, non finite values, oversized body, error body shape), security headers, CORS preflight, rate limit burst, structured logging shape, environment dependent behavior, plus the carried over Phase 1 pricing math suite.

### Gates

* [x] QA: 85 tests green via `uv run pytest`.
* [x] Security: Phase 2 review run by Security Engineer subagent. Sign off received with one medium severity finding (production OpenAPI exposure) addressed in this phase, plus one low severity finding (assert under `python -O`) addressed; remaining low and info severity items accepted and documented in the review report.
* [x] Code Review: PM session reviewed the diff before commit. No simplifications outstanding.

---

## Phase 3: React frontend MVP

**Owners**: Frontend Developer (lead), UI/UX Designer (review), Accessibility Specialist (audit), Security Engineer (CSP, secrets, frontend to backend calls).

**Window cost**: ~95% of one window.

### Deliverables

* `InputForm` (the five inputs, client side validation, submits `POST /api/price`).
* `ResultPanel` (call and put values).
* `LayoutShell`, `Sidebar`, `TopBar` per the Oxblood design.
* Typed API client wrapping `/api/price`.
* Vitest plus Testing Library tests using `[data-component]` and `[data-element]` selectors.
* a11y audit: keyboard nav, screen reader labels, color contrast.

### Gates

QA, Security, Code Review, UI/UX sign off, a11y sign off.

---

## Phase 4: Heat map visualization

**Owners**: Frontend Developer (lead), Backend Developer (vectorized endpoint), Performance Engineer (profile).

**Window cost**: ~90% of one window.

### Deliverables

* `POST /api/heatmap`: 2D grid of call and put values for vol shocks plus price shocks. Vectorized with numpy; a 25 by 25 grid responds in well under one second.
* `HeatMap` component side by side for call and put. Default approach: canvas plus a transparent div hit grid (matches the Oxblood reference). Recharts/Plotly is acceptable if it materially improves maintainability; decision goes through Code Reviewer.
* User configurable vol and price shock ranges and resolution.

### Gates

QA, Security, Code Review, Performance review.

---

## Phase 5: P&L heat map

**Owners**: Frontend Developer (lead), Backend Developer, Risk Reviewer.

**Window cost**: ~40% alone. **Bundle candidate with Phase 6** unless the user objects.

### Deliverables

* Two new form fields: `purchase_price_call`, `purchase_price_put`.
* Heat map toggle: value mode versus P&L mode.
* Color scale: green positive, red negative, neutral midpoint at zero.
* Risk Reviewer validates the P&L sign and magnitude under stress cases.

### Gates

QA, Security, Code Review, Risk Reviewer.

---

## Phase 6: Persistence

**Owners**: Data Engineer (schema), Database Administrator (migrations), Backend Developer (wire it in), Security Engineer (review).

**Window cost**: ~60% alone, or ~95% bundled with Phase 5.

### Deliverables

* `inputs` and `outputs` tables (one input row plus N output rows per Calculate click), linked by `calculation_id` (UUID).
* Alembic migrations with proper indexes.
* SQLAlchemy 2.x models (parameterized queries only; manual SQL string formatting is banned).
* `GET /api/calculations/{id}` to fetch a previous calculation.
* Postgres in `docker-compose.yml`; CI step that runs `alembic upgrade head` plus integration tests against a real Postgres.
* Production DB user has only the privileges it needs (no SUPERUSER, no CREATE DATABASE, no DROP TABLE).
* DSN never committed; `gitleaks` rule verified to catch a committed DSN.

### Gates

QA, Security (SQL injection surface, secrets, least privilege), Code Review.

---

## Phase 7: The Greeks

**Owners**: Quant Domain Validator, Pricing Models Engineer, Backend Developer, Frontend Developer, QA Engineer.

**Window cost**: ~40% alone. **Bundle candidate with Phase 8** unless the user objects.

### Deliverables

* Closed form Greeks (delta, gamma, theta, vega, rho) added to the Black Scholes module.
* `POST /api/price` returns Greeks alongside call and put.
* `GreeksPanel` displays them next to the result panel.
* Property based tests: put call parity, delta bounds, vega non negativity, etc.

### Gates

QA, Security, Code Review, Risk Reviewer.

---

## Phase 8: Real market data

**Owners**: Backend Developer, Frontend Developer, Security Engineer (third party request hardening).

**Window cost**: ~55% alone, or ~95% bundled with Phase 7.

### Deliverables

* `GET /api/tickers/{symbol}`: yfinance lookup with hard timeout (5 seconds), max response size (1 MB), no following arbitrary redirects.
* Ticker input validation: alphanumeric plus dot plus dash, length capped (10 chars).
* Response cache for at least one minute to avoid rate limits.
* `TickerAutocomplete` with debounced search; on select, auto fills the asset price field.

### Gates

QA, Security (SSRF, timeouts, response size, retries), Code Review.

---

## Phase 9: Multiple pricing models

**Owners**: Pricing Models Engineer, Frontend Developer, Risk Reviewer.

**Window cost**: ~95% of one window.

### Deliverables

* Binomial tree pricer.
* Monte Carlo pricer.
* `model` parameter on `/api/price` and `/api/heatmap` routes to the correct module.
* `ModelSelector` UI with side by side comparison view.
* Convergence tests: the three models converge on identical inputs.

### Gates

QA, Security, Code Review, Risk Reviewer.

---

## Phase 10: Backtesting

**Owners**: Pricing Models Engineer plus Backend Developer (engine), Frontend Developer (chart), Performance Engineer.

**Window cost**: ~95 to 99% of one window. **Do not bundle anything else.**

### Deliverables

* `POST /api/backtest`: given a strategy (long call, covered call, straddle, etc.) and a date range, replay historical prices and produce a P&L curve.
* `BacktestChart` renders the curve, with strategy selector.
* Performance review: the backtest endpoint stays within an acceptable time and memory budget.

### Gates

QA, Security, Code Review, Risk Reviewer, Performance review.

---

## Phase 11: Production deployment

**Owners**: DevOps Engineer (lead), Security Engineer (final hardening), Documentation Engineer (setup guide).

**Window cost**: ~90% of one window. Reserve a fresh window because deployment requires the user to log in and click through three dashboards.

### Deliverables

* Frontend on Cloudflare Pages.
* Backend on Render.
* Postgres on Neon.
* Custom subdomain (if the user wants one).
* Final security checklist: HTTPS everywhere, HSTS preload eligibility, CSP and frame ancestors and CORS production correct, secret rotation, no error path leaking stack traces.
* `docs/setup-guide.md` polished end to end: a fresh user can deploy from a fresh clone in under 30 minutes.
* `docs/api.md` published from the FastAPI OpenAPI schema.

### Gates

QA, Security (final hardening), Code Review, Documentation Engineer sign off.

After Phase 11 closes, the PM offers a `/schedule` agent to revisit the deployed app for any rot or follow ups in a few weeks.

---

## Notes on bundling

The PM is permitted to bundle pairs of phases into a single window when the next phase is small enough and the current phase came in well under budget. Bundle candidates per `STATUS.md`: Phase 1 plus 2, Phase 5 plus 6, Phase 7 plus 8. Bundling is opt in: confirm with the user during the post phase check-in. Phase 10 is never bundled.

## Notes on design changes

Both design change flows from `CLAUDE.md` work at any time, including after Phase 11 ships:

* **Flow A**: user describes a change in plain English; the session edits React, Tailwind, and the canonical HTML directly. Logged as a one liner in `STATUS.md` ("Design sync log").
* **Flow B**: user replaces `docs/design/claude-design-output.html`; the PM diffs and dispatches the UI/UX Designer plus Frontend Developer.
