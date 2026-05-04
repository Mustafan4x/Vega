"""Unit tests for :func:`app.db.session.normalize_database_url`.

Phase 11 production deploy hit a 500 because Neon's "Connect manually"
string starts with bare ``postgresql://`` and SQLAlchemy 2.x routes
that to ``psycopg2`` (not installed). The normalizer rewrites the
prefix so a verbatim Neon paste boots correctly. These tests pin the
behavior so a future SQLAlchemy default change does not silently
revive the bug.
"""

from __future__ import annotations

import pytest

from app.db.session import normalize_database_url


@pytest.mark.parametrize(
    "given,expected",
    [
        # Bare postgresql:// gets rewritten.
        (
            "postgresql://user:pw@host/db?sslmode=require",
            "postgresql+psycopg://user:pw@host/db?sslmode=require",
        ),
        # Already-explicit postgresql+psycopg passes through.
        (
            "postgresql+psycopg://user:pw@host/db",
            "postgresql+psycopg://user:pw@host/db",
        ),
        # Explicit psycopg2 (legacy) is left alone; the user opted in.
        (
            "postgresql+psycopg2://user:pw@host/db",
            "postgresql+psycopg2://user:pw@host/db",
        ),
        # Non Postgres URLs pass through.
        ("sqlite:///./var/vega.db", "sqlite:///./var/vega.db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_normalize_database_url(given: str, expected: str) -> None:
    assert normalize_database_url(given) == expected


def test_get_engine_does_not_touch_default_when_env_is_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: the dev SQLite default helper does a mkdir on the
    project tree. ``os.environ.get(KEY, default)`` evaluates the default
    eagerly, so an unguarded call would still mkdir even when
    ``VEGA_DATABASE_URL`` is set. The production container runs as a
    non root user with no write access to the WORKDIR, so the mkdir
    raises PermissionError there. This test pins the lazy fallback so
    that bug cannot regress.
    """

    from app.db import session

    sentinel = {"called": False}

    def fail() -> str:
        sentinel["called"] = True
        raise AssertionError("_default_sqlite_url should not be called when env is set")

    monkeypatch.setattr(session, "_default_sqlite_url", fail)
    monkeypatch.setattr(session, "_engine", None, raising=False)
    monkeypatch.setenv("VEGA_DATABASE_URL", "sqlite://")

    session.get_engine()

    assert sentinel["called"] is False


def test_legacy_trader_database_url_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """The legacy ``TRADER_DATABASE_URL`` fallback was removed after the
    project rename. Only ``VEGA_DATABASE_URL`` is read; setting
    ``TRADER_DATABASE_URL`` has no effect."""

    from app.db import session

    monkeypatch.setattr(session, "_engine", None, raising=False)
    monkeypatch.delenv("VEGA_DATABASE_URL", raising=False)
    monkeypatch.setenv("TRADER_DATABASE_URL", "sqlite:///should-be-ignored.db")

    engine = session.get_engine()
    # Falls back to the dev SQLite default (vega.db) under backend/var,
    # not the TRADER_DATABASE_URL value above.
    assert "should-be-ignored" not in str(engine.url)
    assert "vega.db" in str(engine.url)
