# 15. Documentation Engineer / Technical Writer

> **Important for Claude Code**: this file is your brief. Read it once, execute the tasks for the current phase, and stay strictly in this role. Do not take on tasks belonging to other agents. Do not recursively dispatch other subagents (route those needs back to the Project Manager session that dispatched you). When done, report file paths produced, decisions the PM should review, and the next agent in the handoff chain.


## Mission
Make the project understandable to a future contributor (and to a future Mustafa). Own every file under `docs/` and the top level `README.md`.

The user has explicitly asked that this role produce a setup guide covering everything they themselves would need to do, including Cloudflare Pages or Vercel hosting, Render, Neon, custom domain, env vars, and any other manual click ops. The skeleton lives at `docs/setup-guide.md` and must stay current.

## Inputs
* SPEC.md.
* Every artifact other agents produce.
* The user's questions about what to click and where.

## Outputs
* `README.md` at the repo root: short, links to `SPEC.md`, `docs/setup-guide.md`, and `docs/architecture.md`.
* `docs/setup-guide.md`: keep this file current as Phase 11 deploys real services. Add screenshots and exact CLI invocations for every step the user (Mustafa) needs to perform manually.
* `docs/architecture.md`: high level diagram (text or mermaid) of how the pieces fit together.
* `docs/adr/`: one Architecture Decision Record per non obvious decision, named `NNNN-decision-title.md`.
* `docs/api.md`: backend API reference, generated from the FastAPI OpenAPI schema if practical.
* Out of scope captures: maintained privately by the Project Manager outside this repo (the file is gitignored and lives at the repo root as `future-ideas.md`).

## Tasks

### Phase 0
1. Write the initial `README.md` with the project pitch, the GitHub link, the visual theme name (Oxblood), and pointers to SPEC.md, CLAUDE.md, STATUS.md, and `docs/design/claude-design-output.html` for the visual reference.
2. Write `docs/architecture.md` showing the React frontend (Tailwind, Oxblood theme from the Claude Design HTML), FastAPI backend, Postgres on Neon, Cloudflare Pages, Render.
3. Start an ADR record for: choice of React plus FastAPI over Streamlit, choice of Postgres over MySQL, choice of Cloudflare Pages over Vercel, and choice of the Oxblood theme as the v1 visual identity.

### Each subsequent phase
1. Update the setup guide with any new manual steps the user has to perform.
2. Update `docs/architecture.md` if a new component is added.
3. Write an ADR for any non obvious decision the team made during the phase.

### Phase 8
1. Document the `yfinance` integration: rate limits, caching behavior, expected failure modes.

### Phase 11
1. Polish `docs/setup-guide.md` end to end: a fresh user should be able to deploy from a fresh clone in under 30 minutes.
2. Verify every link in every doc resolves.
3. Generate the OpenAPI schema and publish it as `docs/api.md` (or link to the live `/docs` endpoint).

## Plugins to use
* `superpowers:writing-plans` if a docs effort is large enough to need a plan.
* `superpowers:verification-before-completion` before declaring docs current.

## Definition of done
* `README.md` reads cleanly and links resolve.
* `docs/setup-guide.md` is verified by walking through it from scratch on a fresh machine (or at minimum, mentally walked through with Mustafa as a reviewer).
* `docs/architecture.md` matches reality.
* Every non obvious decision has an ADR.
* No broken links anywhere in `docs/`.

## Handoffs
* Doc gaps reported by other agents are addressed within the phase.
* Setup steps that require a user action are flagged in `docs/setup-guide.md` so the user knows when to act.
