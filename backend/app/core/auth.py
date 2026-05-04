"""JWT bearer authentication via Auth0 JWKS verification.

The FastAPI dependency :func:`require_user` reads the
``Authorization: Bearer <jwt>`` header, verifies the JWT against the
keys published at the configured Auth0 tenant's JWKS endpoint, and
returns the ``sub`` claim. Any failure raises ``HTTPException(401)``
with a generic message that never echoes which check failed.
"""

from __future__ import annotations

import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any

import jwt
from fastapi import HTTPException, Request, status
from jwt.algorithms import RSAAlgorithm

from app.core.config import load_settings

_JWKS_TTL_SECONDS = 24 * 60 * 60


@dataclass
class _JWKSCache:
    keys: list[dict[str, Any]] = field(default_factory=list)
    fetched_at: float = 0.0

    def set(self, keys: list[dict[str, Any]]) -> None:
        self.keys = list(keys)
        self.fetched_at = time.time()

    def is_fresh(self) -> bool:
        return bool(self.keys) and (time.time() - self.fetched_at) < _JWKS_TTL_SECONDS

    def find(self, kid: str) -> dict[str, Any] | None:
        for k in self.keys:
            if k.get("kid") == kid:
                return k
        return None

    def clear(self) -> None:
        self.keys = []
        self.fetched_at = 0.0


_jwks_cache = _JWKSCache()


def _fetch_jwks(domain: str) -> list[dict[str, Any]]:
    url = f"https://{domain}/.well-known/jwks.json"
    with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310  # nosec B310
        import json

        body = json.loads(resp.read().decode())
    return list(body.get("keys", []))


def _ensure_jwks(domain: str) -> None:
    if _jwks_cache.is_fresh():
        return
    _jwks_cache.set(_fetch_jwks(domain))


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
    )


def _verify(token: str, domain: str, audience: str) -> str:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc

    if unverified_header.get("alg") != "RS256":
        raise _unauthorized()

    kid = unverified_header.get("kid")
    if not kid:
        raise _unauthorized()

    _ensure_jwks(domain)
    jwk = _jwks_cache.find(kid)
    if jwk is None:
        _jwks_cache.clear()
        try:
            _ensure_jwks(domain)
        except Exception as exc:  # noqa: BLE001
            raise _unauthorized() from exc
        jwk = _jwks_cache.find(kid)
    if jwk is None:
        raise _unauthorized()

    public_key = RSAAlgorithm.from_jwk(jwk)

    try:
        payload = jwt.decode(
            token,
            public_key,  # type: ignore[arg-type]
            algorithms=["RS256"],
            audience=audience,
            issuer=f"https://{domain}/",
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise _unauthorized()
    return sub


def require_user(request: Request) -> str:
    """FastAPI dependency. Returns the JWT ``sub`` claim or raises 401."""

    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header:
        raise _unauthorized()

    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise _unauthorized()

    token = parts[1].strip()

    settings = load_settings()
    if not settings.auth0_domain or not settings.auth0_audience:
        raise _unauthorized()

    return _verify(token, settings.auth0_domain, settings.auth0_audience)
