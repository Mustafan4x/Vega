"""Database engine and session factory.

DSN comes from ``VEGA_DATABASE_URL`` (default: a local SQLite file
under ``backend/var/vega.db`` for dev). The legacy ``TRADER_DATABASE_URL``
name is still honored as a fallback during the project rename
rollover. Production uses Postgres on Neon (set in the Render service
env in Phase 11). Never commit a production DSN; the ``gitleaks``
rule from Phase 0 catches them.

DSN normalization: bare ``postgresql://`` URLs (the form Neon's
dashboard hands you) make SQLAlchemy 2.x try the ``psycopg2`` driver,
which the project does not ship; only ``psycopg`` (v3) is installed.
:func:`normalize_database_url` rewrites those URLs to the explicit
``postgresql+psycopg://`` form before the engine is built so a
verbatim paste from Neon does not crash production at first DB
touch. Alembic shares the same helper via :mod:`alembic.env`.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import read_env


def _default_sqlite_url() -> str:
    backend_root = Path(__file__).resolve().parent.parent.parent
    var_dir = backend_root / "var"
    var_dir.mkdir(exist_ok=True)
    return f"sqlite:///{var_dir / 'vega.db'}"


def normalize_database_url(url: str) -> str:
    """Rewrite a bare ``postgresql://`` DSN to ``postgresql+psycopg://``.

    The Neon dashboard's "Connect manually" string starts with
    ``postgresql://`` which SQLAlchemy 2.x routes to ``psycopg2``. We
    ship ``psycopg`` (v3), so an unmodified Neon DSN crashes at
    engine creation with ``ModuleNotFoundError: No module named
    'psycopg2'``. Rewriting here keeps the env var copy-paste
    friendly. URLs that already specify a driver, or that are not
    Postgres at all (sqlite, etc.) pass through unchanged.
    """

    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def _build_engine(url: str) -> Engine:
    url = normalize_database_url(url)
    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True, future=True)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        # Lazy evaluation: a default that does a mkdir under the
        # project tree would crash inside the production container
        # (non root user, read only WORKDIR) every time the DSN env
        # var is set. Compute the SQLite fallback only if the env var
        # is missing or empty. ``read_env`` checks VEGA_DATABASE_URL
        # first and falls back to the legacy TRADER_DATABASE_URL.
        url = read_env("DATABASE_URL") or _default_sqlite_url()
        _engine = _build_engine(url)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionFactory
    if _SessionFactory is None:
        _SessionFactory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionFactory


def reset_engine_for_tests(url: str | None = None) -> Engine:
    """Drop the cached engine + session factory and rebuild from ``url``.

    Used by the pytest fixture to swap in an in memory SQLite database
    so tests do not touch the dev or production database.
    """
    global _engine, _SessionFactory
    if url is not None:
        target_url = url
    else:
        # Same lazy evaluation reasoning as get_engine: do not call
        # _default_sqlite_url unless we genuinely need it.
        target_url = read_env("DATABASE_URL") or _default_sqlite_url()
    _engine = _build_engine(target_url)
    _SessionFactory = sessionmaker(bind=_engine, expire_on_commit=False, future=True)
    return _engine


def get_session() -> Iterator[Session]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
