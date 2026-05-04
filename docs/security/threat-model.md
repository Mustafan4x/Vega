# Threat model: Vega (Black Scholes options pricer)

Owner: Security Engineer agent.
Last updated: 2026-05-02 (Phase 0).
Scope: every layer this project will ship across the 11 phases described in `SPEC.md`. This document is the canonical security view of the system. It is reviewed and updated at every phase boundary, and at every PR that touches authn, secrets, third party services, or user input.

## How to read this document

The threat model follows STRIDE plus a slice of OWASP Top 10. For each asset, threats are listed with the controls that mitigate them and the residual risks the project explicitly accepts. "Accepted residual risk" means the risk is real, the project has chosen not to fully mitigate it in v1, and the rationale is documented here so a future reviewer does not need to rediscover it.

Conventions used below:

* **Asset**: something worth protecting.
* **Threat**: a way the asset could be harmed.
* **Control**: the engineering or process measure that mitigates the threat.
* **Residual risk**: what is left after the control is applied.
* **Owner**: the agent role responsible for keeping the control healthy.

## System overview

The deployed v1 system has three runtime tiers:

1. **Frontend**: a static React plus Vite plus Tailwind bundle hosted on Cloudflare Pages. No server side rendering. Talks only to the project's own backend over HTTPS.
2. **Backend**: a FastAPI service hosted on Render. Pure JSON over HTTPS. Endpoints: pricing (Phase 2), heat map (Phase 4), persistence write and history read (Phase 6), Greeks (Phase 7), market data lookup (Phase 8), backtest (Phase 10), `/health`.
3. **Database**: managed Postgres on Neon (production), SQLite (local dev). Accessed only by the backend over a TLS connection string.

The system has **no end user authentication in v1** (see "Accepted residual risks" below). The only third party data source is `yfinance` (Phase 8 onward). Optional: Sentry for error tracking (Observability Engineer's call).

## Trust boundaries

| Boundary | From | To | Trust direction |
|---|---|---|---|
| TLS (frontend) | Public internet | Cloudflare edge | Untrusted to semi trusted |
| TLS (backend) | Public internet (or Cloudflare) | Render web service | Untrusted to trusted |
| DB connection | Render backend | Neon Postgres | Trusted to trusted (mTLS over public internet) |
| Third party API | Render backend | Yahoo finance via `yfinance` | Trusted to untrusted |
| Build pipeline | GitHub Actions runner | npm registry, PyPI | Trusted to untrusted |
| Developer workstation | Mustafa's laptop | GitHub, deployment dashboards | Trusted to trusted (after MFA) |

## Assets

A. **Source code** (the GitHub repo `Mustafan4x/Vega`): the integrity of the code, branch history, and CI configuration.
B. **Production secrets**: `DATABASE_URL` (Neon DSN), `SENTRY_DSN`, plus any future API keys. Compromise of `DATABASE_URL` gives full read/write to the Neon DB.
C. **Postgres database** (Neon): pricing inputs and outputs the user has saved. Not personally identifiable, not commercially sensitive, but loss of integrity would invalidate the History feature.
D. **Backend service** (Render): availability and integrity of the FastAPI process; it is the only path between frontend and database.
E. **Frontend bundle** (Cloudflare Pages): a static site whose integrity matters because it is the public interface.
F. **CI runtime tokens**: the `GITHUB_TOKEN` granted to GitHub Actions per workflow run, plus any deploy tokens for Render or Cloudflare if the project chooses CLI based deploys.
G. **Reputation**: the project is linked from a resume. Visible compromise (defacement, leaked DSN, public exploit) is the highest impact non technical loss.

## Threats and controls

### T1. SQL injection

**Risk window**: Phase 6 onward, every query that touches user supplied values (asset price, strike, ticker symbol, date range, calculation IDs).

**Controls**:

* SQLAlchemy 2.x ORM with parameterized queries only. Manual string concatenation of SQL is banned. The Code Reviewer rejects any PR that uses `text("...")` with f strings.
* `bandit` rule `B608` (hardcoded sql with string formatting) runs on every PR.
* `semgrep` ruleset `p/sqlalchemy` runs on every PR.
* DB user has no DDL privilege in production (no `CREATE`, `ALTER`, `DROP`). Migrations run with a separate higher privilege role only during deploy.

**Residual risk**: ORM bypass via ad hoc raw SQL added in a hotfix. Caught by code review and `bandit`/`semgrep`.

**Owner**: Backend Developer (code), Security Engineer (review).

### T2. Command injection

**Risk window**: anywhere the backend or CI shell out. v1 has no obvious shell out path; the risk is mostly in CI scripts and any helper that uses `subprocess`.

**Controls**:

* `subprocess` calls always use list form arguments, never `shell=True`.
* `bandit` rule `B602` (subprocess shell true) runs on every PR.
* No user input is ever interpolated into shell commands. If a future feature needs this, it must be reviewed by the Security Engineer and use `shlex.quote` plus an explicit allow list.

**Residual risk**: a future agent introducing a one off shell call without review. Mitigated by `bandit` and required code review.

**Owner**: Backend Developer, DevOps Engineer.

### T3. Template / server side template injection

**Risk window**: nominal. FastAPI returns JSON, not HTML. The frontend uses React, which escapes by default.

**Controls**:

* No Jinja2 or other server side templating in the backend. `application/json` only. Documented in `docs/architecture.md`.
* React rendering relies on JSX escaping. Direct DOM injection via the React raw HTML injection prop (the one whose name starts with "dangerously") is banned without explicit Security Engineer review and a DOMPurify pass.
* `semgrep` ruleset `p/react` flags any use of that prop.

**Residual risk**: low.

**Owner**: Backend Developer, Frontend Developer.

### T4. Cross site scripting (XSS)

**Risk window**: Phase 3 onward (React app), Phase 6 onward (history view rendering values from the DB), Phase 8 onward (rendering ticker symbols and company names from `yfinance`).

**Controls**:

* React escapes interpolated content by default. The raw HTML injection prop is banned. `innerHTML` is banned. `eval` is banned. Dynamic `<script>` injection is banned.
* Content Security Policy applied by Cloudflare Pages headers (Phase 3 onward): `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self' https://<backend host>; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests`. The `'unsafe-inline'` for styles is needed because Tailwind plus Vite injects style tags; if the build is reconfigured to produce a single CSS bundle this can be tightened.
* `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: camera=(), microphone=(), geolocation=()` set on every backend response.
* Inputs validated server side via Pydantic (Phase 2 onward), not just on the client. Ticker symbols are restricted to `^[A-Z0-9.-]{1,10}$` (Phase 8).
* Outputs from `yfinance` (company names) are treated as untrusted text and rendered through React's escaping path; no rich HTML rendering of third party content.

**Residual risk**: a future agent introducing a third party widget with inline script. The CSP would block it; surface that as a PR objection.

**Owner**: Frontend Developer, Security Engineer.

### T5. Cross site request forgery (CSRF)

**Risk window**: any state changing endpoint that relies on ambient credentials.

**Controls**:

* The backend does not use cookie based auth. There is no end user session. State changing endpoints (Phase 6's persistence writes) are open in v1; see "Accepted residual risks" for the no auth posture.
* CORS allow list set to the exact deployed frontend origin (e.g., `https://vega.<domain>`) once the production URL is fixed in Phase 11. No wildcards. `allow_credentials` stays `False` so even if cookies were ever introduced they would not be sent cross origin.
* If end user auth is added later (per a deferred plan tracked privately), CSRF tokens or `SameSite=Strict` cookies become mandatory and this section is rewritten.

**Residual risk**: a malicious site can still call the backend's writes from a server side context (no browser involved). This is equivalent to anyone being able to call the API directly, which is the intentional v1 posture (see no auth section). Rate limiting bounds the abuse.

**Owner**: Backend Developer, Security Engineer.

### T6. Server side request forgery (SSRF), focused on yfinance (Phase 8)

**Risk window**: Phase 8 onward. The backend calls Yahoo finance via `yfinance`. The library is widely used but it is an internet egress point and the response is not under the project's control.

**Controls**:

* Hard request timeout: 5 seconds per outbound HTTP call. Failure surfaces as HTTP 504 on the backend.
* Maximum response size: 1 MB. Larger responses are dropped and logged.
* No outbound redirects to private address ranges. The HTTP client used by `yfinance` (or a wrapper around it) blocks resolution to RFC 1918, link local, loopback, and the cloud metadata IP `169.254.169.254`.
* Ticker symbol input strictly validated: `^[A-Z0-9.-]{1,10}$`. No URL, no path traversal, no Unicode look alikes.
* Response shape validated with a Pydantic model before being returned to the client; unknown fields are dropped (no `extra = "allow"`).
* Responses cached server side (Redis or in process LRU, decision deferred to Phase 8) to limit egress and to absorb upstream rate limits.
* If yfinance ever requires changes that pull from an arbitrary user supplied URL, that change requires Security Engineer review.

**Residual risk**: yfinance internally hits Yahoo endpoints we do not control. Compromise of Yahoo could feed bogus prices to the user. Mitigated only by sanity checks on numeric ranges (Risk Reviewer's domain).

**Phase 10 v1 implementation notes** (Performance Engineer review, 2026-05-03):

* The `/api/backtest` endpoint hits yfinance on every cache miss. The Performance Engineer recommended adding `@limiter.limit("10/minute")` per route on top of the global slowapi default of 60/minute per IP. The recommendation is **deferred to Phase 11 production hardening** because the existing slowapi setup creates the `Limiter` inside `build_app()` per call (so each test gets a fresh limiter with deterministic in-memory storage), which conflicts with the module-level `@limiter.limit(...)` decorator pattern slowapi expects for per-route limits. Implementing Fix B cleanly requires a refactor of the limiter ownership model; that refactor lands in Phase 11 alongside per-route limits for `/api/tickers/{symbol}` and `/api/heatmap`. The risk is bounded in the meantime by: (a) the existing 60/minute global per IP cap, (b) the historical service's 1 day TTL + 32 entry LRU cache which absorbs repeated requests on the same `(symbol, start, end)` key, (c) the historical service's 10 second hard timeout per upstream call, and (d) the engine's 1300 date cap which limits the response payload size. Documented as accepted residual risk for v1.

**Phase 8 v1 implementation notes** (Security Engineer review, 2026-05-03):

* The 1 MB response size cap is **not** enforced in the v1 implementation. yfinance buffers the entire payload internally and we never see the raw bytes. Accepted residual risk for v1: yfinance only hits hard coded Yahoo URLs; Yahoo's quoteSummary and chart payloads are single digit KB; the worst case is a memory pressure issue, not an exfiltration path. Concrete remediation if revisited: pass a custom `requests.Session` whose `send` reads the body in chunks with a hard byte ceiling, then `yf.Ticker(symbol, session=...)`.
* The 5 second hard timeout uses `concurrent.futures.future.result(timeout=...)`, which surfaces 504 to the client but does not actually cancel the worker thread (Python threads cannot be interrupted while blocked in C extensions or socket reads). The `ticker-lookup` ThreadPoolExecutor has 4 workers; under sustained Yahoo slowness the pool can fill with zombie workers and subsequent lookups block. Accepted residual risk for v1: the slowapi 60/minute per IP global limit bounds the abuse, and the cache absorbs the common case. Concrete remediation if observability later shows stalling: bake a per request `timeout=` into the requests Session passed to yfinance so the worker thread unblocks at the socket level.
* The "no outbound redirects to private address ranges" control is **not** enforced. yfinance is hard coded to Yahoo URLs and we never pass it a user URL, so the original SSRF attack surface this control addressed does not exist in v1. Accepted residual risk: a Yahoo redirect to `169.254.169.254` is implausible. Any future change that accepts a URL parameter (instead of a ticker symbol) is a Security Engineer review trigger; see the Phase 8 entry in `agents/08-security-engineer.md`.

**Owner**: Backend Developer, Security Engineer.

### T7. Broken access control

**Risk window**: every endpoint that returns or mutates data (Phase 2 onward).

**Controls**:

* In v1 there are no per user resources, so the access control model is simple: every endpoint is public. There is no IDOR surface because there are no user owned objects.
* The history endpoint (Phase 6) is global; any caller sees every saved calculation. This is intentional; see "Accepted residual risks".
* Admin or maintenance routes (e.g., a hypothetical "delete all history") are not exposed by the public API. If they are ever added, they require an out of band auth (e.g., a signed request with a shared secret known only to Mustafa) and Security Engineer sign off.

**Residual risk**: covered explicitly under "no end user auth in v1" below.

**Owner**: Backend Developer, Security Engineer.

### T8. Sensitive data exposure (secrets, DSNs, tokens)

**Risk window**: every commit, every CI run, every deployment.

**Controls**:

* `gitleaks` runs on every PR and on a scheduled weekly scan of the default branch.
* No `.env`, `.env.local`, or any file with a real secret is ever committed. `.gitignore` blocks these patterns starting in Phase 0.
* Production secrets live only in Render (backend) and Cloudflare Pages (frontend) dashboards. Local development uses `.env` files in `backend/` and `.env.local` in `frontend/`, both gitignored.
* `DATABASE_URL` is the only credentialed secret in v1. Compromise of `DATABASE_URL` requires immediate rotation (Neon dashboard, regenerate password, update Render env, redeploy).
* Backend logs scrub the DSN before printing. Logging configuration uses a redaction filter at the formatter level; tested in Phase 2.
* Sentry DSN, if used, is treated as low sensitivity (it allows event submission only, not read access), but is still kept in env vars rather than committed.
* `VITE_*` environment variables are public by design (they are baked into the JS bundle). No secret is ever placed in a `VITE_*` var. Documented in `docs/security/secrets.md` and enforced by the Frontend Developer's review.
* Browser local storage and session storage are not used to store anything sensitive. The History feature persists server side, not client side.

**Residual risk**: compromise of Render's or Cloudflare's dashboard via Mustafa's account. Mitigated by MFA on those accounts (Phase 11 hardening checklist).

**Owner**: Security Engineer, DevOps Engineer.

### T9. Insecure deserialization

**Risk window**: anywhere the backend deserializes data it did not produce.

**Controls**:

* All API input is JSON parsed by FastAPI's Starlette and validated by Pydantic. No Python `pickle` use. No `yaml.load` (only `yaml.safe_load` if YAML is ever used). No `eval`. No `exec`.
* `bandit` rules covering unsafe deserialization (`B301`, `B306`, `B321`, `B411`, etc.) run on every PR.
* `yfinance` returns deserialized objects which the backend re serializes through Pydantic before returning them to the client; raw library objects are not passed through the API surface.
* Any future feature that needs to deserialize binary data (e.g., uploaded CSV for a custom strategy) requires Security Engineer review and a separate threat model entry.

**Residual risk**: low.

**Owner**: Backend Developer, Security Engineer.

### T10. Components with known vulnerabilities (supply chain)

**Risk window**: continuous. Both `pnpm` and `pip` (via `uv`) pull from public registries.

**Controls**:

* Dependabot enabled for `pip` (the `backend/pyproject.toml` and `backend/uv.lock`) and for `pnpm` (the `frontend/package.json` and `frontend/pnpm-lock.yaml`). Configured via `.github/dependabot.yml` (DevOps Engineer wires this in Phase 0).
* `pip-audit` runs against the locked Python deps in CI on every PR and on a weekly schedule.
* `pnpm audit --audit-level=high` runs in CI on every PR.
* CodeQL enabled for both Python and JavaScript/TypeScript on the GitHub repo. CodeQL findings of severity high or critical block merge.
* Lock files (`uv.lock`, `pnpm-lock.yaml`) are committed; CI installs from the lock file only, never from a free version range.
* Any new direct dependency requires a one line justification in the PR description (the Code Reviewer enforces this informally).
* Production deploy uses a pinned Python image (e.g., `python:3.12-slim` at a digest, set in the Render service config in Phase 11) and a pinned Node version in `package.json` `engines`.

**Residual risk**: zero day in a transitive dep before Dependabot files an alert. Mitigated by minimizing the transitive surface (avoid heavy deps when a small one will do; `simplify` skill at Code Reviewer time).

**Owner**: DevOps Engineer, Security Engineer.

### T11. Insufficient logging and monitoring

**Risk window**: continuous from Phase 2 onward.

**Controls**:

* Structured JSON logging with request ID, latency, status code, and route on every backend response (Observability Engineer, Phase 2).
* Auth failures (none in v1, but if added later) log at WARN with the route and IP, never the credential.
* 4xx and 5xx responses are tracked separately. A spike in 4xx (suggesting probing) is observable; the Observability Engineer wires the alert in Phase 11.
* Sentry (if adopted) captures unhandled exceptions with stack traces. Stack traces are never shown to the user; they go only to Sentry.
* Logs do not contain the DSN, ticker query strings beyond the validated symbol, or any value flagged sensitive. Tested in Phase 2.
* Cloudflare access logs (free tier) provide a second source of truth for incoming traffic.

**Residual risk**: free tier log retention is short (Render: about 7 days). Acceptable for a pet project; documented.

**Owner**: Observability Engineer, Security Engineer.

### T12. Denial of service / abuse

**Risk window**: continuous from Phase 2 onward; severe in Phase 10 (backtests are expensive).

**Controls**:

* Rate limiting at the application layer with `slowapi` or equivalent. Suggested defaults (Project Manager to confirm at Phase 2 sign off): 60 requests per minute per IP for cheap endpoints (`/health`, pricing, Greeks); 10 per minute for heat map; 2 per minute for backtest. Burst allowance: 5 over the steady rate.
* Cloudflare WAF in front of the frontend (free tier) absorbs the majority of bot traffic before it reaches Render.
* Backend max request body size: 32 KB (way more than any legitimate input needs; protects against accidental large payloads).
* Heat map and backtest endpoints have explicit input bounds: heat map grid capped at 21 by 21 cells; backtest date range capped at 5 years; ticker symbol length capped at 10. Pydantic models reject oversized inputs with HTTP 422.
* Database connection pool sized so a runaway request cannot starve other requests (DBA's call in Phase 6).
* Render free tier has its own abuse controls at the platform level.

**Residual risk**: a determined attacker can still saturate the free tier. Acceptable for v1; if it becomes a real problem, move to a paid tier and tighten rate limits.

**Owner**: Backend Developer, DevOps Engineer, Security Engineer.

### T13. Security headers / TLS posture

**Risk window**: Phase 3 onward (frontend), Phase 11 (final hardening).

**Controls**:

* HTTPS only. HSTS header set on the backend with `max-age=31536000; includeSubDomains; preload`. Cloudflare Pages serves HTTPS by default.
* `Strict-Transport-Security` on the backend response.
* `X-Content-Type-Options: nosniff`.
* `X-Frame-Options: DENY` (or `Content-Security-Policy: frame-ancestors 'none'`, prefer the CSP form).
* `Referrer-Policy: strict-origin-when-cross-origin`.
* `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=(), usb=()`.
* TLS 1.2 minimum; TLS 1.3 enabled. Both Cloudflare and Render do this by default.
* `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Resource-Policy: same-site` on the backend, to harden against Spectre style cross origin reads.

**Residual risk**: low.

**Owner**: Frontend Developer, Backend Developer, DevOps Engineer.

### T14. Build and deploy integrity

**Risk window**: every CI run, every deploy.

**Controls**:

* Branch protection on `main`: required PR review (1 reviewer), required CI green, required signed commits where feasible (the user has the choice of GPG, SSH signing, or sigstore; the project will use the user's preferred method).
* GitHub Actions workflows pinned to commit SHAs, not floating tags. The DevOps Engineer enforces this.
* `permissions:` block in every workflow file is set to least privilege. The default `contents: read` only; jobs that need to write set the specific scope.
* OIDC tokens preferred over long lived deploy tokens where the platform supports it (Cloudflare Pages and Render both auto deploy on push, so explicit deploy tokens may not be needed; reassess at Phase 11).
* Forks cannot trigger workflows that have access to repository secrets.

**Residual risk**: compromise of GitHub itself. Out of scope.

**Owner**: DevOps Engineer, Security Engineer.

### T15. Local developer environment

**Risk window**: continuous.

**Controls**:

* `.env` and `.env.local` gitignored.
* `pre-commit` hook (DevOps Engineer wires this in Phase 0) runs `gitleaks` locally so a leak is caught before push.
* Mustafa's GitHub account has 2FA on (verify in Phase 0).
* Mustafa's Render and Cloudflare accounts have 2FA on (verify in Phase 11).

**Residual risk**: workstation compromise. Out of scope for the project; addressed at the OS level.

**Owner**: User (Mustafa), Security Engineer (advisory).

## Accepted residual risks

These are real risks the project has explicitly chosen not to fully mitigate in v1. They are accepted in writing here so a future reviewer does not need to rediscover the rationale.

### A1. No end user authentication

There is no login, no user account, no API key for end users. Anyone on the public internet can call the backend's pricing, heat map, persistence, and backtest endpoints.

**Why accepted**:

* This is a public pet project intended to be linked from a resume. Forcing visitors to sign up to try a Black Scholes pricer would defeat the purpose.
* Nothing in the system is sensitive. Pricing inputs and outputs are not personal data; they are arbitrary numbers a visitor types in.
* The History feature (Phase 6) intentionally shows everyone's calculations to everyone, like a public scratchpad. If a visitor types something they consider private, they have made a mistake; the UI states clearly that submissions are public.

**Compensating controls**:

* Rate limiting (T12) bounds resource abuse.
* The DB has no PII column. No emails, no IP addresses are persisted alongside calculations.
* The backend logs rotate and the IP address is not joined with persisted rows; an attacker cannot reconstruct who submitted a given history entry.
* If end user auth is ever added, the threat model is rewritten and a separate auth phase is opened (the deferred plan is tracked privately).

### A2. History is publicly readable

Every visitor can read every saved calculation.

**Why accepted**: same rationale as A1. The History page is a feature, not a leak.

**Compensating controls**: the UI states the public nature of submissions. No user supplied free text fields are included; only numeric inputs.

### A3. yfinance is the sole upstream price source

The project depends on `yfinance`, which depends on Yahoo's undocumented endpoints.

**Why accepted**: the alternative paid price feeds are not free; the user has stated the project will use yfinance.

**Compensating controls**: SSRF controls (T6), caching, and a graceful fallback to user supplied price input if the upstream is down.

### A4. Free tier hosting limitations

Render free tier sleeps after inactivity, Neon free tier has a connection cap, Cloudflare Pages free tier rate limits build minutes.

**Why accepted**: this is a pet project. Cost matters more than cold start latency.

**Compensating controls**: none beyond what the platforms provide. Documented in `docs/setup-guide.md`.

### A5. No customer data, so no formal data classification

The project does not handle PII, PCI, PHI, or any regulated data class. Therefore there is no formal data classification or data retention policy beyond "we keep history rows forever until the user manually clears them".

**Why accepted**: out of scope for a pet project. If the project ever takes real user data, this section is rewritten.

### A6. No formal incident response plan

There is no on call rotation, no PagerDuty, no incident commander.

**Why accepted**: pet project. The implicit incident response is "Mustafa notices and fixes it".

**Compensating controls**: Sentry alerts (if adopted) email Mustafa on unhandled exceptions. Cloudflare emails on traffic spikes.

## Phase 0 user actions

The user (Mustafa) must perform these GitHub click ops by hand. They cannot be done by an agent because they require an authenticated browser session. Do these once before Phase 1 begins.

### Branch protection on `main`

1. Go to https://github.com/Mustafan4x/Vega/settings/branches.
2. Click **Add branch ruleset** (or **Add rule**, depending on which UI variant is current).
3. Set **Branch name pattern** to `main`.
4. Enable the following toggles:
   * **Restrict deletions**.
   * **Require a pull request before merging**.
     * Sub option: **Require approvals** = 1.
     * Sub option: **Dismiss stale pull request approvals when new commits are pushed**.
   * **Require status checks to pass before merging**.
     * Sub option: **Require branches to be up to date before merging**.
     * Sub option: under **Status checks that are required**, add (after Phase 0 wires CI): `lint`, `test`, `gitleaks`, `bandit`, `semgrep`, `pip-audit`, `pnpm-audit`, and the CodeQL checks for Python and JavaScript. If those check names do not exist yet, save the rule first and add the checks once CI runs once.
   * **Require signed commits** (use whichever signing method you prefer: GPG, SSH, or sigstore).
   * **Require linear history**.
   * **Block force pushes**.
5. Click **Create** (or **Save changes**).
6. Verify by opening a no op PR and confirming the merge button is gated on the checks above.

### Dependabot for pip and pnpm

1. Go to https://github.com/Mustafan4x/Vega/settings/security_analysis.
2. Under **Dependabot**:
   * Enable **Dependabot alerts**.
   * Enable **Dependabot security updates**.
   * Enable **Dependabot version updates**. This requires a `.github/dependabot.yml` file in the repo; the DevOps Engineer agent writes that file in Phase 0. Once the file is committed, the toggle takes effect.
3. After the DevOps Engineer commits `.github/dependabot.yml`, return to this page and confirm Dependabot has indexed both the `backend/` (pip via `uv.lock`) and `frontend/` (pnpm via `pnpm-lock.yaml`) ecosystems.

### CodeQL for Python and JavaScript/TypeScript

1. Go to https://github.com/Mustafan4x/Vega/settings/security_analysis.
2. Under **Code scanning**, click **Set up** next to **CodeQL analysis**.
3. Choose **Default** setup. GitHub will auto detect Python and JavaScript/TypeScript and run the standard query suites.
4. If the **Default** option is not available (some org settings disable it), choose **Advanced** and accept the auto generated `.github/workflows/codeql.yml`. Verify the languages list contains both `python` and `javascript-typescript`.
5. Confirm the first CodeQL run completes (it appears under the **Security** tab, **Code scanning** subtab) and that no critical findings are open.

### Secret scanning push protection

1. On the same `settings/security_analysis` page:
2. Enable **Secret scanning**.
3. Enable **Push protection** (this blocks pushes that contain known secret formats).
4. Optional but recommended: enable **Validity checks** (GitHub probes the secret to confirm it is live; useful but not required).

### 2FA on the GitHub account

1. Confirm 2FA is enabled at https://github.com/settings/security. If not, enable it (TOTP via an authenticator app is fine; a hardware key is better).

### Verification

After all of the above, the Security Engineer agent (in a future session) verifies:

* A test PR with a known dummy secret is rejected by push protection.
* A test PR with a deliberately vulnerable dependency triggers a Dependabot alert.
* A test PR with an obvious SQL injection pattern in Python triggers either CodeQL or `bandit` (CodeQL preferred; either is acceptable for v1).
* The merge button on the test PR is disabled until all required checks pass.

If any of these verifications fail, the Security Engineer agent reopens this section and investigates before signing off Phase 0.
