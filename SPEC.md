# Vega: Black Scholes Options Pricer

## Project summary

A full stack Black Scholes options pricer built as a quant interview pet project. The build follows the incremental path described in the source video (REPL, then GUI, then heat map, then P&L heat map, then database persistence) and extends it with the Greeks, real market data, multiple pricing models, and backtesting. The finished product is deployed to the public internet so it can be linked from a resume.

GitHub repository: https://github.com/Mustafan4x/Vega

Visual direction: the canonical visual ground truth for the project is `/home/mustafa/src/vega/docs/design/claude-design-output.html` (the "Oxblood" theme: dark surface, oxblood `#C03A3A` primary, sea green accent, IBM Plex Serif italic display, Newsreader for numbers, Manrope for UI text, JetBrains Mono for code). Open the file in a browser to see all five screens (Pricing, Heat Map, Model Comparison, Backtest, History) rendered live via inline React + Babel. Every design token is exposed as a CSS variable at `:root`, every visual region is labeled with `data-component`, and a JSON design manifest at the bottom of the file enumerates tokens, components, screens, and a Tailwind config sketch.

The `design/` folder at the project root holds the original user .webp mood board (historical reference). The `docs/design/` folder holds the canonical Claude Design HTML, wireframes, and tokens.

## Source material

This spec was written from a YouTube transcript describing the recommended pet project for a quant trader candidate, plus the user's preferences captured during the brainstorming phase. The full transcript is stored at `/home/mustafa/src/vega/docs/source/transcript.md` for any future Claude session that needs to reread it. The original video URL is https://www.youtube.com/watch?v=lY-NP4X455U.

## How this spec is meant to be used

Each section of work is owned by a specialized agent so a single agent can focus deeply on one domain. Quality improves when each role stays scoped. Every agent has a dedicated file in `agents/` that describes:

1. **Mission**: the one sentence purpose of the role.
2. **Inputs**: the deliverables this agent receives from upstream agents.
3. **Outputs**: the deliverables this agent produces for downstream agents.
4. **Tasks**: the ordered task checklist, grouped by phase.
5. **Plugin(s) to use**: which Claude Code plugins or skills the agent should invoke.
6. **Definition of done**: the acceptance criteria for the agent's work.
7. **Handoffs**: which agents this role hands work to next.

Read `agents/00-project-manager.md` first. The Project Manager owns sequencing, runs the brainstorming and planning phases, and dispatches every other agent.

## How to deploy these agents

The files in `agents/` are not just documentation. Each one is a self contained brief for a specialized agent that should be deployed and run on its own. The intent is that each agent runs in its own scoped context (its own Claude Code session or subagent invocation) so it stays focused and produces higher quality work than a single generalist trying to do everything.

> **Quick start for Claude Code**: read `CLAUDE.md` (auto loaded) and `GETTING-STARTED.md` for the literal first session walkthrough. The rest of this section is the explanation behind those instructions.

### Recommended deployment pattern

1. **Start a fresh Claude Code session in `/home/mustafa/src/vega`.** `CLAUDE.md` auto loads and tells the session it is the Project Manager. The PM reads `SPEC.md` and `agents/00-project-manager.md`, then invokes `superpowers:brainstorming` and `superpowers:writing-plans` to produce the per phase implementation plan in `docs/plan.md`.

2. **For each phase**, the Project Manager session dispatches the agents whose tasks are listed for that phase. Two ways to dispatch:

   * **Subagent (recommended for parallel, scoped work).** Use the `Task` tool with `subagent_type: "general-purpose"` and a prompt that says "You are the [Role] agent for the Vega project. Read `/home/mustafa/src/vega/SPEC.md` and `/home/mustafa/src/vega/agents/NN-role.md` and execute the Phase X tasks listed there. Use the plugins listed in the agent file." Subagents are best for agents whose work does not depend on a long running conversation (e.g., Code Reviewer, Security Engineer review pass, QA test writing, Performance Engineer profiling).

   * **Separate Claude Code session (recommended for agents that own a long lived stream of work).** Open a new terminal in `/home/mustafa/src/vega`, start `claude`, and have that session play one role for the duration of the phase. Best for the Backend Developer, Frontend Developer, and DevOps Engineer, where the agent benefits from accumulating context across many edits.

3. **Each agent uses the plugins listed in its file.** For example, the Frontend Developer invokes `frontend-design`, `vercel-react-best-practices`, and `superpowers:test-driven-development`. The Project Manager invokes `superpowers:brainstorming`, `superpowers:writing-plans`, and `superpowers:dispatching-parallel-agents`. The Security Engineer invokes `security-review`. Do not skip these; they are how the agent stays in role.

4. **Handoffs are explicit.** When an agent finishes its phase tasks, it commits its output, opens a PR, and writes a short handoff note in the PR description naming the next agent (per the "Handoffs" section of its agent file). The Project Manager session reviews the handoff and dispatches the next agent.

5. **Quality gates between phases.** Before a phase closes, the Project Manager confirms QA, Security, and Code Review have all signed off. A phase that has not been signed off does not advance.

### Example: starting Phase 0

In a Claude Code session in `/home/mustafa/src/vega`, the user (Mustafa) says:

> Read `SPEC.md` and `agents/00-project-manager.md`. You are the Project Manager. Run `superpowers:brainstorming` to confirm Phase 0 scope, then `superpowers:writing-plans` to produce `docs/plan.md`. Then dispatch the Phase 0 agents in parallel via the `Task` tool: UI/UX Designer, Security Engineer (threat model), DevOps Engineer (repo init), Documentation Engineer (initial README and architecture doc).

That single instruction is enough for the Project Manager session to take over and drive Phase 0 to completion.

### What to do if an agent goes off script

* If an agent's output does not match its agent file, point at the file and re prompt. Do not let scope creep slide.
* If an agent needs information another agent owns, route the question through the Project Manager rather than letting agents talk laterally; this keeps coordination centralized.
* If a phase reveals a missing decision, send it back to brainstorming with the Project Manager. Do not have any one agent make a project wide decision unilaterally.

## Tech stack decisions

| Layer | Choice | Rationale |
|---|---|---|
| Frontend framework | React with Vite and TypeScript | Demonstrates real frontend skill, more impressive than a Streamlit prototype on a resume. |
| Frontend styling | Tailwind CSS | Locked in for v1. Tokens come from the Claude Design HTML at `docs/design/claude-design-output.html` (Oxblood theme). May be revisited later. |
| Visual theme | Oxblood (dark) | Primary `#C03A3A`, accent `#34D399`, fonts Manrope (UI), IBM Plex Serif italic (display), Newsreader (numbers), JetBrains Mono (code). Source: `docs/design/claude-design-output.html`. |
| Frontend hosting | Cloudflare Pages (primary), Vercel (alternative) | See `docs/setup-guide.md` for the Vercel security tradeoff. |
| Backend framework | FastAPI on Python 3.12 | Async, typed, fast, idiomatic for quant Python. |
| Backend hosting | Render or Fly.io free tier | Vercel does not host long running Python services well. |
| Database | Postgres on Neon free tier (production), SQLite (local dev) | Postgres is free via Neon, SQLite gives zero setup local dev. |
| ORM / migrations | SQLAlchemy 2.x with Alembic | Industry standard for Python plus Postgres. |
| Python package manager | `uv` | Fast, modern, single tool replacing pip plus venv plus pip-tools. |
| Frontend package manager | `pnpm` | Fast and disk efficient. |
| Containerization | Docker plus docker-compose | Owned by the DevOps engineer. |
| CI/CD | GitHub Actions | Tests on every PR, deploy on tag. |
| Auth | None for v1 | A per user auth plan is tracked privately for a future release. |
| Market data | `yfinance` | Free, no API key required. |
| Charts | Raw Canvas + SVG (current Oxblood reference uses these) or Recharts/Plotly | The Oxblood HTML implements heat maps as `<canvas>` and line charts inline with SVG, no third party library. Frontend Developer may keep that pattern or adopt Recharts/Plotly if they materially improve maintainability. Decide in Phase 4. |

## Phased build

Each phase is a shippable milestone. Earlier phases must be production ready before the next phase begins. A phase is "done" when QA, Security, Code Review, and the Project Manager all sign off.

### Per phase usage budgets

The user is on the Claude Max 5x plan. Each phase below is **sized to fill roughly 90 to 99 percent of a single Max 5x usage window**. The "Window cost" estimate next to each phase is a rough budget; treat it as a planning aid, not a hard cap. After every phase, the PM session is required to stop and run the check-in protocol described in `CLAUDE.md` ("Pacing rule"). Do not advance to the next phase without explicit user confirmation.

When a phase comes in well under budget, the PM may bundle the next short phase into the same window if the user agrees during the check-in.

### Phase 0: Foundations
**Window cost: ~95 percent of one Max 5x window.** Heavy planning, parallel agent dispatches, repo init, frontend and backend scaffolds, threat model, wireframes, README, and architecture doc all happen here.

Project Manager runs brainstorming and writes the implementation plan in `docs/plan.md`. UI/UX Designer reads the canonical Claude Design HTML at `docs/design/claude-design-output.html` (the Oxblood theme, already approved by the user), extracts tokens to `docs/design/tokens.md` and a draft `frontend/tailwind.config.ts` extension, and writes screen layout descriptions to `docs/design/wireframes.md`. Security Engineer publishes the threat model and baseline. DevOps Engineer wires the local working directory `/home/mustafa/src/vega/` into the existing GitHub repo `Mustafan4x/Vega` (run `git init` locally, add the GitHub repo as `origin`, push the existing files as the first commit), then scaffolds the `uv` project under `backend/` and the `pnpm` plus Vite plus React plus TypeScript plus Tailwind project under `frontend/`, dropping the Tailwind config sketch from the Oxblood HTML's design manifest into `frontend/tailwind.config.ts`. Documentation Engineer writes the initial README and architecture overview.

**End of phase**: PM runs the mandatory check-in protocol from `CLAUDE.md`.

### Phase 1: Python REPL Black Scholes
**Window cost: small alone (~30 percent). PM should bundle Phase 1 plus Phase 2 into a single window unless the user objects at check-in.**

Quant Domain Validator and Backend Developer co-own a pure Python module that computes Black Scholes call and put values from the five inputs (current asset price, strike, time to expiry, risk free interest rate, volatility). A small REPL or `__main__` script accepts the five inputs and prints both prices. Risk and Financial Correctness Reviewer checks the formula and edge cases (T equals zero, sigma equals zero, deep in or out of the money).

**End of phase**: if not bundled with Phase 2, run the check-in protocol.

### Phase 2: FastAPI backend
**Window cost: ~60 percent alone, or ~90 to 95 percent when bundled with Phase 1.**

Backend Developer wraps the calculator in a FastAPI service. A single endpoint accepts the five inputs and returns call and put values. Pydantic models validate input. Security Engineer reviews the input validation, CORS policy, rate limiting, and error responses. Observability Engineer adds structured logging and request tracing. QA Engineer writes contract tests against the endpoint.

**End of phase**: run the check-in protocol.

### Phase 3: React frontend MVP
**Window cost: ~95 percent of one window.** This is the heaviest UI phase because the design system, the API client, and the first visible screens all land here.

Frontend Developer builds the React plus Vite app with a form for the five inputs and a result panel showing call and put. UI/UX Designer reviews against the wireframes. Accessibility Specialist runs an a11y audit (keyboard nav, screen reader labels, color contrast). Security Engineer reviews CSP, secrets handling, and the frontend to backend calls.

**End of phase**: run the check-in protocol.

### Phase 4: Heat map visualization
**Window cost: ~90 percent of one window.** Heat map component, vectorized backend endpoint, perf profiling, and tests fit here.

Frontend Developer adds a heat map component. The two axes are volatility shock and stock price shock; cells show call values (and a second heat map shows put values). Cells are colored on a green to red scale by magnitude. Performance Engineer profiles heat map generation; if needed, the Backend Developer vectorizes the computation server side.

**End of phase**: run the check-in protocol.

### Phase 5: P&L heat map
**Window cost: small alone (~40 percent). PM should bundle Phase 5 plus Phase 6 into a single window unless the user objects at check-in.**

Frontend exposes two new fields: purchase price for the call, purchase price for the put. The heat map switches mode to display P&L instead of value, with green for positive P&L and red for negative P&L. Risk Reviewer validates the P&L sign and magnitude under stress cases.

**End of phase**: if not bundled with Phase 6, run the check-in protocol.

### Phase 6: Persistence
**Window cost: ~60 percent alone, or ~90 to 95 percent when bundled with Phase 5.**

Data Engineer designs the schema (inputs table, outputs table, calculation_id linking them). Database Administrator writes the Alembic migrations and indexes. Backend Developer wires the persistence layer so every Calculate click writes one row to the inputs table and N rows to the outputs table (one per heat map cell). Security Engineer reviews SQL injection surface, parameterized queries, secrets in DSNs, and least privilege for the DB user.

**End of phase**: run the check-in protocol.

### Phase 7: The Greeks
**Window cost: small alone (~40 percent). PM should bundle Phase 7 plus Phase 8 into a single window unless the user objects at check-in.**

Quant Validator and Pricing Models Engineer add closed form Greeks (delta, gamma, theta, vega, rho) to the Black Scholes module. Backend exposes them. Frontend displays them next to the call and put values. QA writes property based tests (e.g., put call parity, delta bounds).

**End of phase**: if not bundled with Phase 8, run the check-in protocol.

### Phase 8: Real market data
**Window cost: ~55 percent alone, or ~90 to 95 percent when bundled with Phase 7.**

Backend Developer adds a service that calls `yfinance` to look up the current price for a ticker symbol. Frontend adds ticker autocomplete; selecting a ticker auto fills the asset price field. Security Engineer reviews the third party request path (timeouts, response size limits, retry policy).

**End of phase**: run the check-in protocol.

### Phase 9: Multiple pricing models
**Window cost: ~95 percent of one window.** Two new pricing models, convergence tests, model selector UI, and side by side comparison view.

Pricing Models Engineer implements the binomial tree model and a simple Monte Carlo pricer. Frontend adds a model selector. The UI shows the three prices side by side so the user can compare. Risk Reviewer checks that the three models converge on identical inputs.

**End of phase**: run the check-in protocol.

### Phase 10: Backtesting
**Window cost: ~95 to 99 percent of one window.** This is the largest single phase: backtesting engine, strategy library, historical price ETL, P&L chart, and tests. The PM should NOT bundle anything else with this phase.

Pricing Models Engineer plus Backend Developer add a backtesting endpoint: given a strategy (e.g., long call, covered call, straddle) and a date range, replay historical prices and produce a P&L curve. Frontend renders the curve. Performance Engineer reviews the time and memory cost.

**End of phase**: run the check-in protocol.

### Phase 11: Production deployment
**Window cost: ~90 percent of one window.** Deployment requires the user to log in and click through three dashboards (Cloudflare, Render, Neon), so expect back and forth with the user during this phase. Reserve a fresh window for it.

DevOps Engineer deploys frontend to Cloudflare Pages, backend to Render, and DB on Neon. Sets up the custom subdomain if the user wants one. Security Engineer runs the final hardening checklist (HTTPS, HSTS, CSP, secret rotation, dependency scan). Documentation Engineer finalizes and verifies the user facing setup guide at `docs/setup-guide.md` (the file already exists as a scaffold from Phase 0).

**End of phase**: run the check-in protocol; the project is now shipped, so the check-in is also a celebration. Offer the user a `/schedule` agent to revisit the deployed app in a few weeks for any rot or follow ups.

## Agent roster

Each link points to a file in `agents/`.

| # | Agent | One line mission |
|---|---|---|
| 00 | [Project Manager](agents/00-project-manager.md) | Owns the plan, sequences phases, runs brainstorming, dispatches every other agent. |
| 01 | [Quant Domain Validator](agents/01-quant-domain-validator.md) | Verifies the Black Scholes math and edge cases. |
| 02 | [Pricing Models Engineer](agents/02-pricing-models-engineer.md) | Implements binomial, Monte Carlo, and backtesting models. |
| 03 | [Backend Developer](agents/03-backend-developer.md) | Builds the FastAPI service and persistence layer. |
| 04 | [Frontend Developer](agents/04-frontend-developer.md) | Builds the React app, heat maps, and charts. |
| 05 | [UI/UX Designer](agents/05-ui-ux-designer.md) | Wireframes, visual direction, interaction design. |
| 06 | [Data Engineer](agents/06-data-engineer.md) | Schema design, ETL of market data. |
| 07 | [Database Administrator](agents/07-database-administrator.md) | Migrations, indexes, query performance. |
| 08 | [Security Engineer](agents/08-security-engineer.md) | Threat model, hardening, secret management, dependency scanning. |
| 09 | [DevOps Engineer](agents/09-devops-engineer.md) | Docker, CI/CD, deployment, infrastructure. |
| 10 | [QA Engineer](agents/10-qa-engineer.md) | Test plan, automated tests, regression suite. |
| 11 | [Code Reviewer](agents/11-code-reviewer.md) | Reviews every PR for code quality and idiom. |
| 12 | [Performance Engineer](agents/12-performance-engineer.md) | Profiles heat map and pricing hot paths. |
| 13 | [Accessibility Specialist](agents/13-accessibility-specialist.md) | a11y audit, WCAG compliance, keyboard and screen reader testing. |
| 14 | [Observability Engineer](agents/14-observability-engineer.md) | Logging, metrics, error tracking. |
| 15 | [Documentation Engineer](agents/15-documentation-engineer.md) | README, setup guide, architecture docs, ADRs. |
| 16 | [Risk and Financial Correctness Reviewer](agents/16-risk-correctness-reviewer.md) | Validates finance assumptions and P&L sign correctness. |

## Coordination rules

1. The Project Manager runs the brainstorming and planning skills before any code is written.
2. No phase begins until the prior phase has Security, QA, and Code Review sign off.
3. Every code change goes through the Code Reviewer before merge.
4. Security Engineer has veto power on any change that touches authn, secrets, third party calls, or user input.
5. Risk Reviewer has veto power on any change that touches the pricing math or P&L calculation.
6. Documentation Engineer updates `docs/` whenever a phase completes.
7. Future ideas (anything out of scope for v1) are written to the maintainer's private notes outside this repo (gitignored at the repo root) and not implemented in v1.
8. **Mandatory check-in after every phase.** The PM session must stop, summarize what shipped, ask the user for current Max plan usage and reset window, and wait for explicit confirmation before starting the next phase. See `CLAUDE.md` "Pacing rule" for the exact protocol. This rule is not optional, even in auto mode.
