# Trader backend production image.
#
# Multi stage so the final image has only Python plus the resolved
# wheels. uv is used at build time only; the runtime stage runs the
# console script directly via the project's virtualenv. Built and
# pushed by Render's docker runtime; see /render.yaml at the repo
# root.

FROM python:3.12-slim AS builder

# uv pinned to a known working version so the build is reproducible.
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Resolve and install dependencies first so the wheel cache is reused
# when only application code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Now install the project itself into the same venv.
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    HOST=0.0.0.0 \
    PORT=8000 \
    FORWARDED_ALLOW_IPS=*

# Run as a non root user. Render's runtime does not require root, and
# dropping privileges shrinks the blast radius of a remote code
# execution bug. The app does not write to disk inside the container
# (logs are stdout, sqlite is dev only), so a read only root is fine.
RUN useradd --create-home --uid 10001 trader

WORKDIR /app

COPY --from=builder --chown=trader:trader /app /app

USER trader

EXPOSE 8000

# trader-serve is the project's pyproject script entry; it pins the
# uvicorn flags this service needs (server_header=False, proxy_headers=True).
CMD ["trader-serve"]
