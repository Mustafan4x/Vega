# Trader project status

Single source of truth for which phase is next. Read this file when the user says "work on the next phase" or any equivalent. Update this file when a phase changes state. The Project Manager session owns it.

**Last updated**: 2026-05-03 (Phase 7 opened).

## Next phase

**Phase 7: The Greeks.** In progress at 72 percent usage; aiming to land the backend half (closed form Greeks math, tests, endpoint update) before the window cap and resume the frontend `GreeksPanel` plus Risk Reviewer in the next window.

If you are reading this file because the user just said "work on the next phase", do the following:

1. Confirm that "Phase 0" is still listed as next (the value above), in case this file has drifted from the table below.
2. Read `CLAUDE.md` for the session role rules and the pacing protocol.
3. Read `SPEC.md` for the phase scope and the window cost estimate.
4. Read `agents/00-project-manager.md` for the Project Manager brief.
5. Begin the phase per the PM brief.

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
| 7 | The Greeks | paused | | ~40% alone | backend half landed; resume notes name the next concrete frontend task |
| 8 | Real market data | not started | | ~55% alone, ~95% with Phase 7 | |
| 9 | Multiple pricing models | not started | | ~95% | |
| 10 | Backtesting | not started | | ~95 to 99% | do not bundle anything else |
| 11 | Production deployment | not started | | ~90% | reserve a fresh window |

## Resume notes

If a phase was paused mid way (e.g., usage hit 90 percent), the PM writes a one paragraph note here naming the last clean commit and the resume point. Otherwise this section stays empty.

**Phase 7 paused 2026-05-03 after the backend half.** Closed form Greeks (delta, gamma, theta, vega, rho) live in `backend/app/pricing/black_scholes.py` as `black_scholes_call_greeks` and `black_scholes_put_greeks` returning a `Greeks` dataclass in textbook math units. The API at `POST /api/price` returns `call_greeks` and `put_greeks` as nested objects in trader friendly display units (vega per 1 percent sigma, rho per 1 percent r, theta per calendar day; delta and gamma in their natural units). 37 new pricing tests cover reference values at the canonical `S=K=100, T=1, r=0.05, sigma=0.20` per Hull, put call parity, delta bounds, gamma sign and call/put identity, vega sign and call/put identity, and edge cases (T=0, sigma=0, invalid inputs). 177 backend tests pass total (was 138, +39 across the new test file and three updates to `test_price.py`). The frontend half remains: (1) extend `frontend/src/lib/api.ts` `PriceResponse` with `call_greeks` and `put_greeks` typed as the Pydantic display shape, (2) build `frontend/src/components/GreeksPanel.tsx` per the canonical reference at `docs/design/claude-design-output.html` lines 1330 to 1350 (five tile grid with Delta, Gamma, Theta, Vega, Rho, each tile carrying a glyph, value, and name; left accent border that cycles through primary, accent, amber, info, violet), (3) wire it into `PricingScreen.tsx` and `ResultPanel.tsx` so the panel renders below the call and put cards, (4) Vitest tests for the panel rendering all five values from a mocked API response, (5) live smoke test, then dispatch the Risk and Financial Correctness Reviewer for the formal Phase 7 sign off (gate Risk Reviewer per `SPEC.md`), (6) plan/STATUS/tracker updates and the mandatory check-in. Wireframes section is in `docs/design/wireframes.md` Pricing screen "Greeks panel" subsection.

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
