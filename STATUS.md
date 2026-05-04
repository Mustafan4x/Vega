# Vega project status

Single source of truth for which phase is next. Read this file when the user says "work on the next phase" or any equivalent. Update this file when a phase changes state. The Project Manager session owns it.

**Last updated**: 2026-05-04 (Phase 11 closed; v1 shipped).

## Next phase

**v1 is shipped.** Frontend at <https://vega-2rd.pages.dev/>, backend at <https://vega-backend-1wm0.onrender.com>, Postgres on Neon. There is no next phase from the spec; design changes follow the two flows in `CLAUDE.md` ("Design change workflow") and any new feature work goes through `docs/future-ideas.md`.

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

## Resume notes

If a phase was paused mid way (e.g., usage hit 90 percent), the PM writes a one paragraph note here naming the last clean commit and the resume point. Otherwise this section stays empty.

(empty)

## Design sync log

The user can change the design at any time, including after Phase 11 ships, via either flow in `CLAUDE.md` ("Design change workflow"):

* **Flow A** (direct from terminal): user describes the change in plain English, the session edits React, Tailwind, and the HTML directly.
* **Flow B** (Claude Design round trip): user replaces `docs/design/claude-design-output.html`, the session diffs and dispatches.

Both flows write one line here per change, prefixed with the flow letter.

Format: `YYYY-MM-DD [A or B]: <one line summary of what changed and which components were updated>`.

(empty)

## How to update this file

The Project Manager session must update this file at three moments:

1. **Starting a phase**: change status from `not started` to `in progress`, set the date in the "Last updated" line, and update the **Next phase** field to name the phase being started.
2. **Pausing mid phase**: change status to `paused`, write a Resume notes entry naming the commit ref and the next concrete task.
3. **Completing a phase**: change status to `completed`, fill in the "Completed on" date, and update the **Next phase** field to the next not-started phase. If the next phase is bundled with the one just completed, mark that phase `bundled with phase N` and skip to the one after.

Never edit any other field unless explicitly asked. Never reorder rows.
