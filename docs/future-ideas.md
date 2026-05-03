# Future ideas

A scratch list of features that are out of scope for v1 but worth picking up later. The Project Manager reviews this list when planning the next major release.

## Authentication and per user history

**Idea**: each user signs in (Google OAuth, GitHub OAuth, or magic link email) and gets a private history of their calculations. Other users cannot see their inputs, outputs, or P&L.

**Why deferred**: adds backend depth (sessions, JWT, OAuth callbacks), data model changes (`user_id` foreign keys on every persisted row), and threat model expansion (account takeover, IDOR, password reset). Not required to demonstrate the core skills the project is meant to show.

**When to revisit**: after Phase 11 is shipped and stable, or earlier if the project grows beyond a single user demo.

**Notes for the implementer**: prefer a hosted OAuth provider (Auth0, Clerk, Supabase Auth) over rolling your own. The Security Engineer will need to update the threat model. The Data Engineer will need to migrate existing rows or treat them as anonymous.

## Dividends in the pricing model

**Idea**: extend the Black Scholes module to support a continuous dividend yield `q` (and, for completeness, the binomial and Monte Carlo pricers added in Phase 9). The standard generalization replaces `S` with `S * exp(-q * T)` in the d1 and d2 formulas, so the change is local to one module.

**Why deferred**: v1 is scoped to European options on a non dividend paying stock to keep the math doc, the test reference values (Hull, Wilmott, Natenberg), and the Pydantic input model small and exact. Adding `q` doubles the test surface (every reference case needs a `q != 0` variant) and complicates the UI form (a new percent input next to the rate field).

**When to revisit**: after Phase 11 ships and the project is being used. Or sooner if the user adds a real ticker and notices the price disagrees with the market because the underlying actually pays dividends.

**Notes for the implementer**: the convention is documented in `docs/risk/conventions.md` (dividends assumed zero in v1). The Quant Domain Validator owns the formula change and the new reference values. Risk Reviewer must update sanity cases. Backend Developer adds an optional `q: float = 0.0` parameter to the function signature so existing callers keep working. Frontend Developer adds the input field and the percent to decimal conversion. Default to `q = 0` everywhere so the v1 behavior is preserved.

## Project name and logo

**Idea**: replace the working title "Trader" with a real product name and a small wordmark or logo. The current name is a generic placeholder; a real name plus a logo will look better on the resume link, in the deployed site's `<title>`, and as the favicon.

**Why deferred**: naming and brand work is creative and personal; it does not block the engineering build, and the wrong name now would just have to be ripped out later. The Oxblood visual identity is locked in (per ADR 0004), so a logo can be designed against that palette whenever the user is ready.

**When to revisit**: any time before Phase 11 (production deployment), so the deployed site, the GitHub repo description, and the resume link all use the same name. Easiest moment is right before Phase 11 opens.

**Notes for the implementer**: places the name appears today as "Trader" or "trader": the GitHub repo name (`Mustafan4x/Trader`), `README.md`, `SPEC.md`, `STATUS.md`, `docs/architecture.md`, the four ADRs, `frontend/index.html` `<title>`, `frontend/src/App.tsx` placeholder text, `backend/pyproject.toml` (`name = "trader-backend"`), `backend/app/repl.py` startup banner, and the local working directory `/home/mustafa/src/trader/`. Renaming is a find and replace pass plus a `gh repo rename` (which preserves the old URL as a redirect). The local directory rename is optional. Logo work belongs to a UI/UX Designer pass; the Oxblood palette and IBM Plex Serif italic display from `docs/design/tokens.md` are the constraints. Favicon at `frontend/public/favicon.svg` is currently the Vite default.

## Other deferred ideas

(Add more here as they come up. Each entry should follow the same format: idea, why deferred, when to revisit, notes.)
