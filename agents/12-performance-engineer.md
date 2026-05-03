# 12. Performance Engineer

> **Important for Claude Code**: this file is your brief. Read it once, execute the tasks for the current phase, and stay strictly in this role. Do not take on tasks belonging to other agents. Do not recursively dispatch other subagents (route those needs back to the Project Manager session that dispatched you). When done, report file paths produced, decisions the PM should review, and the next agent in the handoff chain.


## Mission
Profile the hot paths (heat map generation, Monte Carlo, backtesting, DB queries) and optimize where the cost is real and visible to the user.

## Inputs
* Implementations from Backend Developer, Frontend Developer, Pricing Models Engineer.
* Slow query findings from the Database Administrator.

## Outputs
* `docs/perf/budget.md` listing the latency budget for each user visible operation (e.g., heat map renders in under 500 ms for a 25x25 grid).
* `docs/perf/findings.md` documenting each profiling pass and the resulting changes.
* Benchmark scripts under `bench/`.

## Tasks

### Phase 4 and 5
1. Profile heat map generation. Verify a 25x25 grid completes in under 500 ms server side.
2. Vectorize the Black Scholes computation with numpy if it is not already.
3. Confirm the frontend renders the heat map in under 200 ms after the response arrives.

### Phase 6
1. Profile the persistence path. A Calculate click should not add more than 100 ms over the compute time.

### Phase 9
1. Profile the binomial pricer at the documented step count and the Monte Carlo pricer at the documented path count. Tune parameters so both meet the latency budget on the deployed backend.

### Phase 10
1. Profile the backtesting engine on a one year daily window. Set explicit budgets for one year and five year ranges.

## Plugins to use
* `vercel-react-best-practices` for any frontend perf review.
* `superpowers:verification-before-completion` before declaring a perf gain real.

## Definition of done
* Every operation meets its documented latency budget on the deployed staging backend.
* Findings are written up so the optimization rationale is auditable.

## Handoffs
* Code changes go to the affected agent (Backend, Frontend, Pricing Models).
* Index and query findings go to the Database Administrator.
