"""Shared pytest fixtures for the FastAPI service.

Each test gets a fresh TestClient bound to a freshly built app and a
fresh in memory SQLite database. The shared connection pool keeps the
schema visible across the request lifecycle so persistence tests can
write in one request and read back in the next.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
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


@pytest.fixture(scope="session")
def rsa_keypair() -> dict[str, object]:
    """One RSA keypair shared across the test session.

    Returned dict: ``private_pem``, ``jwk`` (public, with kid='test-key-1'),
    ``kid``.
    """
    import base64

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_numbers = key.public_key().public_numbers()
    n = public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big")
    e = public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big")

    def b64u(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "kid": "test-key-1",
        "n": b64u(n),
        "e": b64u(e),
    }
    return {"private_pem": private_pem, "jwk": jwk, "kid": "test-key-1"}


@pytest.fixture(autouse=True)
def _patched_jwks(monkeypatch: pytest.MonkeyPatch, rsa_keypair: dict[str, object]) -> None:
    """Make every test see our test JWK as the cached JWKS."""
    monkeypatch.setenv("VEGA_AUTH0_DOMAIN", "vega-test.us.auth0.com")
    monkeypatch.setenv("VEGA_AUTH0_AUDIENCE", "vega-api")
    from app.core import auth as auth_module

    auth_module._jwks_cache.set([rsa_keypair["jwk"]])  # type: ignore[index]


@pytest.fixture
def auth_token(rsa_keypair: dict[str, object]) -> Callable[..., str]:
    """Build a signed JWT for tests."""

    def _make(
        sub: str = "google-oauth2|test-user-a",
        aud: str = "vega-api",
        iss: str = "https://vega-test.us.auth0.com/",
        exp_offset_seconds: int = 300,
        kid: str | None = None,
    ) -> str:
        now = int(time.time())
        payload = {
            "sub": sub,
            "aud": aud,
            "iss": iss,
            "iat": now,
            "nbf": now,
            "exp": now + exp_offset_seconds,
        }
        headers = {"kid": kid or rsa_keypair["kid"], "alg": "RS256"}
        return jwt.encode(  # type: ignore[arg-type]
            payload, rsa_keypair["private_pem"], algorithm="RS256", headers=headers
        )

    return _make


@pytest.fixture
def auth_headers(auth_token: Callable[..., str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token()}"}
