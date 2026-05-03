# Trader project status

Single source of truth for which phase is next. Read this file when the user says "work on the next phase" or any equivalent. Update this file when a phase changes state. The Project Manager session owns it.

**Last updated**: 2026-05-03 (Phase 4 opened).

## Next phase

**Phase 4: Heat map visualization.** In progress. Adds a vectorized `POST /api/heatmap` endpoint and a `HeatMap` React component with a canvas painter plus a transparent hit grid. Started with usage already at 68 percent and 34 minutes to reset; aiming to land the backend half (vectorized pricing plus the endpoint plus tests) before the window cap and resume the frontend half in the next window.

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
| 4 | Heat map visualization | paused | | ~90% | backend half landed (commit a6a427e); resume notes name the next concrete frontend task |
| 5 | P&L heat map | not started | | ~40% alone | bundle candidate with Phase 6 |
| 6 | Persistence | not started | | ~60% alone, ~95% with Phase 5 | |
| 7 | The Greeks | not started | | ~40% alone | bundle candidate with Phase 8 |
| 8 | Real market data | not started | | ~55% alone, ~95% with Phase 7 | |
| 9 | Multiple pricing models | not started | | ~95% | |
| 10 | Backtesting | not started | | ~95 to 99% | do not bundle anything else |
| 11 | Production deployment | not started | | ~90% | reserve a fresh window |

## Resume notes

If a phase was paused mid way (e.g., usage hit 90 percent), the PM writes a one paragraph note here naming the last clean commit and the resume point. Otherwise this section stays empty.

**Phase 4 paused 2026-05-03 at commit `a6a427e` (backend half).** The vectorized Black Scholes pricer (`backend/app/pricing/black_scholes_vec.py`) and the `POST /api/heatmap` endpoint (`backend/app/api/heatmap.py`) are live, with 35 new tests (12 vec pricer plus 23 endpoint contract). 21x21 grid responds in under 1 ms cold for the math itself; full perf will be revisited during the Performance Engineer dispatch in the next window. The frontend half is what remains: (1) `frontend/src/lib/heatMapColors.ts` with the segmented linear interpolator and the three color stop constants from `docs/design/wireframes.md` heat map color scale spec, with unit tests; (2) extend `frontend/src/lib/api.ts` with `fetchHeatmap()` mirroring `fetchPrice` (timeout, AbortController, PriceError union); (3) `frontend/src/components/HeatMap.tsx` with a 240x240 canvas painter doing bilinear interpolation across the grid and a transparent CSS grid overlay (`[data-element="hitGrid"]`) of `[data-element="cell"]` divs for hover; (4) `frontend/src/components/HeatMapControls.tsx` for vol shock, spot shock, and resolution selectors; (5) `frontend/src/screens/HeatMapScreen.tsx` wiring the controls plus two HeatMaps (call, put) side by side; (6) Vitest tests for the color module, the API client extension, and the screen; (7) live smoke test, then dispatch Performance Engineer and Security Engineer reviews; (8) update `docs/plan.md`, `STATUS.md`, and the token tracker, commit, push, run the mandatory check-in. Anatomy and color scale spec are in `docs/design/wireframes.md` lines 86 to 178; the canonical reference function is `HeatMap` at `docs/design/claude-design-output.html` line 1377 onward (canvas painter, color stops, overlay hit grid). The Phase 4 task list (#38 through #45) on the in session task list captures the remaining work order.

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
