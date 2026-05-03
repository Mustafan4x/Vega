"""Database engine and session factory.

DSN comes from ``TRADER_DATABASE_URL`` (default: a local SQLite file
under ``backend/var/trader.db`` for dev).  Production uses Postgres on
Neon (set in the Render service env in Phase 11). Never commit a
production DSN; the ``gitleaks`` rule from Phase 0 catches them.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def _default_sqlite_url() -> str:
    backend_root = Path(__file__).resolve().parent.parent.parent
    var_dir = backend_root / "var"
    var_dir.mkdir(exist_ok=True)
    return f"sqlite:///{var_dir / 'trader.db'}"


_engine: Engine | None = None
_SessionFactory: sessionmaker[Session] | None = None


def _build_engine(url: str) -> Engine:
    connect_args: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True, future=True)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = os.environ.get("TRADER_DATABASE_URL", _default_sqlite_url())
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
    target_url = (
        url if url is not None else os.environ.get("TRADER_DATABASE_URL", _default_sqlite_url())
    )
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
