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

## Logo, favicon, and tab title

**Idea**: replace the leftover purple lightning bolt favicon with a custom Oxblood mark, design a proper Vega wordmark for any future marketing surface, and shorten the browser tab title from `Vega · Black Scholes Options Pricer` to just `Vega`.

**Why deferred**: the current favicon at `frontend/public/favicon.svg` is a purple `#863bff` lightning bolt SVG carried over from a frontend template. It loads, it works, and the in app sidebar mark in `LayoutShell.tsx` is already a simple plus shape on `currentColor` that picks up the Oxblood palette correctly, so the visual identity is functionally fine. The longer tab title is descriptive but reads cluttered when the user has many tabs open; a single word reads cleaner. None of this blocks a working build, so the polish is intentionally postponed.

**When to revisit**: any time after Phase 11 ships, especially before sharing the deployed link on a resume, in a blog post, or anywhere a screenshot of the browser tab is visible. The favicon is the first thing a visitor's tab shows, so this is high impact for low effort.

**Notes for the implementer**:

* **Tab title**: edit `frontend/index.html` line 8, change `<title>Vega · Black Scholes Options Pricer</title>` to `<title>Vega</title>`. One line change, no test updates required beyond a single Vitest assertion that `document.title === 'Vega'` to lock the regression.
* **Favicon**: replace `frontend/public/favicon.svg` with a custom SVG that uses the Oxblood palette (oxblood `#C03A3A` primary, sea green `#34D399` accent, both already defined in `docs/design/tokens.md`). Keep the file under 4 KB and verify it renders crisply at 16 px and 32 px (browser tab favicon sizes). Spot check in both light and dark browser themes since the tab background changes by OS.
* **In app sidebar mark**: the inline SVG in `frontend/src/components/LayoutShell.tsx` lines 27 to 31 is a simple plus shape using `currentColor` and already matches the Oxblood theme. Decide whether to keep it as is or harmonize it with the new favicon; both choices are defensible. Whichever way, the `data-element="brandMark"` selector must keep working since `web-design-guidelines` audits depend on it.
* **Wordmark**: out of scope for the favicon swap; this is a separate UI/UX Designer pass if desired. IBM Plex Serif italic from `docs/design/tokens.md` is the display face. The wordmark would render in the sidebar next to `<span data-element="brandName">Vega</span>` and on any future landing page.
* **Ownership**: favicon and wordmark belong to the UI/UX Designer agent (`agents/05-ui-ux-designer.md`); the title and any DOM wiring belong to the Frontend Developer agent (`agents/04-frontend-developer.md`).

## Security hardening research pass

**Idea**: schedule a dedicated security research and hardening sweep on top of the baseline already shipped. The Phase 0 threat model and the Phase 11 hardening checklist (HSTS, CSP, per route rate limits, fail loud config, `pip-audit` and `pnpm audit` clean, non root container, parameterized queries, no secrets in logs) cover the obvious surface. The goal of this pass is to go beyond the obvious: research current attack patterns, look for non obvious vulnerabilities, edge cases, and defense in depth gaps, then close them so the deployed app is as hard as possible to abuse.

**Why deferred**: v1 is scoped to ship and look good on a resume. A deep security pass takes focused time, requires fresh reading on current threats and tools, and is best done once the production surface is stable rather than mid build.

**When to revisit**: after the live demo has been up for a few weeks and real traffic has been observed in the Cloudflare and Render logs. Worth running before the project is publicly linked from a high traffic context (resume, blog post, social).

**Notes for the implementer**: this work belongs to the Security Engineer agent (`agents/08-security-engineer.md`); the Performance Engineer pairs in for any rate limit retuning. Starter checklist, in order of expected payoff:

* Re run STRIDE on every endpoint (`/api/price`, `/api/heatmap`, `/api/calculations`, `/api/tickers`, `/api/backtest`) with abuse cases, not just happy path. Update `docs/security/threat-model.md`.
* Audit `_headers` and CSP on Cloudflare Pages against current OWASP recommendations; tighten `connect-src`, add `Permissions-Policy`, and consider `Cross-Origin-Opener-Policy` plus `Cross-Origin-Embedder-Policy`.
* Run extra dependency scanners beyond `pip-audit` and `pnpm audit`: `osv-scanner`, `trivy` on the container image, and a focused look at `yfinance` since it is a thin wrapper over Yahoo's undocumented endpoints.
* Fuzz endpoints for unhandled input (NaN, Infinity, oversized arrays, malformed dates, ticker injection, unicode tricks).
* Stress test the per route rate limits under realistic abuse patterns (slow drip, distributed clients, expensive heatmap and backtest payloads); tune limits based on observed traffic.
* Verify least privilege for the `vega_app` Postgres role on Neon, and document a rotation procedure for `VEGA_DATABASE_URL` plus the Render and Cloudflare Pages env secrets in `docs/security/`.
* Add a `SECURITY.md` at the repo root with a vulnerability disclosure contact, then run one external scanner pass (OWASP ZAP, Mozilla Observatory, Hardenize) against the live URL and capture the report in `docs/security/`.

The goal is not paranoia. The goal is that anyone who pokes at the live demo, including the user during interview prep, can confidently say the deployment is buttoned up.

## Other deferred ideas

(Add more here as they come up. Each entry should follow the same format: idea, why deferred, when to revisit, notes.)
