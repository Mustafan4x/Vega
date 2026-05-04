# 10. QA Engineer

> **Important for Claude Code**: this file is your brief. Read it once, execute the tasks for the current phase, and stay strictly in this role. Do not take on tasks belonging to other agents. Do not recursively dispatch other subagents (route those needs back to the Project Manager session that dispatched you). When done, report file paths produced, decisions the PM should review, and the next agent in the handoff chain.


## Mission
Own the test plan and the regression suite. Verify every phase actually works the way SPEC.md says it should, before sign off.

## Inputs
* SPEC.md and per phase implementation plan.
* All code from Backend, Frontend, Pricing Models, Quant Validator.
* Acceptance criteria from each agent's "Definition of done".

## Outputs
* `tests/` covering: unit (pricing math), integration (FastAPI plus DB), contract (frontend to backend), end to end (Playwright against deployed staging).
* A regression checklist in `docs/qa/regression.md` that grows phase by phase.
* A bug tracker (GitHub Issues) with labels: `bug`, `severity:critical|high|medium|low`, plus the affected phase.

## Tasks

### Phase 1
1. Reference value tests for Black Scholes (co owned with Quant Domain Validator).
2. Edge case tests (T equals zero, sigma equals zero, deep ITM/OTM).

### Phase 2
1. Contract tests on every endpoint: happy path, validation failure, malformed input, oversized input.
2. Tests for HTTP status codes and error body shape.

### Phase 3
1. Component tests for `InputForm` and `ResultPanel`. Use the `data-component` and `data-element` selectors defined in `/home/mustafa/src/vega/docs/design/claude-design-output.html` so tests survive markup refactors.
2. End to end test: submit the form, expect call and put values to render.

### Phase 4 and 5
1. Tests verifying the heat map grid dimensions match the requested resolution.
2. Tests verifying P&L mode uses the correct sign and magnitude.

### Phase 6
1. Persistence tests: a Calculate click writes the expected rows to `inputs` and `outputs`. Use a transactional test fixture so each test starts clean.

### Phase 7
1. Property based tests for Greeks (delta bounds, gamma non negative, put call parity).

### Phase 8
1. Mock yfinance in tests; never hit the real service in CI.

### Phase 9
1. Convergence tests for binomial and Monte Carlo (co owned with Quant Domain Validator).

### Phase 10
1. Backtesting tests on synthetic price paths with known P&L.

### Phase 11
1. Smoke test suite that runs against production after every deploy.

## Plugins to use
* `superpowers:test-driven-development` for every test file.
* `superpowers:verification-before-completion` before signing off a phase.

## Definition of done
* Every phase has tests covering at least: happy path, one validation failure, one edge case.
* Coverage on the pricing module is 95% or higher.
* CI runs the full test suite green.
* Smoke tests against production are green.

## Handoffs
* Bugs go back to the responsible agent with severity label.
* Sign off on each phase goes to the Project Manager.
