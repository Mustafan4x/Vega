# Setup guide

Step by step walkthrough for deploying Vega to production. Target time on a fresh laptop: under 30 minutes. Skip the local dev section if you already have a working dev environment.

## What you will build

* **Frontend** on Cloudflare Pages, served from `https://<project>.pages.dev`.
* **Backend** on Render, served from `https://<service>.onrender.com`, behind a Docker container.
* **Database** on Neon (managed Postgres), accessed by the backend via `VEGA_DATABASE_URL`.

All three services have free tiers that cover this project comfortably.

## Accounts you will need

1. **GitHub**: <https://github.com/Mustafan4x/Vega> (already created).
2. **Cloudflare**: <https://dash.cloudflare.com/sign-up>.
3. **Render**: <https://render.com/>.
4. **Neon**: <https://neon.tech/>.
5. **Auth0**: <https://manage.auth0.com>.
6. **Optional**: a domain registrar if you want a custom domain.

## Hosting choice rationale

* **Frontend on Cloudflare Pages**, not Vercel: free tier is generous, the WAF and DDoS protection are best in class, and Cloudflare Workers pair cleanly if edge logic is added later. Vercel works too; pick one and stick with it.
* **Backend on Render**, not Vercel or Cloudflare Pages: those platforms are designed for static plus edge functions. They do not host long lived Python servers well. Fly.io is a fine alternative to Render.
* **Database on Neon**, not RDS or Heroku Postgres: Neon's free tier is the best in class for a low traffic project, with branching for staging/prod.

## Local development setup

These steps run on your machine. They do not require any cloud accounts. The canonical local path is `/home/mustafa/src/vega/`.

```bash
# Tooling
curl -LsSf https://astral.sh/uv/install.sh | sh
# Install Node.js LTS plus pnpm: https://pnpm.io/installation

# Backend
cd /home/mustafa/src/vega/backend
uv sync
uv run pytest                     # 295+ tests, all green
uv run vega-serve               # http://localhost:8000

# Frontend (in a second terminal)
cd /home/mustafa/src/vega/frontend
pnpm install
pnpm test --run                   # 114+ tests, all green
pnpm dev                          # http://localhost:5173
```

Open `http://localhost:5173` in a browser; the Pricing screen should load and a Calculate against `S=100, K=100, T=1, r=0.05, sigma=0.20` should return call ≈ 10.45 and put ≈ 5.57.

### Local Postgres parity (optional)

```bash
cd /home/mustafa/src/vega
docker compose up -d              # binds Postgres to 127.0.0.1:5432 only
cd backend
VEGA_DATABASE_URL=postgresql+psycopg://vega:vega@127.0.0.1:5432/vega \
  uv run alembic upgrade head
```

The dev SQLite store at `backend/var/vega.db` is the default if `VEGA_DATABASE_URL` is unset.

## First time deployment

The order matters. Each step verifies the previous one. **Do not skip ahead**: a missing CORS origin or a wrong DSN at the wrong moment is the most common pet project deployment failure.

### Step 1. Database (Neon)

1. Sign in to <https://console.neon.tech/>.
2. **Create a project**: name it `vega`, region `US East (Ohio)` (or whichever is closest to your Render region).
3. **Copy the connection string** from the dashboard's "Connection details" pane. It looks like:
   `postgresql://<user>:<pwd>@<host>.us-east-2.aws.neon.tech/<db>?sslmode=require`
4. **Create the application role** (least privilege; do not use the owner role at runtime). In the Neon SQL editor:
   ```sql
   CREATE ROLE vega_app WITH LOGIN PASSWORD '<paste a strong password>';
   GRANT CONNECT ON DATABASE neondb TO vega_app;
   GRANT USAGE ON SCHEMA public TO vega_app;
   GRANT SELECT, INSERT ON calculation_inputs, calculation_outputs TO vega_app;
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vega_app;
   ```
   Construct the application DSN by replacing the user and password in the connection string from step 3 with `vega_app:<password>`.
5. **Run the schema migration locally** using the OWNER role's DSN (the one from step 3, not the application role):
   ```bash
   cd backend
   VEGA_DATABASE_URL='<owner DSN from step 3>' uv run alembic upgrade head
   ```
   You should see `INFO  [alembic.runtime.migration] Running upgrade -> 9c8f64a81798`.
6. **Verify** that `\dt` from the Neon SQL console lists `calculation_inputs` and `calculation_outputs`. The application DSN now has only `SELECT, INSERT` on those two tables.

The owner DSN never leaves your local shell history. The `vega_app` DSN goes to Render in the next step.

### Step 2. Backend (Render)

1. Sign in to <https://dashboard.render.com/>.
2. **Connect GitHub**: top right, "New" -> "Blueprint", connect the `Mustafan4x/Vega` repo. Render reads `/render.yaml` from the repo root.
3. Render will offer to create a service named `vega-backend` (Docker, free plan, Oregon). Accept.
4. **Set the env vars** Render flagged as `sync: false` (these are not in `render.yaml`):
   * `VEGA_CORS_ORIGINS`: paste the eventual Cloudflare Pages URL. You do not have it yet, so leave a placeholder like `https://placeholder.pages.dev`. We come back here at the end.
   * `VEGA_DATABASE_URL`: paste the **vega_app** DSN from Step 1.4 (not the owner DSN).
5. **Deploy**. Render builds the Docker image (4-6 minutes for a cold build, 1-2 minutes after the first), then starts the service. Watch the build log.
6. **Verify the deploy**:
   ```bash
   curl https://<service>.onrender.com/health
   # -> {"status":"ok"}
   ```
   If `/health` is 200, the service is live. If it 502s, Render is waking from cold start (free tier sleeps after 15 min of idle); retry once.
7. **Note the Render URL** (e.g., `https://vega-backend-abc.onrender.com`). You will paste it into Cloudflare Pages in the next step.

### Step 3. Frontend (Cloudflare Pages)

1. Sign in to <https://dash.cloudflare.com/>.
2. **Pages** -> **Create application** -> **Connect to Git**. Authorize Cloudflare to read the `Mustafan4x/Vega` repo.
3. Build settings:
   * Framework preset: `None` (we want explicit control).
   * Build command: `pnpm install --frozen-lockfile && pnpm build`
   * Build output directory: `dist`
   * Root directory (advanced): `frontend`
4. **Environment variables** (Production):
   * `VITE_API_BASE_URL` = the Render URL from Step 2.7 (e.g., `https://vega-backend-abc.onrender.com`).
   * `NODE_VERSION` = `22`
   * `PNPM_VERSION` = `10`
5. **Save and Deploy**. Cloudflare runs the build (~2 minutes); the result lands at `https://<project>.pages.dev`.
6. **Verify the deploy**:
   * Open the Pages URL in a browser. The Pricing screen loads.
   * Open dev tools, Network tab. Submit the form. The request to `/api/price` should be 200.
   * If you see a CORS error, the `VEGA_CORS_ORIGINS` value in Render is still the placeholder; go to Step 4.

### Step 4. Tie the loop closed

1. **Copy the Cloudflare Pages URL** (e.g., `https://vega-abc.pages.dev`).
2. **In Render** -> your service -> Environment, edit `VEGA_CORS_ORIGINS` to the exact Pages URL. Save and redeploy.
3. **Wait for Render to finish redeploying** (~1 minute).
4. **Reload the Pages URL** and submit the Pricing form. The 200 should be clean.
5. **Smoke test** every screen: Pricing, Heat Map, Compare, Backtest, History. Each should round trip a valid request.

## Custom domain (optional)

1. Buy a domain at any registrar (Cloudflare Registrar is sold at wholesale).
2. **Cloudflare Pages** -> your project -> Custom domains -> Add custom domain. Cloudflare auto provisions DNS if the domain is on Cloudflare.
3. **Add the apex domain to Render** (optional, for a custom backend URL): Render -> service -> Settings -> Custom Domains. Verify ownership via TXT record.
4. **Update `VEGA_CORS_ORIGINS`** in Render to include the custom frontend domain.
5. **Update `VITE_API_BASE_URL`** in Cloudflare Pages to the custom backend domain (if you set one).
6. **Update `_headers`** in `frontend/public/_headers` to swap `https://*.onrender.com` for the custom backend domain in the `connect-src` directive. Commit and let Cloudflare Pages redeploy.

## Things you will be asked to click during setup

* **GitHub**: accept the OAuth permission prompt for Cloudflare Pages (read the repo).
* **GitHub**: accept the OAuth permission prompt for Render (read the repo).
* **Neon**: nothing beyond signup and copying the connection string.
* **Cloudflare**: nothing beyond signup and connecting the GitHub repo.
* **Render**: nothing beyond signup and connecting the GitHub repo, plus pasting the two `sync: false` env vars.

## Branch protection (recommended after first deploy)

Apply on GitHub at <https://github.com/Mustafan4x/Vega/settings/branches>:

* Require a pull request before merging to `main`.
* Require at least one approving review.
* Require status checks: the four CI jobs in `.github/workflows/ci.yml` (`backend`, `frontend`, `secrets-scan`, `bandit`, `semgrep`).
* Require branches to be up to date before merging.
* Restrict who can push to `main`.

Also enable Dependabot (Settings -> Code security -> Dependabot alerts) and CodeQL (Settings -> Code security -> Code scanning) for both Python and JavaScript/TypeScript.

## Secrets reference

Every secret used by the project is listed here. Never paste a real value into this file or any committed file. The Security Engineer agent owns this table and updates it whenever a new secret is introduced.

| Name | Where it lives | What it is |
|---|---|---|
| `VEGA_DATABASE_URL` | Render env vars (production), local `.env` (dev only) | Postgres connection string for the **application** role at Neon. Limited to `SELECT, INSERT` on `calculation_inputs` and `calculation_outputs`. |
| `VEGA_CORS_ORIGINS` | Render env vars (production), local `.env` (dev only) | Comma separated list of allowed frontend origins. Production fail loud rejects empty values, wildcards, and HTTP origins. |
| `VITE_API_BASE_URL` | Cloudflare Pages env vars (production), local `.env.local` (dev only) | Public URL of the Render backend. Baked into the frontend bundle at build time. Production fail loud rejects empty and localhost values. |
| `VITE_AUTH0_DOMAIN` | Cloudflare Pages env vars (production), local `.env.local` (dev only) | Auth0 tenant domain (e.g., `<tenant>.us.auth0.com`). Baked into the frontend bundle at build time. Production fail loud rejects empty values. |
| `VITE_AUTH0_CLIENT_ID` | Cloudflare Pages env vars (production), local `.env.local` (dev only) | Auth0 SPA application client ID. Baked into the frontend bundle at build time. Production fail loud rejects empty values. |
| `VITE_AUTH0_AUDIENCE` | Cloudflare Pages env vars (production), local `.env.local` (dev only) | Auth0 API identifier (`vega-api`). Sent in the SDK's `audience` parameter so issued tokens carry the right `aud` claim. |
| `VITE_AUTH0_REDIRECT_URI` | Cloudflare Pages env vars (production), local `.env.local` (dev only) | Full callback URL (e.g., `https://vega-2rd.pages.dev/callback`). Must match an Allowed Callback URL in the Auth0 SPA application. |
| `VEGA_AUTH0_DOMAIN` | Render env vars (production), local shell env (dev only) | Auth0 tenant domain. The backend fetches the JWKS from `https://<this>/.well-known/jwks.json` to verify JWT signatures. Production fail loud rejects empty values. |
| `VEGA_AUTH0_AUDIENCE` | Render env vars (production), local shell env (dev only) | Auth0 API identifier (`vega-api`). The backend rejects any JWT whose `aud` claim does not match. Production fail loud rejects empty values. |

The owner DSN at Neon (DDL privileges) never goes into Render. Migrations run from a developer's shell during a maintenance window.

## Rollback

* **Frontend**: Cloudflare Pages -> Deployments -> select a previous build -> Rollback. Effective in seconds.
* **Backend**: Render -> Manual Deploy -> select a previous commit. Effective in 1-2 minutes.
* **Database**: Neon supports point in time restore on paid plans. On the free tier, the schema is small enough to hand re run.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Failed to fetch` in browser console | CORS misconfigured | Verify `VEGA_CORS_ORIGINS` in Render exactly matches the Pages URL (including https://). |
| `VITE_API_BASE_URL is not set` in console | Cloudflare Pages env var missing | Set `VITE_API_BASE_URL` in Pages and trigger a redeploy. |
| Backend returns 502 | Render free tier cold start | Wait 30 seconds and retry; or upgrade to a paid plan. |
| 429 on every request | Rate limit hit | The default is 60/minute per IP; throttle the client or set `VEGA_RATE_LIMIT_DEFAULT` higher. Per route caps on `/api/heatmap`, `/api/tickers`, `/api/backtest` are tighter (see `docs/api.md`). |
| Migration fails on Neon | Owner DSN wrong | Use the connection string with the OWNER role from Neon's "Connection details", not the application role. |
| `pnpm` not found in Cloudflare build | Node setup | Cloudflare Pages auto detects `pnpm-lock.yaml`. If not, set `PNPM_VERSION=10` in env vars. |

## Auth0 setup (Phase 12)

Vega uses Auth0 for sign-in. Provision a free tenant and register two artifacts: a Single Page Application (the frontend) and an API (the backend audience).

1. Create an Auth0 tenant at <https://manage.auth0.com>. Free tier covers 7,500 monthly active users; Vega will not approach this.
2. **Create the API**: Applications, then APIs, then Create API. Name `Vega API`, identifier `vega-api`, signing algorithm `RS256`. The identifier is the `audience` value the frontend and backend share.
3. **Create the SPA**: Applications, then Applications, then Create Application. Type `Single Page Web Applications`. After creation, set:
   - Allowed Callback URLs: `http://localhost:5173/callback, https://vega-2rd.pages.dev/callback`.
   - Allowed Logout URLs: `http://localhost:5173, https://vega-2rd.pages.dev`.
   - Allowed Web Origins: `http://localhost:5173, https://vega-2rd.pages.dev`.
   - Refresh Token Rotation: enabled. Refresh Token Expiration: rotating.
4. **Enable identity providers**: Authentication, then Social, then enable Google and GitHub. No magic link, no email plus password.

### Frontend env vars (Cloudflare Pages, build-time)

```
VITE_AUTH0_DOMAIN=<tenant>.us.auth0.com
VITE_AUTH0_CLIENT_ID=<spa client id>
VITE_AUTH0_AUDIENCE=vega-api
VITE_AUTH0_REDIRECT_URI=https://vega-2rd.pages.dev/callback
```

A production build without `VITE_AUTH0_DOMAIN` or `VITE_AUTH0_CLIENT_ID` aborts (fail-loud).

### Backend env vars (Render service env)

```
VEGA_AUTH0_DOMAIN=<tenant>.us.auth0.com
VEGA_AUTH0_AUDIENCE=vega-api
```

Production startup fails loud if either is missing when `VEGA_ENVIRONMENT=production`.

### Local dev

Copy `frontend/.env.example` to `frontend/.env.local` and fill in the SPA values. The backend reads its values from your shell env when you run `uv --project backend run uvicorn app.main:app --reload`.
