# Secrets reference

Owner: Security Engineer agent.
Last updated: 2026-05-03 (Phase 11).

This is the canonical list of every secret the project uses or will use, where each one lives, who has access to it, and the rotation policy. The Documentation Engineer keeps `docs/setup-guide.md` aligned with this file. **Never paste a real secret into this file or any other committed file.**

The table is grouped by phase to make it obvious when each new secret enters the project.

## Definitions

* **Secret**: any value whose disclosure would let someone do something the project does not want them to do (for example, write to the production database, submit telemetry to a paid Sentry plan, or impersonate a deploy).
* **Public config**: a value that is not secret but is environment specific (for example, the production backend URL the frontend talks to). Public config still belongs in env vars so the same code runs in dev, staging, and prod, but disclosure is harmless.

The frontend uses Vite, which inlines any env var prefixed with `VITE_` into the client JavaScript bundle. **Anything inlined into the bundle is public.** Therefore no real secret may ever live in a `VITE_*` variable. This is enforced by review and by the Frontend Developer's discipline.

## Master table

| Name | Type | Where it lives (production) | Where it lives (local dev) | Who has access | Introduced in phase | Rotation policy |
|---|---|---|---|---|---|---|
| `VEGA_DATABASE_URL` | Secret (DSN with embedded password) | Render web service env var | `backend/.env` (gitignored) | Mustafa, Render runtime, Neon. | Phase 6. | Rotate immediately if the value appears in any log, screenshot, or repo. Otherwise rotate annually as hygiene. Procedure: regenerate the password in the Neon dashboard, update Render env, redeploy. |
| `VEGA_CORS_ORIGINS` | Public config (comma separated origin list) | Render web service env var | `backend/.env` (dev only; defaults to `http://localhost:5173`) | Mustafa, Render runtime. | Phase 2; production fail loud added in Phase 11. | No rotation. Update when the frontend domain changes. Production refuses empty, wildcard, or HTTP origins at boot. |
| `VITE_API_BASE_URL` | Public config (URL string) | Cloudflare Pages env var | `frontend/.env.local` (gitignored) | Public (baked into JS bundle). | Phase 3; production fail loud added in Phase 11. | No rotation; this is just the production backend URL. Production refuses empty or localhost values at first request. |
| `SENTRY_DSN` | Low sensitivity (event submission only) | Render web service env var | `backend/.env` optional (gitignored) | Mustafa, Render runtime, Sentry. | Phase 2 or Phase 11 (Observability Engineer's call; not adopted in v1). | Rotate if the project changes Sentry organization or if abuse is suspected. Otherwise no scheduled rotation. |
| `VEGA_ENVIRONMENT` | Public config (string `"production"` / `"development"`) | Render web service env var | `backend/.env` | Public. | Phase 2. | No rotation. |
| `VEGA_RATE_LIMIT_DEFAULT` | Public config (rate spec, e.g., `60/minute`) | Render web service env var | `backend/.env` (optional) | Public. | Phase 2. | No rotation. |
| `GITHUB_TOKEN` | Ephemeral CI secret | GitHub Actions runtime (auto provisioned per job) | n/a | GitHub Actions per job. | Phase 0. | Auto rotated by GitHub on every workflow run. The project does not store or persist this token. |
| `CLOUDFLARE_API_TOKEN` | Secret (only if CLI deploys are chosen) | GitHub Actions secret `CLOUDFLARE_API_TOKEN` | n/a | Mustafa, the workflow that uses it. | Phase 11 (only if CLI deploys; the default in this repo uses the Cloudflare Pages GitHub integration which does not store a token). | Rotate every 90 days while in use. Procedure: revoke the token at https://dash.cloudflare.com/profile/api-tokens, create a new one with the same scope, update the GitHub Actions secret. |
| `RENDER_API_KEY` | Secret (only if CLI deploys are chosen) | GitHub Actions secret `RENDER_API_KEY` | n/a | Mustafa, the workflow that uses it. | Phase 11 (only if CLI deploys; Render's GitHub integration auto deploys via Blueprint without a stored key). | Rotate every 90 days while in use. |
| `NEON_API_KEY` | Secret (only if CLI tooling is used for migrations from CI) | GitHub Actions secret `NEON_API_KEY` | n/a | Mustafa, the workflow that uses it. | Not adopted in v1. CI does not run migrations; Mustafa runs `alembic upgrade head` from a local shell during a maintenance window. | Rotate every 90 days while in use. |

## Notes on each secret

### `VEGA_DATABASE_URL`

Format: `postgresql+psycopg://<user>:<password>@<host>:<port>/<dbname>?sslmode=require`. SSL is required by Neon; the connection string includes `sslmode=require`.

* The backend reads it via `os.environ["VEGA_DATABASE_URL"]` at startup and constructs the SQLAlchemy engine. The raw value is never logged. A redaction filter is applied at the Python logging level so even if a developer accidentally logs the engine URL, the password is masked.
* Local dev uses SQLite by default if `VEGA_DATABASE_URL` is unset, so the developer does not need a real Neon connection on their workstation.
* The DB user embedded in the production DSN (the **application** role, named `vega_app` in `docs/setup-guide.md`) has only `SELECT` and `INSERT` privileges on the `calculation_inputs` and `calculation_outputs` tables, scoped to those tables specifically (not schema wide). No `UPDATE`, `DELETE`, or any DDL. The production deploy procedure (Phase 11) creates this application role at the same time as it creates a separately named migration role.
* The migration role is the **owner** DSN (the one Neon hands you on project creation) with `CREATE`, `ALTER`, and `DROP` on the schema, used only by `alembic upgrade head` during deploy. The migration DSN lives only in Mustafa's local shell session, never in CI, never in Render env. After each successful deploy, the deploy script does NOT keep the migration DSN in any persistent location.

### `VITE_API_BASE_URL`

Format: `https://<backend host>` (no trailing slash). Example: `https://vega-backend.onrender.com`.

* Inlined into the frontend bundle at build time. Anyone who views the deployed site source can read it. This is fine; the backend is independently public.
* The frontend's `readApiBaseUrl` function (in `src/lib/api.ts`) refuses to make calls in a production bundle (`import.meta.env.PROD === true`) when the value is empty or starts with `http://localhost`. A misconfigured deploy throws on the first request with a clear message pointing at this guide. See `frontend/src/lib/api.test.ts` for the assertions.

### `VEGA_CORS_ORIGINS`

Format: comma separated list of origins, each in `https://...` form. Example: `https://vega.pages.dev,https://api.vega.example.com`.

* The backend reads it at startup. In production (`VEGA_ENVIRONMENT=production`) the loader fails loud and refuses to boot when the value is empty, contains `*`, or contains any non https origin (`app/core/config.py`, `_validate_production`). See `backend/tests/api/test_environment.py` for the assertions.
* Dev defaults to `http://localhost:5173` only when the loader is not in production mode. A wildcard would defeat the threat model T8 protection against arbitrary cross origin reads of the API.

### `SENTRY_DSN`

Format: `https://<key>@<org>.ingest.sentry.io/<project>`.

* Sentry DSNs are designed to be embeddable in client side code; they grant event submission only, not read access. They are still kept in env vars so the same code runs without Sentry in dev (when the DSN is unset).
* If Sentry is wired into the frontend (the Observability Engineer may decide either way), the DSN goes into `VITE_SENTRY_DSN` and is treated as public. If only the backend uses Sentry, it stays in `SENTRY_DSN` (server side env).
* Optional in v1; the Observability Engineer makes the call in Phase 2 or Phase 11.

### `VEGA_ENVIRONMENT`

Toggles behavior:

* `VEGA_ENVIRONMENT=development` (default) enables `/docs` and `/openapi.json` (FastAPI's OpenAPI UI) and accepts a localhost CORS fallback.
* `VEGA_ENVIRONMENT=production` disables `/docs` and `/openapi.json`, enforces fail loud CORS validation, and enforces the generic error responses described in the Phase 2 checklist.

Not a secret, but it lives in the env block alongside secrets and is documented here for completeness.

### `VEGA_RATE_LIMIT_DEFAULT`

Application wide per IP rate limit applied across every endpoint via `application_limits` on the slowapi limiter. Default `60/minute`. Per route caps on heavier endpoints (heatmap, tickers, backtest) are tighter and live in code, not env. See `docs/api.md`.

Not a secret. Documented here for completeness.

### `GITHUB_TOKEN`

Auto provisioned by GitHub Actions on every workflow run. The project never stores it. Workflows that need to push back to the repo (for example, Dependabot creating PRs) use it via `${{ secrets.GITHUB_TOKEN }}` in YAML; the workflow's `permissions:` block scopes the token down to the minimum (`contents: read` by default).

### `CLOUDFLARE_API_TOKEN`, `RENDER_API_KEY`, `NEON_API_KEY`

These three are conditional. They are introduced **only if** the project moves to CLI based deploys (e.g., a GitHub Actions job that runs `wrangler pages deploy`). The default in this repo is to use each platform's GitHub integration, which performs auto deploys without storing API keys in CI. Re evaluate in Phase 11 once the deploy story is finalized.

If introduced:

* Tokens are scoped to the minimum: a Cloudflare token scoped to "Edit Pages" on the specific project; a Render token scoped to the specific service; a Neon token scoped to the specific project.
* Tokens are stored as GitHub Actions secrets (repository scope; not organization scope, since this is a personal repo).
* Each token has a calendar reminder on Mustafa's calendar at 90 days for rotation. The Security Engineer agent's role is to remind the user one week before the deadline and to verify rotation took place.

## Where the secrets are NOT

Listing the absence of secrets is as important as listing where they are.

* No secret is in any file under `frontend/`, `backend/app/`, `backend/tests/`, `frontend/src/`, `docs/`, or any other tracked path. Verified by `gitleaks` on every PR.
* No secret is in any committed `.env`, `.env.local`, `.env.production`, or similar file. The committed `.env.example` files contain only placeholder values (e.g., `DATABASE_URL=postgresql://user:password@host:5432/dbname`).
* No secret is hard coded into a Docker image. The `Dockerfile` references env vars at runtime; secrets are injected by Render's env var system at container start.
* No secret is in Sentry breadcrumbs, error messages, or log lines. The logging redaction filter masks any value that matches a DSN regex.
* No secret is in a screenshot or attachment in any `docs/` file. The Documentation Engineer reviews this on every doc PR.

## Incident response runbook: leaked secret

If a secret is found in a committed file, a public log, a screenshot, or anywhere else it should not be:

1. **Rotate immediately**, before doing anything else. Do not wait for the postmortem.
   * `DATABASE_URL`: regenerate the password in the Neon dashboard. Update Render env. Redeploy. Confirm the old password no longer works (`psql` against the old DSN should fail).
   * `CLOUDFLARE_API_TOKEN`, `RENDER_API_KEY`, `NEON_API_KEY`: revoke at the issuing dashboard. Create a new token. Update the GitHub Actions secret.
   * `SENTRY_DSN`: revoke and regenerate at the Sentry dashboard.
2. **Audit access**. For a leaked DB DSN: pull the Neon connection log and look for connections from unexpected IPs or at unexpected times. For a leaked CI token: pull the GitHub audit log for the repo.
3. **Purge the secret from git history** if it was committed. Use `git filter-repo` or BFG. Force push the rewritten history. Notify any collaborators (in this repo, just the user) so they can re clone.
4. **File a postmortem** at `docs/security/incidents/YYYY-MM-DD-<short-name>.md` describing what leaked, how it leaked, the rotation timestamp, and the corrective action that prevents recurrence.
5. **Update this file** with the lesson learned (for example, "added a regex for `<format>` to the `gitleaks` config").

This runbook is owned by the Security Engineer agent and should be tabletop tested by Mustafa once before Phase 11 closes.
