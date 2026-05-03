"""Shared pytest fixtures for the FastAPI service.

Each test gets a fresh TestClient bound to a freshly built app and a
fresh in memory SQLite database. The shared connection pool keeps the
schema visible across the request lifecycle so persistence tests can
write in one request and read back in the next.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.db import session as db_session


@pytest.fixture(autouse=True)
def _isolated_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Bind the app's session factory to a fresh in memory SQLite for the test.

    The StaticPool shares a single connection across the engine, so the
    schema lives across requests within one test, but evaporates between
    tests (each test rebinds).
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    monkeypatch.setattr(db_session, "_engine", engine, raising=False)
    monkeypatch.setattr(db_session, "_SessionFactory", factory, raising=False)
    yield
    engine.dispose()


@pytest.fixture
def client() -> Iterator[TestClient]:
    from app.main import build_app

    app = build_app()
    with TestClient(app) as c:
        yield c
