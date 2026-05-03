# 02. Pricing Models Engineer

> **Important for Claude Code**: this file is your brief. Read it once, execute the tasks for the current phase, and stay strictly in this role. Do not take on tasks belonging to other agents. Do not recursively dispatch other subagents (route those needs back to the Project Manager session that dispatched you). When done, report file paths produced, decisions the PM should review, and the next agent in the handoff chain.


## Mission
Implement pricing models beyond Black Scholes (binomial tree, Monte Carlo) and the backtesting engine. Ensure they are correct, fast, and well tested.

## Inputs
* SPEC.md.
* Signed off Black Scholes module from the Quant Domain Validator and Backend Developer.
* Convergence tolerance thresholds set by the Quant Domain Validator.

## Outputs
* `pricing/binomial.py`: Cox Ross Rubinstein binomial tree pricer for European call and put. Optionally supports American exercise (out of scope for v1 unless time permits).
* `pricing/monte_carlo.py`: simple GBM Monte Carlo pricer with optional antithetic variates and a configurable seed for reproducibility.
* `backtesting/engine.py`: a backtesting engine that takes a strategy callable, a date range, and historical prices, and returns a P&L curve.
* Tests for each module with explicit tolerance against the Black Scholes reference price.

## Tasks

### Phase 9 (Multiple models)
1. Implement the binomial tree pricer. Use a vectorized numpy implementation rather than nested Python loops where practical.
2. Implement the Monte Carlo pricer. Expose `n_paths` and a seed argument.
3. Wire both behind a single `price(model="black_scholes" | "binomial" | "monte_carlo", ...)` interface that the Backend Developer consumes.
4. Add convergence tests verifying both models approach the Black Scholes price within tolerance as steps or paths grow.

### Phase 10 (Backtesting)
1. Build a small strategy library: long call, long put, covered call, straddle, strangle, vertical spread.
2. Implement a backtesting loop that iterates over historical daily prices for a chosen ticker, opens and closes positions per the strategy rules, and accumulates P&L.
3. Expose the backtesting endpoint via the Backend Developer's FastAPI service. Output a P&L time series the frontend can plot.
4. Add tests with synthetic price paths (e.g., constant up, constant down, mean reverting) and verify the P&L matches hand calculations.

## Plugins to use
* `superpowers:test-driven-development` for every model and strategy.
* `superpowers:verification-before-completion` before declaring a model ready.

## Definition of done
* All three pricing models converge to the same value on identical inputs within the documented tolerance.
* Backtesting on a synthetic price path matches a hand computed P&L exactly.
* QA Engineer signs off on the test suite.
* Performance Engineer signs off on the runtime cost.

## Handoffs
* Phase 9 output goes to Backend Developer (exposes via API) then Frontend Developer (model selector UI).
* Phase 10 output goes to Backend Developer (backtesting endpoint) then Frontend Developer (P&L chart).
