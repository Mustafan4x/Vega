# DevOps runbook

This document covers how to run the Trader stack locally, what CI does on every pull request, and where the build pipeline lives. Subsequent phases will extend it with Docker, Postgres, and production deployment to Cloudflare Pages plus Render plus Neon.

## Tooling required on the developer machine

| Tool | Purpose | Recommended version |
|---|---|---|
| `git` | VCS | 2.40 or newer |
| `uv` | Python package manager for the backend | 0.11 or newer |
| Python | Backend runtime | 3.12 (managed by uv) |
| Node.js | Frontend toolchain | 22 LTS |
| `pnpm` | Frontend package manager | 10 (install via `corepack enable`) |
| `pre-commit` | Local hook runner | 4.x (install with `uv tool install pre-commit`) |

If `pnpm` is missing, run `corepack enable --install-directory ~/.local/bin` and add `~/.local/bin` to your `PATH`.

## Repository layout (Phase 0 baseline)

```
/home/mustafa/src/trader/
  backend/            FastAPI service (uv project)
    app/              Application package (main.py with /health endpoint)
    tests/            Pytest tests
    pyproject.toml    Project metadata, dev tools (ruff, mypy, pytest, httpx)
  frontend/           Vite plus React plus TypeScript app
    src/
      App.tsx
      main.tsx
      index.css       Imports Tailwind, then tokens.css
      styles/
        tokens.css    Oxblood design tokens (CSS custom properties)
      test/
        setup.ts      Vitest setup (jest-dom matchers)
        App.test.tsx  Smoke test
    tailwind.config.ts  Theme.extend block from the design manifest
    vite.config.ts    Vite plus Tailwind plus Vitest config
  docs/
    design/claude-design-output.html  Visual ground truth
    devops.md         This file
  .github/workflows/ci.yml  Pull request gate
  .pre-commit-config.yaml   Local hook config
  .gitignore                Python, Node, OS, secrets
```

## Backend, day to day

```bash
cd backend

# First time setup, or whenever pyproject.toml changes
uv sync

# Run the dev server with auto reload
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Visit the health endpoint
curl http://127.0.0.1:8000/health
# => {"status":"ok"}

# Lint, type check, test
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

The backend uses the Hatchling build backend with the package living under `backend/app/`. Add new runtime deps with `uv add <name>` and dev deps with `uv add --dev <name>`.

## Frontend, day to day

```bash
cd frontend

# First time setup, or whenever package.json changes
pnpm install

# Vite dev server with hot module reload
pnpm dev

# Production build (TypeScript build then Vite build)
pnpm build

# Lint, type check, test
pnpm lint
pnpm tsc
pnpm test --run
```

The Tailwind tokens resolve to CSS variables defined in `src/styles/tokens.css`. Both files are kept in sync with `docs/design/claude-design-output.html`. When a token changes, edit all three.

## Pre commit hooks

Hooks are managed by the `pre-commit` framework. Configuration lives in `/home/mustafa/src/trader/.pre-commit-config.yaml` and includes:

* `ruff` (Python lint plus format) on `backend/`.
* `prettier` on frontend source files.
* Local `eslint` invocation on frontend source files.
* `gitleaks` for secret scanning across the whole tree.
* Standard `pre-commit-hooks` (trailing whitespace, end of file, large file guard, merge conflict markers, private key detection).

Install once with:

```bash
pre-commit install
```

Run on demand with `pre-commit run --all-files`.

## Continuous integration

The workflow at `.github/workflows/ci.yml` runs on every pull request and on every push to `main`. It has three jobs:

1. **Backend**: `uv sync --frozen`, `ruff check`, `ruff format --check`, `mypy app`, `pytest`.
2. **Frontend**: `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm tsc`, `pnpm test --run`, `pnpm build`.
3. **Secrets scan**: `gitleaks` against the full history.

The pnpm store is cached on `pnpm-lock.yaml`; uv's cache is enabled via `astral-sh/setup-uv@v7`. With warm caches, the typical PR completes in well under five minutes.

## Adding a new dependency

Backend:

```bash
cd backend
uv add <package>            # runtime
uv add --dev <package>      # dev only
```

Frontend:

```bash
cd frontend
pnpm add <package>
pnpm add -D <package>       # dev only
```

Both write a lock file (`uv.lock` and `pnpm-lock.yaml`) that must be committed.

## Deployment (placeholder for Phase 11)

Cloudflare Pages for the frontend, Render for the backend, Neon for Postgres. The detailed deployment steps land in `/home/mustafa/src/trader/docs/setup-guide.md` and `render.yaml` during Phase 11. For now this section is a stub.

## Troubleshooting

* **`pnpm: command not found`**: run `corepack enable --install-directory ~/.local/bin` and ensure `~/.local/bin` is on `PATH`.
* **`uv: command not found`**: install per `https://docs.astral.sh/uv/getting-started/installation/`.
* **`pre-commit` reports an unknown hook id after editing the config**: run `pre-commit clean` then `pre-commit install --install-hooks`.
* **Vitest fails to find `expect.toBeInTheDocument`**: confirm `src/test/setup.ts` imports `@testing-library/jest-dom/vitest` and that `vite.config.ts` lists it in `test.setupFiles`.
