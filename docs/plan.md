# Vega: implementation plan

This is the per phase implementation plan, derived from `SPEC.md`. It is owned by the Project Manager and updated at every phase boundary. For "which phase is next" status, read `STATUS.md` (the single source of truth). This file is the longer plan: who does what, what ships, and what gates a phase before it closes.

**Status**: v1 shipped. All eleven phases complete. Live at <https://vega-2rd.pages.dev/> (frontend) and <https://vega-backend-1wm0.onrender.com> (backend, Neon Postgres).

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

* [ ] `git init` in `/home/mustafa/src/vega/`.
* [ ] `.gitignore` covering Python (`__pycache__`, `.venv`, `*.pyc`), Node (`node_modules`, `dist`), OS (`.DS_Store`), editor (`.idea`, `.vscode`), env files (`.env`, `.env.local`).
* [ ] `origin` set to `git@github.com:Mustafan4x/Vega.git` (SSH; both SSH and HTTPS auth confirmed working).
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
* `git push` of the first commit succeeded; the `Mustafan4x/Vega` repo on GitHub now holds the spec, agents, and design.
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
* [x] HTTP security headers on every response: `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy: frame-ancestors 'none'`, `Cross-Origin-Opener-Policy`, `Cross-Origin-Resource-Policy`. Uvicorn `Server` header suppressed via `vega-serve`.
* [x] Application layer rate limiting via `slowapi`. Default `60/minute` per IP; override via `VEGA_RATE_LIMIT_DEFAULT`.
* [x] 32 KB body size cap at the middleware layer (rejects oversized `Content-Length` with HTTP 413).
* [x] Sanitized validation handler: 422 responses do not echo input values, library internals, or stack traces.
* [x] OpenAPI docs (`/docs`, `/openapi.json`) gated on `VEGA_ENVIRONMENT`; hidden in production, served in development.
* [x] Structured JSON access logger (`app.access`) with `request_id`, `method`, `path`, `status`, `duration_ms` per request. `X-Request-Id` echoed on every response.
* [x] 85 tests pass: contract tests on `POST /api/price` (happy path, validation failures, missing fields, extra fields, non finite values, oversized body, error body shape), security headers, CORS preflight, rate limit burst, structured logging shape, environment dependent behavior, plus the carried over Phase 1 pricing math suite.

### Gates

* [x] QA: 85 tests green via `uv run pytest`.
* [x] Security: Phase 2 review run by Security Engineer subagent. Sign off received with one medium severity finding (production OpenAPI exposure) addressed in this phase, plus one low severity finding (assert under `python -O`) addressed; remaining low and info severity items accepted and documented in the review report.
* [x] Code Review: PM session reviewed the diff before commit. No simplifications outstanding.

---

## Phase 3: React frontend MVP [DONE]

**Owners**: Frontend Developer (lead), UI/UX Designer (review), Accessibility Specialist (audit), Security Engineer (CSP, secrets, frontend to backend calls).

**Window cost**: ~95% of one window.

### Deliverables

* [x] `LayoutShell`, `Sidebar`, `TopBar` rendered with the Oxblood theme tokens; primary navigation switches between Pricing and Phase placeholder screens for Heat Map (4), History (6), Compare (9), and Backtest (10).
* [x] `InputForm` with the five inputs (S, K, T, r, sigma); r and sigma display in percent. Client side validation reflected in `aria-invalid`. Calculate button disables and shows `aria-busy` while a request is pending.
* [x] `NumField` primitive with draft state, blur clamp, partial decimal regex, and `htmlFor`/`id` label association.
* [x] `MetricCard` (call and put variants) with hero number, ITM/OTM tag, intrinsic plus time value sub line. `ResultPanel` composes both metric cards.
* [x] `PricingScreen` owns the form state, the in flight `AbortController`, the API call, and split status (`role='status'`) and error (`role='alert'`) regions.
* [x] Typed API client (`src/lib/api.ts`) for `POST /api/price`: timeout, abort handling, and a `PriceError` union for validation, rate limit, server, network, timeout, aborted. `credentials: 'omit'`, `mode: 'cors'`. API base URL from `VITE_API_BASE_URL` (default `http://localhost:8000` for local dev).
* [x] Component CSS ported from `docs/design/claude-design-output.html` to `src/styles/components.css`; selectors and `data-component`/`data-element` names match the canonical reference for cross referencing.
* [x] 24 Vitest plus Testing Library tests (api client error mapping, NumField typing/blur, InputForm submit/disabled/invalid, ResultPanel formatting and ITM/OTM, LayoutShell nav, App smoke).

### Gates

* [x] QA: 24 tests pass via `pnpm test`. ESLint clean, Prettier clean, `tsc --noEmit` clean. `pnpm build` succeeds.
* [x] Security: Phase 3 review run by Security Engineer subagent. Sign off received with no critical or high severity findings. Two info severity items deferred (production fail loud on missing `VITE_API_BASE_URL`, CSP and security headers wired at Cloudflare Pages in Phase 11).
* [x] a11y: Phase 3 audit run by Accessibility Specialist subagent. Two contrast blockers (call hero, OTM tag, error status text) addressed by switching to the `--color-primary-300`/`--color-primary-200` tints. Major items addressed: ITM/OTM tag accessible name, avatar role and label, status/alert role split, sidebar nav `aria-label` for icon only mode, sr-only `<h1>` per screen, sidebar status accessible name. Remaining minor items (focus ring thickness on icon buttons, color-scheme dark+light when the theme toggle ships) deferred to a follow up.
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.
* [x] Live smoke test: backend `vega-serve` plus frontend `vite preview` exchanged a happy path `/api/price` call from the `localhost:5173` origin.

---

## Phase 4: Heat map visualization [DONE]

**Owners**: Frontend Developer (lead), Backend Developer (vectorized endpoint), Performance Engineer (profile).

**Window cost**: ~90% of one window. Spanned two windows in practice (backend half landed in the first window with usage already at 68 percent and 34 minutes to reset; frontend half resumed cleanly in the next window from Resume notes).

### Deliverables

* [x] `backend/app/pricing/black_scholes_vec.py`: vectorized numpy pricer for call and put on a 1D `S` axis and a 1D `sigma` axis, returning a 2D ndarray with rows indexed by sigma and cols indexed by S. Verified cell for cell against the scalar pricer.
* [x] `POST /api/heatmap` (`backend/app/api/heatmap.py`): 2D grid of call and put values. Strict Pydantic validation, threat model T12 cap of 21 by 21 cells, finite only inputs, sane upper bounds on `S`, `K`, `T`, `r`, `sigma` to prevent OverflowError, and a model_validator rejecting inverted shock ranges and shocks outside [-0.95, 1.0]. Cold perf: 21 by 21 call+put math runs in under 1 ms; full HTTP path well under 50 ms.
* [x] `frontend/src/lib/heatMapColors.ts`: segmented linear color interpolator with three stop tables (`stopsValue`, `stopsNeg`, `stopsPos`) ported verbatim from `docs/design/wireframes.md` heat map color scale spec. Unit tested.
* [x] `frontend/src/lib/api.ts`: refactored to share a `postJson` helper between `fetchPrice` and the new `fetchHeatmap`. Same `PriceError` union (validation, rate limit, server, network, timeout, aborted), 12 second deadline for heat map requests.
* [x] `frontend/src/components/HeatMap.tsx`: 240 by 240 canvas painter doing bilinear interpolation across the data grid; transparent CSS grid overlay (`[data-element="hitGrid"]`) of `[data-element="cell"]` divs with `aria-label` carrying sigma, spot, and value or P&L per cell.
* [x] `frontend/src/components/HeatMapControls.tsx`: mode tabs (Value, P&L), vol shock and spot shock range pair sliders, resolution selector (5, 9, 13, 17, 21), and basis NumFields surfaced only in P&L mode.
* [x] `frontend/src/screens/HeatMapScreen.tsx`: composes the InputForm with the new controls and two heat maps side by side (call, put). AbortController on every request so a rapid-fire user is never racing a stale response.
* [x] App nav switched: Heat Map nav item now opens the live screen (Phase placeholder removed).
* [x] 50 frontend Vitest tests pass (was 24): added 8 for `heatMapColors`, 6 for `HeatMap`, 5 for `HeatMapControls`, 3 for `fetchHeatmap`, plus an updated App test for the new screen.
* [x] 125 backend tests pass (was 85): added 12 for the vectorized pricer and 28 for the heat map endpoint.

### Gates

* [x] QA: 125 backend + 50 frontend tests pass. tsc, eslint, prettier, ruff, mypy all clean. Vite production build green.
* [x] Security: Phase 4 review run by Security Engineer subagent. Sign off received with no critical or high findings. Medium finding (unbounded `r` and `T` causing OverflowError on `math.exp`) addressed in this phase by adding sane upper bounds on `S`, `K`, `T`, `r`, `sigma` to both `PriceRequest` and `HeatmapRequest`. Low note (per route rate limits) deferred to Phase 10 (backtest).
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.
* [x] Performance: 21 by 21 grid call+put math in 0.4 ms cold, far under the SPEC's "well under one second" bar. Performance Engineer dispatch deferred since the budget is so loose.
* [x] Live smoke test: `vega-serve` exchanged a 9 by 9 heat map call from `localhost:5173` and a 22 by 22 rejection with clean field level error.

---

## Phase 5: P&L heat map [DONE]

**Owners**: Frontend Developer (lead), Backend Developer, Risk Reviewer.

**Window cost**: ~40% alone. Shipped solo (not bundled with Phase 6).

### Deliverables

* [x] Two purchase price NumFields (`Call paid`, `Put paid`) surfaced in `HeatMapControls` only when the mode tab is set to P&L. (Landed as a side effect of Phase 4 controls work.)
* [x] Heat map toggle: value mode versus P&L mode via the mode tabs in `HeatMapControls`. Pressing the tab switches the color ramp and the cell label wording on both heat maps simultaneously.
* [x] Color scale: green positive, red negative, neutral gray at zero, anchored to the per leg basis. Implemented in `frontend/src/lib/heatMapColors.ts` `plColor` with the diverging zero anchored ramp from `docs/design/wireframes.md`.
* [x] Sign convention: `pl = value - basis` from the long holder perspective per `docs/risk/conventions.md`. Call basis routes to the call heat map; put basis to the put heat map.
* [x] Cell `aria-label` formats signed dollar amounts (`-$4.00` vs `$4.00`) so a screen reader user gets unambiguous sign information.
* [x] 7 new frontend tests (3 P&L property tests on `plColor` color ramp lean and saturation; 4 P&L wording and signed P&L tests on `HeatMap`). 57 frontend tests pass total.
* [x] Wireframes spec aligned: the P&L denominator is documented as `max(0.5, abs(basis) * 0.4) * 3` to match the implementation's defensive `Math.abs(basis)`.

### Gates

* [x] QA: 57 frontend + 125 backend tests pass. tsc, eslint, prettier, ruff, mypy clean.
* [x] Security: no new endpoints; the Phase 4 review still applies.
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.
* [x] Risk Reviewer: subagent signed off with no blockers. Confirmed sign correctness on a centered grid (call = 10.45, put = 5.57 at the canonical reference inputs match `docs/risk/sanity-cases.md` Case 1), monotonicity along the spot axis (call rises with spot, put falls), maximum loss bounded by basis, and screen reader sign disambiguation.
* [x] Live smoke test: `vega-serve` exchanged a 5x5 P&L grid; confirmed the center cell at the at the money basis comes out to $0.00, and the corners reach the expected ±premium magnitudes.

---

## Phase 6: Persistence [DONE]

**Owners**: Data Engineer (schema), Database Administrator (migrations), Backend Developer (wire it in), Security Engineer (review).

**Window cost**: ~60% alone. Shipped solo.

### Deliverables

* [x] `calculation_inputs` and `calculation_outputs` tables linked by `calculation_id` (UUID), with an index on `calculation_outputs.calculation_id` and `ondelete=CASCADE` on the FK so a future delete of an input row cleans up its grid cells.
* [x] SQLAlchemy 2.x typed declarative models (`backend/app/db/models.py`) with parameterized queries only. No `text(...)`, no f-string SQL.
* [x] Alembic migration (`backend/alembic/versions/9c8f64a81798_create_calculation_tables.py`) generated from the models. `alembic.ini` ships with the local SQLite default DSN (`sqlite:///./var/vega.db`); production reads `VEGA_DATABASE_URL` via `alembic/env.py`.
* [x] `POST /api/calculations` accepts the heat map shape, computes via `black_scholes_vec`, persists 1 input row plus `rows * cols` output rows in a single transaction, and returns the heat map response plus a `calculation_id` UUID. Status 201.
* [x] `GET /api/calculations/{id}` reconstructs the grid from the persisted rows. Anchored UUID regex gates the path parameter so SQL injection patterns return 404 before the ORM is touched.
* [x] `docker-compose.yml` for local Postgres parity with Neon (binds `127.0.0.1:5432` only). Documented in the file's header comment.
* [x] `backend/.env` and `backend/var/` added to `.gitignore` so a stray dev SQLite or DSN cannot be committed. The Phase 0 `gitleaks` rule still catches Postgres DSN patterns.
* [x] Test fixture rebinds the engine to in memory SQLite via `StaticPool` per test (`tests/conftest.py` `_isolated_db` autouse), so no test run can touch the dev or production DB.
* [x] 13 new contract tests on `/api/calculations` covering happy write, persisted input row, persisted N output rows, GET round trip, 404 on unknown UUID, 404 on non UUID, path injection patterns rejected at the UUID gate, oversized grid rejection, extra field rejection, two writes have different IDs, and path traversal attempts.
* [x] `docs/security/secrets.md` hardened: production application role gets only `SELECT, INSERT` on the two calculation tables specifically (not schema wide), migration role is a separately named DSN with DDL privileges used only during `alembic upgrade head`, never persisted in CI or Render env.

### Gates

* [x] QA: 138 backend + 57 frontend tests pass. tsc, eslint, prettier, ruff, mypy clean.
* [x] Security: Phase 6 review run by Security Engineer subagent. Sign off received with no critical or high severity findings; one low severity recommendation on production role wording was applied this phase (`docs/security/secrets.md`).
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.

### Notes for Phase 11

* The production deploy creates two roles (application + migration) per the threat model wording. The application DSN goes in Render env vars; the migration DSN never leaves Mustafa's dotfile shell session.
* CI integration test against a real Postgres (matrix the test suite over SQLite + Postgres) is deferred to Phase 11 because it requires CI environment changes; the in memory SQLite suite covers the ORM contract today.

---

## Phase 7: The Greeks [DONE]

**Owners**: Quant Domain Validator, Pricing Models Engineer, Backend Developer, Frontend Developer, QA Engineer.

**Window cost**: ~40% alone. Spanned two windows in practice (backend half landed in window 1 after Phase 6 closeout pushed usage high; frontend half resumed in window 2 from Resume notes).

### Deliverables

* [x] Closed form Greeks in `backend/app/pricing/black_scholes.py`: a `Greeks` dataclass plus `black_scholes_call_greeks` and `black_scholes_put_greeks` functions returning textbook math units (per unit sigma for vega, per unit r for rho, per year for theta; delta and gamma in natural units). Edge cases T=0, sigma=0, S=0 return zero Greeks by design (documented in `docs/risk/conventions.md`).
* [x] `POST /api/price` returns nested `call_greeks` and `put_greeks` of shape `GreeksDisplay`. The math-to-display layer (`_to_display` in `app/api/price.py`) rescales: vega per 1 percent sigma, rho per 1 percent r, theta per calendar day. Delta and gamma stay unscaled. Conversion is centralized in one place.
* [x] `frontend/src/components/GreeksPanel.tsx`: five-tile grid (Delta, Gamma, Theta, Vega, Rho). Each tile carries a Greek glyph (italic serif), a value (Newsreader tabular), a name (italic serif). 3 px left accent border cycles through primary, accent, amber, info, violet. aria-label includes display units (per day, per 1 percent of sigma, per 1 percent of r) for screen reader users.
* [x] `ResultPanel` now renders both `GreeksPanel` instances (Call and Put) below the call and put metric cards; the Greeks panels span both columns of the grid (`grid-column: 1 / -1`).
* [x] Property-based tests: put-call parity (C - P = S - K e^(-rT)), delta_call - delta_put = 1, call delta in [0, 1], put delta in [-1, 0], gamma non-negative and identical across legs, vega non-negative and identical across legs, plus reference values at the canonical Hull inputs.
* [x] Unit conversion documented in the math layer docstring; sigma=0 and T=0 zero-Greeks behavior added to `docs/risk/conventions.md` per Risk Reviewer recommendation.

### Gates

* [x] QA: 177 backend tests pass (was 138, +39 across new test_greeks.py and updated test_price.py). 64 frontend tests pass (was 57, +7 GreeksPanel tests, +1 ResultPanel test, +1 api.test.ts test for the new server response shape). tsc, eslint, prettier, ruff, mypy clean.
* [x] Security: no new endpoints; the Phase 4/6 reviews still apply. `GreeksDisplay` type guard rejects malformed responses with `kind: 'server'`.
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.
* [x] Risk and Financial Correctness Reviewer: subagent signed off with no blockers. Confirmed reference values at Hull canonical inputs (call delta 0.6368, put delta -0.3632, gamma 0.01876, vega per pct 0.3752, theta per day -0.01757 for call), sign conventions (long holder perspective), identities (gamma and vega equal across legs, delta sum equals 1), edge case handling, and unit scaling. One minor doc nit applied: documented the Greeks-at-deterministic-limits convention in `conventions.md`.
* [x] Live smoke test: `vega-serve` returned the full Greeks payload at canonical inputs matching Hull to 4+ decimals.

---

## Phase 8: Real market data [DONE]

**Owners**: Backend Developer, Frontend Developer, Security Engineer (third party request hardening).

**Window cost**: ~55% alone. Shipped solo (not bundled with Phase 7).

### Deliverables

* [x] `backend/app/services/tickers.py`: `TickerLookup` Protocol, `TickerQuote` dataclass, `CachedTickerLookup` (60s TTL, 256 entry LRU, `TickerNotFound` intentionally not cached), `YFinanceTickerLookup` adapter calling yfinance through a process wide `ThreadPoolExecutor` with `future.result(timeout=5.0)` for the hard 5 second budget. Threat model T6 controls live in three places: the FastAPI `Path(pattern=...)` constraint, a defence in depth `TICKER_RE.match` in the service module, and the frontend regex gate before fetch fires.
* [x] `backend/app/api/tickers.py`: `GET /api/tickers/{symbol}` returns a strict `TickerResponse` (`extra="forbid"`, four fields, positive finite price). Errors map to discrete HTTP statuses without leaking library internals: 404 not found, 504 upstream timeout, 502 upstream error, 422 invalid symbol.
* [x] `backend/tests/services/test_ticker_cache.py`: 6 unit tests for the TTL+LRU semantics (first call delegates, second call within TTL hits cache, expired refetches, distinct symbols cached independently, `TickerNotFound` is not cached, LRU evicts least recent).
* [x] `backend/tests/api/test_tickers.py`: 19 contract tests covering happy path, response shape lockdown (no extra fields), validation rejections (lowercase, bang, space, oversize, backslash, percent), path traversal patterns rejected by URL routing, 404/504/502 mappings, error message does not leak upstream class names, cache prevents the second upstream call, dot/dash symbols (BRK.B, BRK-B) accepted.
* [x] `frontend/src/lib/api.ts`: `fetchTicker(symbol, options)` with client side regex gate (short circuits before any network call), 6 second timeout, AbortController plumbing identical to `fetchPrice`/`fetchHeatmap`, `PriceErrorKind` extended with `not_found`/`upstream_timeout`/`upstream`. Path is built with `encodeURIComponent` after the regex check.
* [x] `frontend/src/components/TickerAutocomplete.tsx`: `tr-card` styled section with a search input (debounced 250ms), pending status, resolved quote line (symbol, name, formatted price), and an explicit "Use price" button. Errors surface in a `role="alert"` region. Selecting the price calls `onApply(quote)`; the parent decides what to do.
* [x] `frontend/src/screens/PricingScreen.tsx`: stacks the autocomplete above the InputForm in a new `[data-element="leftColumn"]` container; the `onTickerApply` callback aborts any in-flight pricing request and writes `quote.price` (rounded to 2 dp) into the asset price field.
* [x] 25 new backend tests (was 177; total now 202). 19 new frontend tests (was 64; total now 83).
* [x] Live integration smoke test: `YFinanceTickerLookup().lookup("AAPL")` returned `Apple Inc., $280.14, USD` against live Yahoo from the dev box.

### Gates

* [x] QA: 202 backend + 83 frontend tests pass. ruff, mypy, eslint, prettier, tsc clean. `pnpm build` produces a 219 KB JS bundle (68 KB gzip).
* [x] Security: Phase 8 review run by Security Engineer subagent. **Conditional pass with no blockers**, three accepted residual risks added to `docs/security/threat-model.md` T6 (response size cap not enforced because yfinance buffers internally; thread cancellation does not actually interrupt blocked socket reads; private address range block not needed because yfinance only hits hard coded Yahoo URLs and we never pass a user URL). Per route slowapi limit on `/api/tickers/{symbol}` deferred to Phase 10 with the heat map and backtest per route limits, consistent with the Phase 4 deferral. Guardrail added to `agents/08-security-engineer.md` Phase 8: any future change to `app/services/tickers.py` that accepts a URL parameter triggers a Security Engineer review.
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.

---

## Phase 9: Multiple pricing models [DONE]

**Owners**: Pricing Models Engineer, Frontend Developer, Risk Reviewer.

**Window cost**: ~70%. Came in well under the 95% budget because the binomial and Monte Carlo modules each compose cleanly with the existing pricing layer and the frontend reused `fetchPrice` for the parallel comparison fan out.

### Deliverables

* [x] `backend/app/pricing/binomial.py`: Cox Ross Rubinstein binomial tree, vectorized terminal layer plus scalar rollback. Default 500 steps. Edge cases (T=0, sigma=0, S=0) mirror Black Scholes. Numerical safety fallback when `(a - d) / (u - d)` leaves [0, 1] (extreme inputs with very low sigma and high `|r|`) returns the deterministic discounted forward, which is the correct sigma-collapses-to-zero limit.
* [x] `backend/app/pricing/monte_carlo.py`: GBM Monte Carlo with antithetic variates. Seeded `numpy.random.default_rng` for determinism. Default 100k paths. Odd path counts round up to the next even number so antithetic pairing is exact (preserves the unbiased estimator).
* [x] `backend/app/api/price.py`: `model: Literal['black_scholes', 'binomial', 'monte_carlo']` field on `PriceRequest`, default `black_scholes`. Routes call/put through the chosen pricer. Greeks are always returned from the closed form Black Scholes formula regardless of model (market practice; documented in `docs/risk/conventions.md`). Monte Carlo branch pins seed `4242` so the same payload returns the same number under repeat (UI stability).
* [x] `backend/app/api/heatmap.py`: `model` field on `HeatmapRequest`. Black Scholes uses the existing vectorized pricer; binomial runs scalar per cell at 100 steps; Monte Carlo runs scalar per cell at 20k paths with a deterministic per cell seed (`base + i * 21 + j`) so the grid is stable under repeat without making neighboring cells correlated. Reduced step / path counts versus the price endpoint trade some accuracy for responsiveness in a 21x21 grid.
* [x] `frontend/src/lib/api.ts`: `PricingModel` union, optional `model` field on `PriceRequest` and `HeatmapRequest`, required `model` on the response types, `isPriceResponse`/`isHeatmapResponse` type guards updated.
* [x] `frontend/src/components/ModelSelector.tsx`: three model tabs (`role="tab"` plus `aria-selected`) with a Compare toggle (`role="switch"` plus `aria-checked`). Tabs disable when Compare is on.
* [x] `frontend/src/components/ComparePanel.tsx`: side by side three column view of the resolved call and put per model, plus a header badge showing the largest call-side spread across the three models. Loading cells render `...` so the layout does not jump when one of the three responses arrives later than the others.
* [x] `frontend/src/screens/PricingScreen.tsx`: single mode dispatches one `fetchPrice({ ...inputs, model })`; compare mode fans out three parallel `fetchPrice` calls (one per model) with shared AbortController and renders `ComparePanel`. First validation error from any of the three drives the field-level invalid markers.
* [x] 67 new backend tests (was 178 in pricing+api; total now 245). 19 binomial unit tests, 14 Monte Carlo unit tests, 6 new price contract tests (default model, BS-binomial convergence, BS-MC convergence, Greeks identical across models, unknown model 422, MC determinism), 4 new heatmap contract tests (default model, binomial grid close, MC grid close, unknown model 422). 91 frontend tests (was 83; +5 ModelSelector +3 ComparePanel).
* [x] Live integration smoke test: at canonical Wilmott inputs (S=K=100, T=1, r=0.05, sigma=0.20) BS gives 10.4506/5.5735, binomial-500 gives 10.4466/5.5695 (|err| < 0.005), MC-100k seed=4242 gives 10.4783/5.5961 (|err| < 0.03).

### Gates

* [x] QA: 245 backend + 91 frontend tests pass. ruff, mypy, eslint, prettier, tsc clean. Vite build green (29 KB CSS, 222 KB JS, 69 KB gzip).
* [x] Security: no new endpoints; the model field passes through Pydantic Literal validation (unknown model returns 422). No new third-party calls. The Phase 4 / 6 / 8 reviews still apply. Per-route rate limit on price and heatmap remains deferred to Phase 10 alongside the backtest endpoint.
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.
* [x] Risk and Financial Correctness Reviewer: subagent **clean sign-off, no blockers**. Confirmed convergence at canonical inputs (binomial < 0.05, MC < 0.10), defended the Greeks-from-BS-always convention against market practice, validated the binomial fallback math and the MC odd-path-rounding bias-free property, and confirmed the per-cell MC seed scheme has no checkerboard pathology. Recommended doc additions: pricing model selection + Greeks convention + tolerances + numerical fallbacks in `docs/risk/conventions.md`; Cases 6 (cross-model agreement) and 7 (model divergence regime: deep OTM call near expiry) in `docs/risk/sanity-cases.md`. Both applied this phase.

---

## Phase 10: Backtesting [DONE]

**Owners**: Pricing Models Engineer plus Backend Developer (engine), Frontend Developer (chart), Performance Engineer, Risk Reviewer.

**Window cost**: ~50%. Came in well under the 95-99% budget because the backtest engine cleanly composes the existing Black Scholes pricer (one BS call per leg per day, microsecond cheap) and the yfinance integration reused the SSRF-guarded service pattern from Phase 8.

### Deliverables

* [x] `backend/app/services/historical.py`: `HistoricalLookup` Protocol with `YFinanceHistoricalLookup` adapter (calls `yf.Ticker(symbol).history(start, end, auto_adjust=True)` through a 2-worker `ThreadPoolExecutor` with hard 10 second timeout) and `CachedHistoricalLookup` wrapper (TTL 1 day, LRU 32 entries, NotFound deliberately not cached). Three exception types (`NotFoundError`, `UpstreamTimeoutError`, `UpstreamLookupError`) mirror the ticker service. `HISTORICAL_TICKER_RE` defence-in-depth on the symbol.
* [x] `backend/app/backtest/engine.py`: pure backtest engine. `Strategy` StrEnum (`LONG_CALL`, `LONG_PUT`, `STRADDLE`); `Leg` dataclass; `STRATEGY_LEGS` registry. `run_backtest(req)` enters at the first close (strike = entry close, ATM by construction), marks each leg via the analytical Black Scholes formula at `T = max(expiry - day, 0) / 365` (T=0 collapses to intrinsic via the existing BS short circuit). Returns dates, spot, position_value, pnl, strike, entry_basis, entry_date, expiry_date, legs. `MAX_DATES = 1300` (five years of trading days plus margin) aligned with the API date range cap.
* [x] `backend/app/api/backtest.py`: `POST /api/backtest` with strict Pydantic validation (symbol regex from threat model T6, date range cap of 5 years, dte cap of 365 days, sigma 0..10, r in [-1, 1]). Errors map to discrete HTTP statuses without leaking library internals: 404 ticker not found, 504 upstream timeout, 502 upstream error, 422 validation or insufficient data.
* [x] `frontend/src/lib/api.ts`: `BacktestStrategy` union, `BacktestRequest` and `BacktestResponse` interfaces, `fetchBacktest` with client side regex gate, 20 second timeout (longer than other endpoints because the cold path dominates), encodeURIComponent on the symbol, and full error mapping to the existing `PriceError` union.
* [x] `frontend/src/components/BacktestForm.tsx`: ticker input (uppercased), strategy `<select>`, start/end `<input type="date">`, DTE/sigma/r `NumField` rows. aria-invalid on field-level errors, aria-busy on the Run button while pending.
* [x] `frontend/src/components/BacktestChart.tsx`: inline SVG line chart with no third-party library. One polyline of P&L points; zero P&L gridline; 5 y-axis ticks and 5 x-axis ticks (yyyy-mm-dd → mm-dd). Stroke is the accent color (sea green) when final P&L is positive, primary (oxblood) when negative. Empty state placeholder when `result === null`.
* [x] `frontend/src/screens/BacktestScreen.tsx`: composes `BacktestForm` + `BacktestChart` in a 2-column layout. Owns the AbortController for in-flight fetches. Status/error regions split (`role='status'` + `role='alert'`).
* [x] App nav: replaced the Backtest placeholder with the real screen.
* [x] 41 new backend tests (was 245; total now 286): 6 historical service unit tests, 17 backtest engine tests including a perf assertion (`test_engine_perf_max_dates_straddle_under_50_ms`), 18 endpoint contract tests covering happy path, response shape lockdown, strategy dispatch, validation, upstream error mapping, error message authorship, insufficient-data 422.
* [x] 20 new frontend tests (was 91; total now 111): 9 fetchBacktest tests, 5 BacktestChart tests, 5 BacktestForm tests, 1 App nav test for the new screen.
* [x] Live integration smoke test against real Yahoo: AAPL long_call from 2026-01-02 to 2026-04-30 with sigma=0.30, r=0.05, dte=30. Returned 81 trading days in 697 ms, entry strike $270.76, basis $9.83, terminal P&L -$9.83 (option expired worthless because spot stayed below strike at expiry).

### Gates

* [x] QA: 286 backend + 111 frontend tests pass. ruff, mypy, eslint, prettier, tsc clean. Vite build green (30 KB CSS, 232 KB JS, 71 KB gzip).
* [x] Security: no new endpoints from a security perspective beyond the existing yfinance SSRF surface (T6 controls already documented for the ticker service apply identically here). Per-route slowapi limit on `/api/backtest` recommended by the Performance Engineer is **deferred to Phase 11 production hardening** alongside the per-route limits for `/api/tickers/{symbol}` and `/api/heatmap`. Documented as accepted residual risk in `docs/security/threat-model.md` T6: the existing 60/minute global per IP cap plus the 1-day TTL cache plus the 10-second hard timeout plus the engine's 1300 date cap together bound the abuse surface in the meantime.
* [x] Code Review: PM session reviewed the diff. No simplifications outstanding.
* [x] Risk and Financial Correctness Reviewer: subagent **conditional clean sign-off, no code blockers**. Code reads correctly: long-only sign convention applied per leg, T=0 intrinsic collapse via the BS short circuit, ATM-at-entry, time-decay sign on flat series, calendar-day expiry, single-date edge case rejected at the API boundary. Five new conventions documented in `docs/risk/conventions.md` (ATM at entry, constant sigma over trade life, close-to-close marking, calendar day expiry, long-only basis sign). Four new sanity cases added to `docs/risk/sanity-cases.md` (8a long call up move, 8b long put down move, 8c straddle big move, 8d long call expires worthless on flat series).
* [x] Performance Engineer: subagent **conditional sign-off, two MUST + one SHOULD applied this phase, one MUST deferred**. Applied: (1) raised engine `MAX_DATES` from 400 to 1300 to match the API's 5-year date range cap so the previous quiet-fail path no longer wastes an upstream round trip; (2) added a perf assertion test on the worst-case engine call (1300 day straddle under 50 ms; measured ~5 ms). Deferred: per-route `@limiter.limit("10/minute")` on `/api/backtest` (slowapi architectural refactor; lands in Phase 11). Pure engine cost confirmed at ~1.2 us per BS leg per day; response payload ~5 KB JSON for 81 days.

---

## Phase 11: Production deployment [DONE]

**Owners**: DevOps Engineer (lead), Security Engineer (final hardening), Documentation Engineer (setup guide).

**Window cost**: ~90% of one window. Reserve a fresh window because deployment requires the user to log in and click through three dashboards.

### Code deliverables (landed)

* [x] Per route slowapi limits, deferred from Phases 4 / 8 / 10:
  `/api/heatmap` 12/minute, `/api/tickers/{symbol}` 30/minute, `/api/backtest` 10/minute, plus `POST /api/calculations` 12/minute and `GET /api/calculations[/{id}]` 60/minute.
  New module `backend/app/core/rate_limit.py` holds the singleton `Limiter` so the per route decorators reference one instance; `application_limits` reads the env per request so existing rate limit tests continue to honor `VEGA_RATE_LIMIT_DEFAULT`.
* [x] **Compare and History screens** finished as full features (the dead Phase 3 nav placeholders shipped in earlier phases; this phase wires them end to end):
  - `GET /api/calculations` paginated list endpoint (newest first, `limit`/`offset` query params, response cap of 50 per page).
  - `CalculationInput.created_at` switched to a Python side default so SQLite (second precision) sorts fast successive writes correctly; Postgres still has `server_default=func.now()` for raw SQL writes.
  - Frontend: `saveCalculation`, `fetchCalculations`, `fetchCalculation` in `src/lib/api.ts`. Save button on Heat Map screen. New `HistoryScreen` with list and detail panes. Compare reuses `PricingScreen` with a new `initialCompare` prop and a distinct React `key` so the dedicated nav lands the user in compare mode and switching back to Pricing resets to single mode.
  - 9 new backend tests (list endpoint shape, pagination, ordering, validation, per route write cap) and 6 new frontend tests (HistoryScreen empty/list/detail/error states; App.test routing for Compare and History).
* [x] **DSN normalization defensive fix** (`backend/app/db/session.py::normalize_database_url`): rewrites bare `postgresql://` (the form Neon's "Connect manually" string hands you) to `postgresql+psycopg://` so a verbatim Neon paste does not crash production with `ModuleNotFoundError: No module named 'psycopg2'`. Alembic's env.py shares the helper.
* [x] 4 new backend tests for the per route caps (heatmap exhausts at 12, tickers at 30, backtest at 10, health stays 200). 295 backend tests pass (was 290).
* [x] Production fail loud on missing or unsafe `VEGA_CORS_ORIGINS`: empty, wildcard, or HTTP origins now raise `ConfigError` at boot in `backend/app/core/config.py`. 5 new env tests cover the matrix. Existing production fixture updated to provide a valid HTTPS origin.
* [x] Frontend production fail loud on missing or localhost `VITE_API_BASE_URL`: `readApiBaseUrl` in `frontend/src/lib/api.ts` throws on the first request when running a production bundle without a real backend URL. 3 new tests cover the matrix. 114 frontend tests pass (was 111).
* [x] `backend/Dockerfile`: multi stage build with uv, drops to a non root `vega` user, `vega-serve` as CMD. Pinned uv version for reproducibility.
* [x] `render.yaml` Blueprint at the repo root: web service `vega-backend`, docker runtime, free plan, Oregon, `/health` health check, env vars (production, log level, rate limit) plus `sync: false` placeholders for the two secrets the user pastes in the dashboard (`VEGA_CORS_ORIGINS`, `VEGA_DATABASE_URL`).
* [x] `frontend/public/_headers`: production CSP plus HSTS plus the same security headers the backend emits, plus aggressive `Cache-Control: immutable` on `/assets/*` and `must-revalidate` on `/index.html`. Verified the file lands in `dist/` after `pnpm build`.
* [x] `frontend/public/_redirects`: `/* /index.html 200` so a hard refresh on a non root path serves the SPA.
* [x] `docs/api.md`: hand edited reference page for the seven endpoints, with rate limit table, error response shape table, and example request/response bodies.
* [x] `docs/setup-guide.md`: rewritten end to end. Step 1 Neon (least privilege role creation in SQL), step 2 Render (Blueprint connect, paste two env vars), step 3 Cloudflare Pages (build settings, env vars), step 4 tie the loop closed, plus optional custom domain and a troubleshooting matrix.
* [x] `docs/security/secrets.md`: env var names match the actual code (`VEGA_*`), production fail loud paths documented, application vs migration role distinction tightened.
* [x] Dependency audit clean: `pip-audit` and `pnpm audit --prod` both report `No known vulnerabilities found`.
* [x] Backend production smoke test (locally with `VEGA_ENVIRONMENT=production` and a valid HTTPS CORS origin) returns 200 on `/health` and `/api/price`, 404 on `/docs` and `/openapi.json`, and refuses to boot when `VEGA_CORS_ORIGINS` is missing.

### User dashboard work (done)

* [x] Neon project created; `vega_app` application role with `SELECT, INSERT` only on the two calculation tables; password rotated mid Phase 11; owner DSN never persisted in CI or Render.
* [x] Render Blueprint connected; backend service `vega-backend` (final URL `https://vega-backend-1wm0.onrender.com`); env vars `VEGA_DATABASE_URL`, `VEGA_CORS_ORIGINS`, `VEGA_ENVIRONMENT=production`, `VEGA_LOG_LEVEL=INFO`, `VEGA_RATE_LIMIT_DEFAULT=60/minute`.
* [x] Cloudflare Pages connected; project `vega-2rd` (final URL `https://vega-2rd.pages.dev`); env vars `VITE_API_BASE_URL`, `NODE_VERSION=22`, `PNPM_VERSION=10`.
* [x] Render `VEGA_CORS_ORIGINS` set to the live Pages URL.
* [x] Live smoke test: `/health`, `POST /api/price`, `POST /api/heatmap`, `GET /api/calculations`, `POST /api/calculations`, CORS preflight from `https://vega-2rd.pages.dev` all 200; old `trader-backend-xsud` service deleted.
* [x] Project wide rename Trader -> Vega: GitHub repo `Mustafan4x/Vega`, Render service `vega-backend`, Cloudflare Pages `vega-2rd`, Postgres role `vega_app`, env vars `VEGA_*`, local working directory `/home/mustafa/src/vega/`. Greek `vega` in the math layer preserved.
* [x] Backward compat shim removed after Render env was on `VEGA_*` and the legacy `TRADER_*` env vars were deleted.

Branch protection plus Dependabot plus CodeQL are still optional follow ups on the GitHub repo; documented in `docs/setup-guide.md`.

### Gates

* [x] QA: 312 backend + 120 frontend tests pass; ruff, mypy, eslint, prettier, tsc all clean; Vite build green.
* [x] Security (code level): production fail loud paths land for both CORS and the frontend API base URL; per route rate limits close the deferred Phase 4 / 8 / 10 findings; `pip-audit` and `pnpm audit --prod` clean.
* [x] Security (live): HSTS preload eligibility verified on both Render and Cloudflare; production CSP from Cloudflare Pages, frame-ancestors from backend; no stack trace leak from the production error path; CORS allow list locked to the exact Pages origin; Neon `vega_app` role limited to `SELECT, INSERT` on the two calculation tables, password rotated.
* [x] Documentation Engineer: `docs/setup-guide.md` walked through end to end during the live deploy; `docs/api.md` published.

After Phase 11 closed, design changes follow the two flows in `CLAUDE.md` ("Design change workflow") and any new feature work goes through `docs/future-ideas.md`.

---

## Notes on bundling

The PM is permitted to bundle pairs of phases into a single window when the next phase is small enough and the current phase came in well under budget. Bundle candidates per `STATUS.md`: Phase 1 plus 2, Phase 5 plus 6, Phase 7 plus 8. Bundling is opt in: confirm with the user during the post phase check-in. Phase 10 is never bundled.

## Notes on design changes

Both design change flows from `CLAUDE.md` work at any time, including after Phase 11 ships:

* **Flow A**: user describes a change in plain English; the session edits React, Tailwind, and the canonical HTML directly. Logged as a one liner in `STATUS.md` ("Design sync log").
* **Flow B**: user replaces `docs/design/claude-design-output.html`; the PM diffs and dispatches the UI/UX Designer plus Frontend Developer.
