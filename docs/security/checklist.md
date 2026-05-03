# Per phase security hardening checklist

Owner: Security Engineer agent.
Last updated: 2026-05-02 (Phase 0).

This checklist is the gate the Security Engineer applies at every phase boundary. A phase does not close without every box ticked or an explicit accepted residual risk noted in `docs/security/threat-model.md`. The Project Manager must see the Security Engineer's sign off before opening the next phase.

The check items are written as imperatives. Each item lives under one phase even when the underlying control is reaffirmed every subsequent phase; later phases pick up the cumulative state from earlier phases.

## Phase 0: Foundations

Repo level controls; nothing is deployed yet.

* [ ] Branch protection on `main` configured: PR review required, CI green required, signed commits required, linear history required, force push blocked. (User click op; see `threat-model.md` "Phase 0 user actions".)
* [ ] Dependabot alerts, security updates, and version updates enabled at the GitHub repo level. (User click op.)
* [ ] `.github/dependabot.yml` committed with entries for `pip` (the `backend/` ecosystem) and `pnpm` (the `frontend/` ecosystem) plus `github-actions`. (DevOps Engineer.)
* [ ] CodeQL enabled for both Python and JavaScript/TypeScript. (User click op.)
* [ ] Secret scanning enabled with push protection. (User click op.)
* [ ] `gitleaks` configured as a CI check on every PR. Workflow file under `.github/workflows/`. (DevOps Engineer.)
* [ ] `bandit` configured as a CI check on every PR for any Python under `backend/`. (DevOps Engineer.)
* [ ] `semgrep` configured as a CI check with at minimum `p/owasp-top-ten`, `p/python`, `p/react`, `p/sqlalchemy`. (DevOps Engineer.)
* [ ] `.gitignore` blocks `.env`, `.env.*`, `*.pem`, `*.key`, `*.pfx`, `id_rsa*`, and any other private credential file pattern. (DevOps Engineer.)
* [ ] `pre-commit` config installed locally with `gitleaks` and `ruff` (for Python) and `eslint` (for TS once Phase 0 scaffolds the frontend). (DevOps Engineer.)
* [ ] Threat model published at `docs/security/threat-model.md`.
* [ ] Secrets table published at `docs/security/secrets.md`.
* [ ] User has 2FA enabled on GitHub. (User self check.)
* [ ] No real secrets are in any committed file. Verified by running `gitleaks` against the working tree.

## Phase 1: Python REPL Black Scholes

Pure module; no network surface.

* [ ] All numeric inputs to the Black Scholes module are typed and validated (no implicit coercion of strings or arbitrary objects).
* [ ] No use of `eval`, `exec`, or any binary deserialization in the module.
* [ ] No file system reads or writes from the pricing module (it is a pure function).
* [ ] `bandit` clean on the module.
* [ ] Test inputs that trigger numeric edge cases (T equals 0, sigma equals 0, deep ITM, deep OTM) are part of the test suite (Quant Validator owned, Security Engineer reviews to ensure they do not crash or leak via stack traces).

## Phase 2: FastAPI backend

The first network surface. This is the largest single security review of the build.

* [ ] Pydantic models defined for every endpoint request and response. No model uses `extra = "allow"`. (Backend Developer.)
* [ ] Input bounds set: numeric ranges sane (e.g., volatility in (0, 5), time to expiry in (0, 50), price > 0). Reject out of range with HTTP 422.
* [ ] Maximum request body size enforced (32 KB).
* [ ] CORS allow list set to the exact deployed frontend origin once known. For local dev, allow `http://localhost:5173` only. Wildcards are banned. `allow_credentials=False`.
* [ ] Rate limiting active via `slowapi` or equivalent. Suggested defaults documented in `threat-model.md` T12. PM confirms the values.
* [ ] HTTP security headers added on every response: `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: frame-ancestors 'none'`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()`, `Cross-Origin-Opener-Policy: same-origin`, `Cross-Origin-Resource-Policy: same-site`.
* [ ] Custom exception handler in place: 4xx returns a non leaking JSON body; 5xx logs the stack trace server side and returns a generic body.
* [ ] Structured JSON logging includes request ID, route, status code, latency. Does not include request body or any user input that could carry credentials.
* [ ] No DSN in any log line. Verified with a unit test that exercises a connection failure path and asserts on the log content.
* [ ] `/health` endpoint returns 200 with no leaked info (no version, no uptime that could fingerprint the host beyond what the platform already exposes).
* [ ] OpenAPI docs at `/docs` and `/redoc` either disabled in production or behind a flag the Security Engineer reviews.
* [ ] `bandit` clean. `semgrep` clean. `pip-audit` clean.
* [ ] Contract tests in QA's suite verify the rate limit returns 429 once exceeded.

## Phase 3: React frontend MVP

First user facing surface.

* [ ] CSP header set on the Cloudflare Pages site: `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://<backend host>; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests`.
* [ ] No inline `<script>` tags in the built HTML. Verified by grepping the build output.
* [ ] No use of `eval` in any frontend dependency. Verified by `pnpm why` or a simple grep on the bundle.
* [ ] No use of the React raw HTML injection prop anywhere in the codebase. Enforced by an ESLint rule (`react/no-danger`).
* [ ] No secrets in `VITE_*` vars. Only public config (`VITE_API_BASE_URL`).
* [ ] All API calls go through a single `apiClient` module that pins the backend origin from `VITE_API_BASE_URL` and rejects responses with unexpected content types.
* [ ] Errors from the backend are rendered through React's escaping path. No raw HTML rendering of error messages.
* [ ] `pnpm audit --audit-level=high` clean.
* [ ] CSP policy verified live with `securityheaders.com` or equivalent (Phase 11 redoes this on the production URL).
* [ ] Frontend does not store anything in `localStorage` or `sessionStorage` other than a UI preference (theme, last selected ticker). Documented.

## Phase 4: Heat map visualization

Mostly an extension of Phase 3 plus a vectorized backend endpoint.

* [ ] Heat map endpoint enforces grid bounds: rows and columns capped at 21 each. Larger requests are rejected with HTTP 422.
* [ ] Heat map endpoint payload size capped on the response side too: a 21 by 21 grid of doubles is well under 32 KB; document and assert the upper bound.
* [ ] No new third party charting library introduced without Security Engineer review (Canvas / SVG inline is fine; Recharts and Plotly are also fine but require a dependency review).
* [ ] If a charting library is added: `pnpm audit` clean, the library has been published for at least 6 months with no public CVEs.

## Phase 5: P&L heat map

No new surface; reuses Phase 4 endpoint with extra fields.

* [ ] Purchase price fields validated server side (non negative, finite, within an order of magnitude of the asset price).
* [ ] No change to the sign convention of P&L without Risk Reviewer plus Security Engineer joint sign off (a sign flip is a correctness issue, but a publicly visible one would be a reputational hit, which is in the security threat model).

## Phase 6: Persistence

The first stateful phase. Database security takes over.

* [ ] Every query goes through SQLAlchemy ORM or a parameterized `text()` call. No string formatted SQL. Verified by `bandit` `B608` and a manual code search.
* [ ] Production DB user has only the privileges it needs: `SELECT`, `INSERT` on the inputs and outputs tables; no `DDL`, no `DROP`, no `SUPERUSER`. Migrations run as a separate higher privilege role at deploy time.
* [ ] Migrations are reversible. Alembic `downgrade` works on the staging DB.
* [ ] `DATABASE_URL` lives only in Render env vars and the local `.env`. `gitleaks` would catch a committed DSN; verified by adding a synthetic DSN to a branch and confirming `gitleaks` flags it (then deleting the branch).
* [ ] Neon connection encrypts at rest and in transit (default; documented in `secrets.md`).
* [ ] No PII column added without Security Engineer review. The schema currently has no PII columns.
* [ ] Indexes designed by the DBA do not leak data through their names (e.g., no `idx_user_email`).
* [ ] Persistence write endpoint has its own rate limit (suggest 30 per minute per IP) on top of the global limit, since each call writes up to 441 rows.
* [ ] History read endpoint paginates. Maximum page size 100. No "fetch all" path.
* [ ] No raw exception messages from the DB driver leak to the client (e.g., a unique constraint violation returns a generic 4xx).

## Phase 7: The Greeks

Pure math extension; no new surface.

* [ ] Greeks endpoint inputs reuse the pricing endpoint's Pydantic model (DRY plus consistent validation).
* [ ] No new external dependency introduced (closed form Greeks are pure Python).
* [ ] Property based tests do not call any external service.

## Phase 8: Real market data (yfinance, the SSRF surface)

The first egress point. This is the second largest security review of the build.

* [ ] Ticker symbol input validated against `^[A-Z0-9.-]{1,10}$`. Reject anything else with HTTP 422.
* [ ] Outbound HTTP timeout: 5 seconds. Verified by a test that intercepts the underlying HTTP client and asserts the timeout.
* [ ] Maximum response size: 1 MB. Larger responses dropped before parsing.
* [ ] Outbound DNS resolution refuses RFC 1918, link local, loopback, and the cloud metadata IP `169.254.169.254`. Implemented either by wrapping the HTTP client or by a network policy in the runtime environment.
* [ ] Cache layer in front of `yfinance` calls (in process LRU is fine for v1). Cache key is the validated ticker symbol; cache TTL is at least 60 seconds for quotes.
* [ ] `yfinance` is pinned to a specific version in `uv.lock`. Updates go through Dependabot review.
* [ ] Response shape from the cache is validated through a Pydantic model before reaching the API client. Unknown fields are dropped.
* [ ] If `yfinance` raises, the error is logged server side and the client receives a generic 502 plus a hint to retry; no upstream stack trace leaks.
* [ ] If the upstream returns a non finite or negative price, the backend rejects it with a 502 and logs a metric (Risk Reviewer's domain too).
* [ ] Ticker autocomplete does not perform a fan out to many endpoints; it queries one upstream per keystroke at most, debounced 300 ms client side.

## Phase 9: Multiple pricing models

Pure math; same risk profile as Phase 7.

* [ ] Monte Carlo seed is sourced from `secrets.token_bytes` or `random.SystemRandom`, not `random.seed(int(time.time()))`, so the result is not predictable. (More defense in depth than a real attack vector for pricing, but the principle is cheap to keep.)
* [ ] Binomial tree depth bounded server side (e.g., max 1000 steps). Reject larger requests with HTTP 422.
* [ ] Monte Carlo iteration count bounded server side (e.g., max 100 000). Reject larger requests with HTTP 422.

## Phase 10: Backtesting

The largest single endpoint by compute cost.

* [ ] Backtest date range capped at 5 years.
* [ ] Backtest endpoint behind its own stricter rate limit (suggest 2 per minute per IP, 5 burst).
* [ ] Strategy library is a closed enum. The endpoint never executes user supplied code.
* [ ] Historical price ETL fetches over the same hardened HTTP client used in Phase 8.
* [ ] Backtest results are not persisted with any user identifier (none exists), but a request ID is logged so a user could ask "why did my backtest 503" and the operator can find the log.
* [ ] CPU and memory ceiling per request set at the framework level (e.g., a timeout middleware that aborts at 30 seconds wall clock).

## Phase 11: Production deployment

Final hardening pass.

* [ ] HTTPS enforced on both frontend and backend. Verified with `curl -I` against both URLs.
* [ ] HSTS header includes `preload` and the user has decided whether to submit to https://hstspreload.org/.
* [ ] CSP, `Permissions-Policy`, COOP, CORP all verified live via https://securityheaders.com/. Target grade A or higher.
* [ ] CORS allow list updated to the production frontend origin. Local dev origins removed from the production config.
* [ ] All secrets rotated from any default values used during development. New `DATABASE_URL` after first production deploy.
* [ ] `pip-audit` and `pnpm audit` re run against the production lock files. Zero high or critical findings.
* [ ] CodeQL re run on the latest commit. Zero high or critical findings.
* [ ] No backend endpoint returns a stack trace under any path. Verified by a 5xx test that triggers a forced exception.
* [ ] Render and Cloudflare Pages dashboards have 2FA enabled on the user's accounts. (User self check.)
* [ ] Neon dashboard has 2FA enabled. (User self check.)
* [ ] OpenAPI docs (`/docs`, `/redoc`) either disabled or password protected in production.
* [ ] `robots.txt` permits indexing only of intended public paths. The production URL is appropriate to be indexed; the API host is `Disallow: /`.
* [ ] A documented runbook for "what to do if the DSN leaks" exists at `docs/security/secrets.md`. Tested by Mustafa in a tabletop walkthrough.
* [ ] Final threat model update: every "Phase X" reference is reviewed and updated to past tense where the control is now in place; any newly accepted residual risks are added.
