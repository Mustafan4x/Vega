# Vega project status

Single source of truth for which phase is next. Read this file when the user says "work on the next phase" or any equivalent. Update this file when a phase changes state. The Project Manager session owns it.

**Last updated**: 2026-05-05 (post v1+1 polish: dividends `q` shipped across the full surface).

## Next phase

**No spec phase remaining.** Phase 12 closed v1+1. The next deferred polish item from the maintainer's private `future-ideas.md` is "Logo, favicon, and tab title".

## Phase status table

Status values: `not started`, `in progress`, `completed`, `bundled with phase N` (when this phase shipped together with another phase in the same window), `paused` (mid phase, see Resume notes).

| # | Phase | Status | Completed on | Window cost | Notes |
|---|---|---|---|---|---|
| 0 | Foundations | completed | 2026-05-02 | ~95% | scaffolds, plan, threat model, design tokens, ADRs all landed; first commit on `main` is c47e561 |
| 1 | Python REPL Black Scholes | completed | 2026-05-02 | ~30% alone | shipped solo (commit 8a0735e); 38/38 tests pass; REPL produces textbook Wilmott values |
| 2 | FastAPI backend | completed | 2026-05-03 | ~60% alone | 85/85 tests pass; POST /api/price live, security headers, rate limit, structured logs; Security Engineer signed off |
| 3 | React frontend MVP | completed | 2026-05-03 | ~95% | LayoutShell, InputForm, ResultPanel wired end to end against Phase 2 backend; 24 Vitest tests; Security and a11y reviews signed off |
| 4 | Heat map visualization | completed | 2026-05-03 | ~90% | spanned two windows; backend at a6a427e, frontend follow-up; 28 endpoint tests, 50 frontend tests; canvas painter live; Security signed off |
| 5 | P&L heat map | completed | 2026-05-03 | ~40% alone | shipped solo; 7 new tests, Risk Reviewer signed off; wireframes spec aligned |
| 6 | Persistence | completed | 2026-05-03 | ~60% alone | shipped solo; SQLAlchemy 2.x models, Alembic migration, POST/GET /api/calculations, 13 new contract tests; Security signed off |
| 7 | The Greeks | completed | 2026-05-03 | ~40% alone | spanned two windows (backend at 82936f2, frontend follow-up); 39 new backend tests + 9 new frontend tests; Risk Reviewer signed off |
| 8 | Real market data | completed | 2026-05-03 | ~55% alone | shipped solo; 25 new backend tests + 19 new frontend tests; live AAPL smoke test green; Security Engineer conditional pass (no blockers); three T6 residual risks documented |
| 9 | Multiple pricing models | completed | 2026-05-03 | ~70% (well under budget) | binomial CRR + Monte Carlo (antithetic) added; `model` param on price and heatmap; ModelSelector + ComparePanel; 67 new backend tests + 8 new frontend tests; live three-model convergence verified; Risk Reviewer clean sign-off |
| 10 | Backtesting | completed | 2026-05-03 | ~50% (well under budget) | shipped solo; pure backtest engine + yfinance historical service + POST /api/backtest + frontend BacktestForm/BacktestChart/BacktestScreen; 41 new backend tests + 20 new frontend tests; live AAPL smoke test green; Risk Reviewer + Performance Engineer both signed off (per-route rate limit deferred to Phase 11) |
| 11 | Production deployment | completed | 2026-05-04 | ~95% | per-route rate limits closed (heatmap 12/min, tickers 30/min, backtest 10/min, calculations write 12/min, read 60/min); production fail-loud on missing CORS and missing API base URL; render.yaml + Dockerfile (uv multi-stage, non-root); CF Pages _headers (CSP, HSTS) + _redirects (SPA fallback); docs/api.md and end-to-end docs/setup-guide.md polished; pip-audit and pnpm audit clean; live deploy at vega-2rd.pages.dev / vega-backend-1wm0.onrender.com / Neon; project-wide rename Trader -> Vega including code, env vars, docs, GitHub repo, Render service, CF Pages project, Neon application role (vega_app), Neon password rotated, local folder /home/mustafa/src/vega/; 312 backend + 120 frontend tests pass |
| 12 | Authentication and per user history | completed | 2026-05-04 | ~1 full window (split across two sessions) | Auth0 + Google/GitHub OAuth via `@auth0/auth0-react`; backend RS256 JWT verification with JWKS cache, audience and issuer checks; `user_id NOT NULL` on `calculation_inputs` with composite `(user_id, created_at DESC)` index; existing rows truncated at migration; cross-user isolation enforced (404 on IDOR); logged-out Save funnel replays via `appState.pendingSave` after Auth0 redirect; `<AuthCallback />` route at `/callback`; CSP `_headers` allows `*.auth0.com` (connect-src, frame-src, img-src plus Gravatar); STRIDE addendum to threat model; Auth0 setup section in `docs/setup-guide.md` plus six new env vars in the secrets reference and Auth0 in the Accounts list; 329 backend + 127 frontend tests pass; pip-audit + pnpm audit clean. Plan: docs/superpowers/plans/2026-05-04-auth-and-per-user-history.md. Spec: docs/superpowers/specs/2026-05-04-auth-and-per-user-history-design.md |

## Resume notes

### 2026-05-04: Phase 12 paused mid frontend

**Why paused**: end of usage window for the day. Resuming next session after the user's Claude Max window resets, in a fresh chat. This entry tells that session everything it needs to pick up exactly where we left off.

**Branch state**:

* Working branch: `phase-12-auth-design`.
* Last code commit: `e20a9ce` (Bundle 2: AuthButtons, LayoutShell footer, HistoryScreen auth branch).
* Last commit overall is this Resume notes commit on top of `e20a9ce`. Both local and `origin/phase-12-auth-design` should match after the push that closes this session.
* Working tree must be clean before resume; if it is not, `git status` will show why and the next session must investigate before doing anything else.

**Where to start in the next session** (read everything in this order):

1. `/home/mustafa/src/vega/CLAUDE.md` (auto loaded; project conventions).
2. `/home/mustafa/src/vega/STATUS.md` (this file; this Resume notes section is the most up to date statement of what has happened).
3. `/home/mustafa/src/vega/docs/superpowers/specs/2026-05-04-auth-and-per-user-history-design.md` (the design spec; the contract).
4. `/home/mustafa/src/vega/docs/superpowers/plans/2026-05-04-auth-and-per-user-history.md` (the 24 task implementation plan; tasks completed are listed below).
5. Switch to the branch and confirm: `git checkout phase-12-auth-design && git pull --ff-only && git status`.
6. Sanity test: `uv --project backend run pytest -q` should report 329 passed; `pnpm --filter frontend test --run` should report 124 passed.
7. Resume at Bundle 3 (Tasks 18 and 19 of the plan).

**Commits already on the branch** (oldest to newest; see `git log --oneline phase-12-auth-design ^main` for the live list):

| Plan ref | SHA prefix | Message |
|---|---|---|
| Pre-work | dac5fce | Phase 12 design: auth and per user history spec |
| Pre-work | f00d1b0 | Phase 12 plan: implementation plan for auth and per user history |
| Task 0 | 2bb3f56 | Phase 12 open: STATUS.md row, in-progress flag |
| Task 1 | f5cd786 | Phase 12: add pyjwt[crypto] dependency |
| Task 2 | 0c4aa35 | Phase 12 backend: Auth0 settings (domain, audience) with prod fail-loud |
| Task 3 | 65720c4 | Phase 12 backend: JWT auth dependency with JWKS verification |
| Task 4 | 6738840 | Phase 12 migration: drop rows, add user_id NOT NULL, composite index |
| Task 5 | a4053fd | Phase 12 model: CalculationInput.user_id (String(64), NOT NULL) |
| Task 6 | f1a7591 | Phase 12 tests: existing /api/calculations tests use auth_headers |
| Tasks 7+8 (bundled) | 4baa15b | Phase 12 backend: gate POST/GET endpoints, filter by user_id, isolation tests |
| Task 9 | 5981189 | Phase 12 IaC: declare VEGA_AUTH0_* env vars in render.yaml |
| Tasks 11 to 14 (Bundle 1) | baa7de5 | Phase 12 frontend: SDK install, Auth0Provider, test mock, authedFetch |
| Tasks 15 to 17 (Bundle 2) | e20a9ce | Phase 12 frontend: AuthButtons, LayoutShell footer, HistoryScreen auth branch |

Task 10 (push branch + resume notes scaffold) was effectively absorbed by the Task 9 push; no separate commit was needed.

**What is pending**:

* **Bundle 3 (plan Tasks 18, 19)**:
  * `frontend/src/screens/HeatMapScreen.tsx`: `onSave` branches on `isAuthenticated`. Logged in: call `getAccessTokenSilently()` and pass `bearerToken` to `saveCalculation`. Logged out: call `loginWithRedirect({ appState: { pendingSave: { request, response } } })`. Save button label changes to "Sign in to save" when logged out.
  * Create `frontend/src/screens/HeatMapScreen.test.tsx` (does not exist today): two tests covering the logged out and logged in branches.
  * Create `frontend/src/lib/auth-callback.tsx`: tiny route handler that calls `handleRedirectCallback`, reads `appState.pendingSave`, replays one save with the bearer token, then `window.history.replaceState({}, '', '/')`. Use a `useRef` guard so React StrictMode's double mount does not double-replay.
  * Create `frontend/src/lib/auth-callback.test.tsx`.
  * Modify `frontend/src/App.tsx` to render `<AuthCallback />` when `window.location.pathname === '/callback'`. Manual pathname check is enough; the project does not yet have a router.
  * The plan has the exact code and test bodies for all of these.
* **Bundle 4 (plan Tasks 20, 21, 22)**:
  * `frontend/public/_headers`: CSP `connect-src` and `frame-src` add `https://*.auth0.com`; `img-src` adds `https://s.gravatar.com https://*.auth0.com`.
  * `docs/security/threat-model.md`: append the Phase 12 STRIDE addendum.
  * `docs/setup-guide.md`: append the Auth0 setup section (Application + API setup, callback URLs, env vars).
* **Bundle 5 (plan Tasks 23, 24)**:
  * Final smoke: backend pytest + ruff + mypy; frontend test + lint + tsc + build; pip-audit + pnpm audit.
  * Flip Phase 12 row in this file to `completed`, fill `Completed on`, write the next-phase line (next deferred polish item from the gitignored ideas file: logo, favicon, tab title).
  * Append a Phase 12 block to `~/src/tracker/total_token_usage.md` (file lives outside the repo) per the convention in CLAUDE.md.
  * `git push`, then `gh pr create` with the title and body in the plan, then `gh pr checks <N> --watch --interval 10`, then `gh pr merge <N> --squash --delete-branch --admin` once green. Per CLAUDE.md push protocol the admin merge is pre-authorized for this solo repo.
  * After merge: `git checkout main && git pull --ff-only`. Optional manual smoke against the live deploy.

**Known fixtures and patterns to reuse, not reinvent**:

* Backend `tests/conftest.py` has `rsa_keypair` (session-scoped), `_patched_jwks` (autouse), `auth_token`, `auth_headers`. Tests sign tokens with a per session test RSA keypair; the JWKS cache is monkey-patched so urllib never hits Auth0.
* Frontend `src/test/auth0-mock.ts` exports `MockAuth0State`, `makeAuth0Mock`, `setAuth0MockState`, `getAuth0MockState`, `resetAuth0MockState`. Test files using it MUST add this at module top level (before any other import that might transitively pull `@auth0/auth0-react`):

  ```tsx
  import { vi } from 'vitest'
  import { getAuth0MockState } from '../test/auth0-mock'

  vi.mock('@auth0/auth0-react', () => ({
    useAuth0: () => getAuth0MockState(),
    Auth0Provider: ({ children }: { children: unknown }) => children,
  }))
  ```

  `vi.mock` is hoisted by vitest at parse time; calling it inside a function or `beforeEach` does not work.
* `frontend/src/lib/api.ts` already accepts `bearerToken?: string` on `FetchOptions`. The three calculations api functions (`saveCalculation`, `fetchCalculations`, `fetchCalculation`) accept it. `PriceErrorKind` includes `'unauthorized'` for 401 responses.

**Adaptations made versus the plan** (so the next session does not unwind them):

* Task 2: implementer also updated the existing `production_client` fixture and `test_production_accepts_multiple_https_origins` in `test_environment.py` to set `VEGA_AUTH0_DOMAIN` / `VEGA_AUTH0_AUDIENCE`, because the new prod fail-loud check otherwise broke them. Two-line addition per fixture.
* Task 3: imports moved to top of `tests/conftest.py` to satisfy ruff E402; `Callable` switched from `typing` to `collections.abc`; the unused `import json` was dropped.
* Task 4: simple `add_column` worked on SQLite (rows were DELETEd first); no `batch_alter_table` was needed.
* Tasks 7 and 8 were bundled into one commit (`4baa15b`) because Task 7 alone leaves the suite in a deeper red and Task 8 unwinds it.
* Bundle 1 (Tasks 11 to 14) landed as one combined commit (`baa7de5`) instead of four separate commits.
* Bundle 2 (Tasks 15 to 17) landed as one combined commit (`e20a9ce`). Existing `HistoryScreen` tests now seed `isAuthenticated: true` in their `beforeEach` so they continue to exercise the original list/detail-fetch path despite the new auth branch.

**Test counts at pause**:

* Backend: 329 pass.
* Frontend: 124 pass (was 120 before Phase 12).
* mypy: 2 pre-existing yfinance `import-untyped` warnings only (unchanged from before Phase 12).

**Workflow context for the resuming session**:

* The user runs Phase 12 via `superpowers:subagent-driven-development`, dispatching subagents per bundle. Sonnet for integration work, haiku for mechanical edits. Bundles tend to be 30k to 100k subagent tokens each.
* The user wants per-bundle pause-and-confirm. Do NOT auto-advance through Bundle 3, 4, or 5 without an explicit "go" or "finish bundle N" or equivalent. After Bundle 5 the phase is complete and the standing push protocol takes over for the merge.
* Cumulative subagent tokens spent on Phase 12 implementation so far: roughly 459k. Tasks 18 to 24 are estimated at 150k to 200k more.

**STATUS.md update protocol**:

When resuming, the first concrete action after sanity checks is to flip this Phase 12 row from `paused` back to `in progress` and update "Last updated". Do that before any code work. When the phase finally closes, follow the standard "Completing a phase" rules in the "How to update this file" section below.

## Design sync log

The user can change the design at any time, including after Phase 11 ships, via either flow in `CLAUDE.md` ("Design change workflow"):

* **Flow A** (direct from terminal): user describes the change in plain English, the session edits React, Tailwind, and the HTML directly.
* **Flow B** (Claude Design round trip): user replaces `docs/design/claude-design-output.html`, the session diffs and dispatches.

Both flows write one line here per change, prefixed with the flow letter.

Format: `YYYY-MM-DD [A or B]: <one line summary of what changed and which components were updated>`.

2026-05-05 A: dividends `q` field added to InputForm, HeatMapControls (via reuse), BacktestForm; new `psi` row added to GreeksPanel with `rose` accent token; `q` rendered in HistoryScreen summary table column and detail card inputs strip.

## How to update this file

The Project Manager session must update this file at three moments:

1. **Starting a phase**: change status from `not started` to `in progress`, set the date in the "Last updated" line, and update the **Next phase** field to name the phase being started.
2. **Pausing mid phase**: change status to `paused`, write a Resume notes entry naming the commit ref and the next concrete task.
3. **Completing a phase**: change status to `completed`, fill in the "Completed on" date, and update the **Next phase** field to the next not-started phase. If the next phase is bundled with the one just completed, mark that phase `bundled with phase N` and skip to the one after.

Never edit any other field unless explicitly asked. Never reorder rows.
