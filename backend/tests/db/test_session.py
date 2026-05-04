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
        ("sqlite:///./var/trader.db", "sqlite:///./var/trader.db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_normalize_database_url(given: str, expected: str) -> None:
    assert normalize_database_url(given) == expected
