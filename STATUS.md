# Trader project status

Single source of truth for which phase is next. Read this file when the user says "work on the next phase" or any equivalent. Update this file when a phase changes state. The Project Manager session owns it.

**Last updated**: 2026-05-02 (Phase 0 closed)

## Next phase

**Phase 1: Python REPL Black Scholes** (likely bundled with Phase 2: FastAPI backend in the same window).

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
| 1 | Python REPL Black Scholes | not started | | ~30% alone | bundle candidate with Phase 2 |
| 2 | FastAPI backend | not started | | ~60% alone, ~95% with Phase 1 | |
| 3 | React frontend MVP | not started | | ~95% | |
| 4 | Heat map visualization | not started | | ~90% | |
| 5 | P&L heat map | not started | | ~40% alone | bundle candidate with Phase 6 |
| 6 | Persistence | not started | | ~60% alone, ~95% with Phase 5 | |
| 7 | The Greeks | not started | | ~40% alone | bundle candidate with Phase 8 |
| 8 | Real market data | not started | | ~55% alone, ~95% with Phase 7 | |
| 9 | Multiple pricing models | not started | | ~95% | |
| 10 | Backtesting | not started | | ~95 to 99% | do not bundle anything else |
| 11 | Production deployment | not started | | ~90% | reserve a fresh window |

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
