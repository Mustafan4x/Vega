"""Alembic environment.

Reads the database URL from ``VEGA_DATABASE_URL`` (the same env var
the FastAPI service reads in :mod:`app.db.session`) so a single source
of truth governs both the running app and the migration runner.
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import read_env
from app.db.models import Base
from app.db.session import normalize_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

env_url = read_env("DATABASE_URL")
if env_url:
    config.set_main_option("sqlalchemy.url", normalize_database_url(env_url))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
