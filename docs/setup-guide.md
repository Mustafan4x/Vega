# Setup guide

This guide is for the human (Mustafa) to walk through. Anything that requires a browser session, a one time signup, a payment method on file, or a click on someone else's UI lives here. The Documentation Engineer keeps this file current as the project ships.

<!-- TODO: this file is a starter scaffold. The Documentation Engineer agent will expand each section with screenshots, exact CLI invocations, and verified copy as the corresponding phases complete. -->

## Accounts you will need

All of these have free tiers that are enough for this project.

1. **GitHub**: https://github.com/Mustafan4x/Trader (already created).
2. **Cloudflare**: for Cloudflare Pages (frontend hosting). Sign up at https://dash.cloudflare.com/sign-up.
3. **Render**: for FastAPI backend hosting. Sign up at https://render.com/.
4. **Neon**: for managed Postgres. Sign up at https://neon.tech/.
5. **Optional, only if you want a custom domain**: a domain registrar (Cloudflare Registrar is fine, no markup over wholesale).

## Hosting choice: Cloudflare Pages vs Vercel

The project defaults to **Cloudflare Pages** for the frontend. Reasons:

* The free tier is generous.
* Cloudflare's WAF and DDoS protection are best in class.
* It pairs cleanly with Cloudflare Workers if edge logic is added later.

Vercel remains a fine alternative. Recent reports of Vercel related incidents have not been independently verified by this project; for a public pet project that does not store user secrets, the practical risk of using either platform is low. The decision was made on platform fit, not on incident response. If Vercel is preferred, the deploy steps are nearly identical; pick one and stick with it.

## Backend hosting: Render vs Fly.io

Render is the default in this guide because the dashboard is simpler. Fly.io is a fine alternative; pick whichever you like. **Do not** try to host the FastAPI backend on Vercel or Cloudflare Pages: those platforms are designed for static plus edge functions and do not host long lived Python servers well.

## Local development setup

These steps run on Mustafa's machine. They do not require any cloud accounts. The canonical local path is `/home/mustafa/src/trader/` (lowercase, regardless of the GitHub repo's display name).

1. Install `uv` (Python toolchain): `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Install Node.js (LTS) and `pnpm`: see https://pnpm.io/installation.
3. If the local working directory does not exist yet (fresh machine), clone with: `git clone https://github.com/Mustafan4x/Trader.git /home/mustafa/src/trader`. On Mustafa's primary machine the directory is already wired up by the DevOps Engineer agent in Phase 0; no clone needed there.
4. Install Python deps: `cd /home/mustafa/src/trader/backend && uv sync`
5. Install frontend deps: `cd /home/mustafa/src/trader/frontend && pnpm install`
6. Start the backend: `cd /home/mustafa/src/trader/backend && uv run uvicorn app.main:app --reload`
7. Start the frontend: `cd /home/mustafa/src/trader/frontend && pnpm dev`
8. Open `http://localhost:5173` in a browser.

The DevOps Engineer agent will fill in the exact directory layout, env var template (`.env.example`), and `docker-compose up` flow once Phase 0 is complete.

## First time deployment

These steps are sequenced so each one fails loudly if the prior one was skipped.

### Database (Neon)

1. Sign in to Neon, create a project, name it `trader`.
2. Copy the connection string from the dashboard.
3. Store it locally as `DATABASE_URL` in a `.env` file (never commit this file).
4. Run the Alembic migration locally to verify connectivity: `uv run alembic upgrade head`.

### Backend (Render)

1. Sign in to Render, create a new Web Service, point it at the GitHub repo.
2. Set the build command per the DevOps Engineer's `render.yaml` (filled in during Phase 11).
3. Set environment variables in the Render dashboard: `DATABASE_URL`, `ENVIRONMENT=production`, plus any others the Security Engineer specifies.
4. Confirm the public URL responds at `/health`.

### Frontend (Cloudflare Pages)

1. Sign in to Cloudflare, go to Pages, connect the GitHub repo.
2. Build command: `pnpm install && pnpm build`. Output directory: `frontend/dist`.
3. Set the env var `VITE_API_BASE_URL` to the Render backend URL.
4. Confirm the deployed URL loads and the form submits successfully against the production backend.

### Custom domain (optional)

1. Buy a domain at any registrar (Cloudflare Registrar is sold at wholesale).
2. In Cloudflare Pages, add the custom domain. Cloudflare will configure DNS automatically if the domain is on Cloudflare.
3. Update `VITE_API_BASE_URL` if you also want a custom subdomain for the API.

## Things you will be asked to click during setup

This list will grow as the agents do their work. Whenever an agent needs the human to log in somewhere, click "I agree", or provide a billing email, that step ends up here.

* GitHub: accept any required org or branch protection prompts.
* Cloudflare Pages: confirm the OAuth permission grant to read the repo.
* Render: confirm the OAuth permission grant to read the repo.
* Neon: nothing beyond signup and copying the connection string.

## Secrets reference

Every secret used by the project is listed here. Never paste a real value into this file or any committed file.

| Name | Where it lives | What it is |
|---|---|---|
| `DATABASE_URL` | Render env, local `.env` | Postgres connection string from Neon. |
| `VITE_API_BASE_URL` | Cloudflare Pages env, local `.env.local` | Public URL of the Render backend. |
| `SENTRY_DSN` | Render env, local `.env` (optional) | Filled in by the Observability Engineer if Sentry is adopted. |

The Security Engineer agent owns this table and updates it whenever a new secret is introduced. The Documentation Engineer agent verifies the table matches the actual code.
