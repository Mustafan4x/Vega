# Phase 12: Authentication and per user history. Implementation plan.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Auth0-backed Google/GitHub OAuth so each visitor gets a private, per user history of saved heat map calculations. Pricer, Greeks, heatmap, model compare, and backtest stay public.

**Architecture:** Backend gains an `app.core.auth.require_user` FastAPI dependency that verifies an `Authorization: Bearer <jwt>` against Auth0's JWKS (RS256, audience `vega-api`, issuer `https://<tenant>.auth0.com/`) and returns the JWT's `sub` claim. Database adds `user_id VARCHAR(64) NOT NULL` to `calculation_inputs` plus a composite `(user_id, created_at DESC)` index. Existing rows are dropped. Frontend wraps the app in `<Auth0Provider>` from `@auth0/auth0-react`, routes the three `/api/calculations*` calls through an `authedFetch` wrapper, and uses the SDK's `appState` to replay a pending save after the post-login redirect. Logged-out UX is friendly: Save and History stay visible; clicking either triggers `loginWithRedirect`.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, Alembic, `pyjwt[crypto]` (new), pytest. React 19, Vite 8, `@auth0/auth0-react` (new), Vitest, Testing Library.

**Source spec:** `docs/superpowers/specs/2026-05-04-auth-and-per-user-history-design.md`.

**Branch:** `phase-12-auth-design` (already created and contains the spec commit). All tasks below land on this branch. Single PR at the end.

**Natural pause point:** after Task 10 (backend complete, all backend tests green, commit clean). The deployed API at this checkpoint returns 401 on `/api/calculations*` because the frontend cannot yet send tokens; this is acceptable because no merge to `main` happens until the full Phase 12 PR lands. Resume continues frontend work on the same branch.

---

## File structure

### Backend (create or modify)

| Path | Status | Responsibility |
|---|---|---|
| `backend/pyproject.toml` | modify | Add `pyjwt[crypto]>=2.10` dependency. |
| `backend/app/core/auth.py` | create | `JWKSCache`, `verify_jwt`, `require_user` dependency. |
| `backend/app/core/config.py` | modify | Add `auth0_domain`, `auth0_audience` to `Settings`; production fail loud. |
| `backend/app/db/models.py` | modify | Add `user_id` column to `CalculationInput`. |
| `backend/alembic/versions/<rev>_phase12_user_id.py` | create | Drop existing rows, add `user_id NOT NULL`, add composite index. |
| `backend/app/api/calculations.py` | modify | Inject `require_user` dependency on all three endpoints; filter by `user_id`; IDOR returns 404. |
| `backend/tests/conftest.py` | modify | Add `rsa_keypair`, `auth_token`, `auth_headers` fixtures; monkey-patch JWKS loader. |
| `backend/tests/api/test_auth.py` | create | Auth dependency contract tests (happy path plus 7 failure modes). |
| `backend/tests/api/test_calculations.py` | modify | Add `auth_headers` to existing tests; add isolation tests. |
| `backend/tests/db/test_models.py` | modify | Confirm `user_id` is `NOT NULL` and indexed. |

### Frontend (create or modify)

| Path | Status | Responsibility |
|---|---|---|
| `frontend/package.json` | modify | Add `@auth0/auth0-react>=2.5.0`. |
| `frontend/src/main.tsx` | modify | Wrap `<App/>` in `<Auth0Provider>`; Vite env var fail loud. |
| `frontend/src/lib/api.ts` | modify | Add `authedFetch` wrapper; route `saveCalculation`, `fetchCalculations`, `fetchCalculation` through it. |
| `frontend/src/components/LayoutShell.tsx` | modify | Add sidebar footer block: Sign-in button or user button. |
| `frontend/src/components/AuthButtons.tsx` | create | `<SignInButton/>`, `<UserButton/>` components used by LayoutShell and HistoryScreen empty state. |
| `frontend/src/screens/HistoryScreen.tsx` | modify | Branch on `isAuthenticated`; logged-out empty state. |
| `frontend/src/screens/HeatMapScreen.tsx` | modify | `onSave` branches on `isAuthenticated`; logged-out triggers login with `appState.pendingSave`. |
| `frontend/src/lib/auth-callback.tsx` | create | Process Auth0 redirect; replay `appState.pendingSave` once. |
| `frontend/src/App.tsx` | modify | Render AuthCallback at `/callback`. |
| `frontend/src/test/auth0-mock.ts` | create | Centralized `useAuth0` mock helper for tests. |
| `frontend/src/screens/HistoryScreen.test.tsx` | modify | Logged-in / logged-out branches. |
| `frontend/src/screens/HeatMapScreen.test.tsx` | create | onSave branches. (No existing test file for this screen.) |
| `frontend/src/lib/auth-callback.test.tsx` | create | Replay path test. |
| `frontend/src/components/LayoutShell.test.tsx` | modify | Sidebar footer renders correctly per auth state. |

### IaC and docs

| Path | Status | Responsibility |
|---|---|---|
| `frontend/public/_headers` | modify | CSP `connect-src` and `frame-src` add `https://*.auth0.com`. |
| `docs/security/threat-model.md` | modify | Add STRIDE addendum for the auth surface. |
| `docs/setup-guide.md` | modify | Add "Auth0 setup" section. |
| `render.yaml` | modify | Declare `VEGA_AUTH0_DOMAIN`, `VEGA_AUTH0_AUDIENCE`. |
| `STATUS.md` | modify | Add Phase 12 row; flip status `in progress` at start, `completed` at end. |
| `frontend/.env.example` | create | Document `VITE_AUTH0_*` vars. |

---

## Task 0: Open the phase

**Files:**
- Modify: `STATUS.md`

- [ ] **Step 1: Confirm the working branch**

Run: `git branch --show-current`
Expected: `phase-12-auth-design`

If not on that branch: `git checkout phase-12-auth-design`.

- [ ] **Step 2: Add Phase 12 row to `STATUS.md`**

Open `STATUS.md`. In the "Phase status table" append a new row after Phase 11:

```
| 12 | Authentication and per user history | in progress | | ~1 full window | Auth0 + Google/GitHub OAuth, write-gate auth perimeter, drop existing rows; spec at docs/superpowers/specs/2026-05-04-auth-and-per-user-history-design.md |
```

In the "Next phase" section, replace the current text with:

```
**Phase 12: Authentication and per user history.** Auth0 + Google/GitHub OAuth via `@auth0/auth0-react`, JWT bearer + JWKS verification on FastAPI side, `user_id NOT NULL` on `calculation_inputs`. Existing rows are dropped at migration. Window cost: ~1 full window. Pause point if needed: after backend tests pass.
```

Update the "Last updated" line to `2026-05-04 (Phase 12 in progress)`.

- [ ] **Step 3: Commit**

```bash
git add STATUS.md
git commit -m "Phase 12 open: STATUS.md row, in-progress flag"
```

---

## Task 1: Add `pyjwt[crypto]` dependency

**Files:**
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Edit `pyproject.toml`**

In the `dependencies` array, add `"pyjwt[crypto]>=2.10"` after `"psycopg[binary]>=3.3.4"`:

```toml
dependencies = [
    "alembic>=1.18.4",
    "fastapi>=0.136.1",
    "numpy>=2.4.4",
    "psycopg[binary]>=3.3.4",
    "pydantic>=2.13.3",
    "pyjwt[crypto]>=2.10",
    "slowapi>=0.1.9",
    "sqlalchemy>=2.0",
    "uvicorn[standard]>=0.46.0",
    "yfinance>=1.3.0",
]
```

- [ ] **Step 2: Resolve and lock**

Run: `uv --project backend sync`
Expected: `pyjwt`, `cryptography` installed; lockfile updated.

- [ ] **Step 3: Smoke import**

Run: `uv --project backend run python -c "import jwt; print(jwt.__version__)"`
Expected: prints a version >= 2.10.

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock
git commit -m "Phase 12: add pyjwt[crypto] dependency"
```

---

## Task 2: Backend `Settings` carries `auth0_domain` and `auth0_audience`

**Files:**
- Modify: `backend/app/core/config.py`
- Test: `backend/tests/api/test_environment.py`

- [ ] **Step 1: Write failing tests**

Open `backend/tests/api/test_environment.py`. Add at the bottom:

```python
def test_settings_loads_auth0_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEGA_AUTH0_DOMAIN", "vega-test.us.auth0.com")
    monkeypatch.setenv("VEGA_AUTH0_AUDIENCE", "vega-api")
    from app.core.config import load_settings

    settings = load_settings()
    assert settings.auth0_domain == "vega-test.us.auth0.com"
    assert settings.auth0_audience == "vega-api"


def test_settings_auth0_optional_in_development(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VEGA_AUTH0_DOMAIN", raising=False)
    monkeypatch.delenv("VEGA_AUTH0_AUDIENCE", raising=False)
    monkeypatch.setenv("VEGA_ENVIRONMENT", "development")
    from app.core.config import load_settings

    settings = load_settings()
    assert settings.auth0_domain == ""
    assert settings.auth0_audience == ""


def test_settings_auth0_required_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VEGA_ENVIRONMENT", "production")
    monkeypatch.setenv("VEGA_CORS_ORIGINS", "https://vega-2rd.pages.dev")
    monkeypatch.delenv("VEGA_AUTH0_DOMAIN", raising=False)
    monkeypatch.delenv("VEGA_AUTH0_AUDIENCE", raising=False)
    from app.core.config import ConfigError, load_settings

    with pytest.raises(ConfigError, match="VEGA_AUTH0_DOMAIN"):
        load_settings()
```

- [ ] **Step 2: Run tests, expect failure**

Run: `uv --project backend run pytest tests/api/test_environment.py -k auth0 -v`
Expected: FAIL with `AttributeError: 'Settings' object has no attribute 'auth0_domain'` or similar.

- [ ] **Step 3: Implement**

Open `backend/app/core/config.py`. Modify the `Settings` dataclass to add two fields:

```python
@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    rate_limit_default: str
    max_body_bytes: int
    log_level: str
    environment: str
    auth0_domain: str
    auth0_audience: str

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
```

In `load_settings`, before the `if settings.is_production:` block, add:

```python
    auth0_domain = (read_env("AUTH0_DOMAIN", "") or "").strip()
    auth0_audience = (read_env("AUTH0_AUDIENCE", "") or "").strip()

    settings = Settings(
        cors_origins=origins,
        rate_limit_default=rate_limit,
        max_body_bytes=max_body,
        log_level=log_level,
        environment=environment,
        auth0_domain=auth0_domain,
        auth0_audience=auth0_audience,
    )
```

(Replace the existing `Settings(...)` constructor call with the one above; do not duplicate.)

In `_validate_production`, add at the end:

```python
    if not settings.auth0_domain:
        raise ConfigError(
            "VEGA_AUTH0_DOMAIN must be set in production. "
            "See docs/setup-guide.md (Auth0 setup)."
        )
    if not settings.auth0_audience:
        raise ConfigError(
            "VEGA_AUTH0_AUDIENCE must be set in production. "
            "See docs/setup-guide.md (Auth0 setup)."
        )
```

- [ ] **Step 4: Run tests, expect pass**

Run: `uv --project backend run pytest tests/api/test_environment.py -k auth0 -v`
Expected: 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/tests/api/test_environment.py
git commit -m "Phase 12 backend: Auth0 settings (domain, audience) with prod fail-loud"
```

---

## Task 3: Backend `app.core.auth` module — JWKS cache + JWT verifier

**Files:**
- Create: `backend/app/core/auth.py`
- Test: `backend/tests/api/test_auth.py`
- Modify: `backend/tests/conftest.py` (add `rsa_keypair`, `auth_token`, `auth_headers` fixtures)

- [ ] **Step 1: Add fixtures to `conftest.py`**

Append to `backend/tests/conftest.py`:

```python
import json
import time
from typing import Callable

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


@pytest.fixture(scope="session")
def rsa_keypair() -> dict[str, object]:
    """One RSA keypair shared across the test session.

    Returned dict: ``private_pem``, ``jwk`` (public, with kid='test-key-1'),
    ``kid``.
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_numbers = key.public_key().public_numbers()
    n = public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big")
    e = public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big")
    import base64

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
    """Make every test see our test JWK as the cached JWKS.

    Sets a fake Auth0 domain and audience so verify_jwt's iss/aud checks
    pass and patches the cached fetcher.
    """
    monkeypatch.setenv("VEGA_AUTH0_DOMAIN", "vega-test.us.auth0.com")
    monkeypatch.setenv("VEGA_AUTH0_AUDIENCE", "vega-api")
    from app.core import auth as auth_module

    auth_module._jwks_cache.set([rsa_keypair["jwk"]])  # type: ignore[index]


@pytest.fixture
def auth_token(rsa_keypair: dict[str, object]) -> Callable[..., str]:
    """Build a signed JWT for tests.

    Defaults: sub=user_a_sub, valid for 5 minutes, audience and issuer
    matching the test fixture environment.
    """

    def _make(
        sub: str = "google-oauth2|test-user-a",
        aud: str = "vega-api",
        iss: str = "https://vega-test.us.auth0.com/",
        exp_offset_seconds: int = 300,
        kid: str | None = None,
    ) -> str:
        now = int(time.time())
        payload = {"sub": sub, "aud": aud, "iss": iss, "iat": now, "nbf": now, "exp": now + exp_offset_seconds}
        headers = {"kid": kid or rsa_keypair["kid"], "alg": "RS256"}
        return jwt.encode(payload, rsa_keypair["private_pem"], algorithm="RS256", headers=headers)  # type: ignore[arg-type]

    return _make


@pytest.fixture
def auth_headers(auth_token: Callable[..., str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token()}"}
```

- [ ] **Step 2: Write failing tests for `app.core.auth`**

Create `backend/tests/api/test_auth.py`:

```python
"""Contract tests for the JWT auth dependency.

Builds tokens with a per-session test RSA key (see conftest.py) and
asserts the FastAPI ``require_user`` dependency accepts valid tokens
and rejects every documented failure mode with a generic 401 that does
not echo error details.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient


def test_require_user_accepts_valid_jwt(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/api/calculations", headers=auth_headers)
    assert response.status_code == 200, response.text


def test_require_user_rejects_missing_header(client: TestClient) -> None:
    response = client.get("/api/calculations")
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_require_user_rejects_malformed_header(client: TestClient) -> None:
    response = client.get("/api/calculations", headers={"Authorization": "Token abc"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_require_user_rejects_expired_jwt(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(exp_offset_seconds=-60)
    response = client.get(
        "/api/calculations", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_require_user_rejects_wrong_audience(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(aud="wrong-audience")
    response = client.get(
        "/api/calculations", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_require_user_rejects_wrong_issuer(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(iss="https://attacker.example.com/")
    response = client.get(
        "/api/calculations", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_require_user_rejects_unknown_kid(
    client: TestClient, auth_token: Callable[..., str]
) -> None:
    token = auth_token(kid="not-a-real-kid")
    response = client.get(
        "/api/calculations", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_require_user_rejects_alg_none(client: TestClient) -> None:
    # An attacker tries to set alg=none and unsigned payload.
    import base64
    import json as _json

    header = base64.urlsafe_b64encode(_json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(
        b"="
    )
    payload = base64.urlsafe_b64encode(
        _json.dumps(
            {
                "sub": "x",
                "aud": "vega-api",
                "iss": "https://vega-test.us.auth0.com/",
                "exp": 9999999999,
            }
        ).encode()
    ).rstrip(b"=")
    token = f"{header.decode()}.{payload.decode()}."

    response = client.get(
        "/api/calculations", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_require_user_does_not_leak_error_detail(client: TestClient) -> None:
    response = client.get(
        "/api/calculations", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert response.status_code == 401
    body = response.json()
    assert body == {"detail": "Authentication required."}
    assert "exp" not in str(body)
    assert "signature" not in str(body).lower()
```

- [ ] **Step 3: Run tests, expect failure**

Run: `uv --project backend run pytest tests/api/test_auth.py -v`
Expected: FAIL — module `app.core.auth` does not exist.

- [ ] **Step 4: Implement `app.core.auth`**

Create `backend/app/core/auth.py`:

```python
"""JWT bearer authentication via Auth0 JWKS verification.

The FastAPI dependency :func:`require_user` reads the
``Authorization: Bearer <jwt>`` header, verifies the JWT against the
keys published at the configured Auth0 tenant's JWKS endpoint, and
returns the ``sub`` claim. Any failure raises ``HTTPException(401)``
with a generic message that never echoes which check failed.

The JWKS is fetched lazily on the first call and cached for 24 hours.
On a key miss (token uses an unknown ``kid``) the cache is invalidated
once and refetched before failing the request.
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
    with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 - fixed scheme
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
        # Key rotated; refetch once before giving up.
        _jwks_cache.clear()
        try:
            _ensure_jwks(domain)
        except Exception as exc:  # noqa: BLE001 - any fetch failure -> 401
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
        # Misconfigured server: in production this is impossible (fail
        # loud at boot); in development, refusing the request is the
        # safest behavior.
        raise _unauthorized()

    return _verify(token, settings.auth0_domain, settings.auth0_audience)
```

- [ ] **Step 5: Wire the dependency into one endpoint as a smoke test**

Open `backend/app/api/calculations.py`. Add to the imports near the top:

```python
from app.core.auth import require_user
```

Modify `list_calculations` (the GET `/api/calculations` handler) to add the dependency without changing return shape yet:

```python
@router.get("/calculations", response_model=CalculationListResponse)
@limiter.limit(CALCULATIONS_READ_RATE_LIMIT)
def list_calculations(
    request: Request,
    limit: int = Query(LIST_LIMIT_DEFAULT, ge=1, le=LIST_LIMIT_MAX, description="Page size."),
    offset: int = Query(0, ge=0, le=10_000, description="Number of items to skip."),
    user_id: str = Depends(require_user),
    session: Session = Depends(get_session),
) -> CalculationListResponse:
```

Leave the body of `list_calculations` unchanged for now — Task 8 does the filter. This lets the auth tests run end-to-end against a real route. (`user_id` is intentionally unused at this point; Task 8 wires it in.)

- [ ] **Step 6: Run auth tests, expect pass**

Run: `uv --project backend run pytest tests/api/test_auth.py -v`
Expected: 9 tests pass.

- [ ] **Step 7: Run full backend suite, expect existing list tests to fail authoritatively**

Run: `uv --project backend run pytest -q`
Expected: tests in `test_calculations.py` that hit `GET /api/calculations` without an `Authorization` header now return 401 → those tests will fail. That's intentional and gets fixed in Task 7. The auth tests (9) pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/auth.py backend/app/api/calculations.py backend/tests/conftest.py backend/tests/api/test_auth.py
git commit -m "Phase 12 backend: JWT auth dependency with JWKS verification"
```

---

## Task 4: Alembic migration — drop rows, add `user_id`, composite index

**Files:**
- Create: `backend/alembic/versions/<rev>_phase12_user_id.py`

- [ ] **Step 1: Generate a blank revision**

Run:

```bash
cd /home/mustafa/src/vega/backend
uv run alembic revision -m "phase12 user_id and per user index"
```

Expected: a new file under `backend/alembic/versions/`. Note the revision id printed, e.g. `a3f1b2c4d5e6_phase12_user_id_and_per_user_index.py`.

- [ ] **Step 2: Fill in `upgrade()` and `downgrade()`**

Open the new file. Replace `upgrade` and `downgrade` with:

```python
def upgrade() -> None:
    # Phase 12 policy (spec): drop existing rows. The frontend now
    # requires sign in to save, so all future rows have a user_id; we
    # do not backfill the historical anonymous rows.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("TRUNCATE TABLE calculation_outputs, calculation_inputs CASCADE")
    else:
        # SQLite (dev / tests): truncate via DELETE; CASCADE handled by FK.
        op.execute("DELETE FROM calculation_outputs")
        op.execute("DELETE FROM calculation_inputs")

    op.add_column(
        "calculation_inputs",
        sa.Column("user_id", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_calculation_inputs_user_id_created_at",
        "calculation_inputs",
        ["user_id", sa.text("created_at DESC")],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_calculation_inputs_user_id_created_at",
        table_name="calculation_inputs",
    )
    op.drop_column("calculation_inputs", "user_id")
```

Confirm `down_revision` references `9c8f64a81798` (the Phase 6 migration). If Alembic auto-set it, leave it.

- [ ] **Step 3: Apply against a scratch SQLite to confirm the migration runs**

Run:

```bash
cd /home/mustafa/src/vega/backend
VEGA_DATABASE_URL=sqlite:///./scratch.db uv run alembic upgrade head
VEGA_DATABASE_URL=sqlite:///./scratch.db uv run alembic downgrade -1
VEGA_DATABASE_URL=sqlite:///./scratch.db uv run alembic upgrade head
rm scratch.db
```

Expected: each command exits 0. The roundtrip confirms `upgrade` and `downgrade` both work.

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/
git commit -m "Phase 12 migration: drop rows, add user_id NOT NULL, composite index"
```

---

## Task 5: ORM model — `CalculationInput.user_id`

**Files:**
- Modify: `backend/app/db/models.py`
- Test: `backend/tests/db/test_models.py`

- [ ] **Step 1: Write failing test**

Open or create `backend/tests/db/test_models.py`. Add:

```python
from sqlalchemy import inspect

from app.db import CalculationInput


def test_calculation_input_has_user_id_not_null() -> None:
    columns = {c.name: c for c in inspect(CalculationInput).columns}
    assert "user_id" in columns
    assert columns["user_id"].nullable is False
    assert columns["user_id"].type.length == 64  # type: ignore[attr-defined]
```

- [ ] **Step 2: Run, expect failure**

Run: `uv --project backend run pytest tests/db/test_models.py::test_calculation_input_has_user_id_not_null -v`
Expected: FAIL — `user_id` not in columns.

- [ ] **Step 3: Add the column to the model**

Open `backend/app/db/models.py`. In `CalculationInput`, after `cols`, add:

```python
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
```

- [ ] **Step 4: Run, expect pass**

Run: `uv --project backend run pytest tests/db/test_models.py -v`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/db/models.py backend/tests/db/test_models.py
git commit -m "Phase 12 model: CalculationInput.user_id (String(64), NOT NULL)"
```

---

## Task 6: Update `test_calculations.py` to send auth headers on every request

**Files:**
- Modify: `backend/tests/api/test_calculations.py`

- [ ] **Step 1: Replace bare client calls with authed equivalents**

In `backend/tests/api/test_calculations.py`, every test that uses `client` for a `/api/calculations` request needs an `auth_headers` fixture. Update each test signature and call:

Before:
```python
def test_create_calculation_returns_201_with_uuid(client: TestClient) -> None:
    response = client.post("/api/calculations", json=VALID_PAYLOAD)
```

After:
```python
def test_create_calculation_returns_201_with_uuid(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    response = client.post("/api/calculations", json=VALID_PAYLOAD, headers=auth_headers)
```

Apply this change to every test in the file. Use a search-and-edit pass: every `client.post("/api/calculations"`, `client.get("/api/calculations"`, and `client.get(f"/api/calculations/{...}` gains `headers=auth_headers`.

- [ ] **Step 2: Run, expect existing tests to pass under auth**

Run: `uv --project backend run pytest tests/api/test_calculations.py -v`
Expected: every existing test passes (now with bearer tokens). The list and detail responses now also expect `user_id` filtering, but Task 8 has not landed yet, so the data is global; tests still pass because each test starts with a fresh DB.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/api/test_calculations.py
git commit -m "Phase 12 tests: existing /api/calculations tests use auth_headers"
```

---

## Task 7: Add cross-user isolation tests to `test_calculations.py`

**Files:**
- Modify: `backend/tests/api/test_calculations.py`

- [ ] **Step 1: Add isolation tests**

Append to `backend/tests/api/test_calculations.py`:

```python
def test_post_persists_user_id_from_token(
    client: TestClient, auth_token, rsa_keypair
) -> None:
    token_a = auth_token(sub="google-oauth2|user-a")
    response = client.post(
        "/api/calculations",
        json=VALID_PAYLOAD,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 201
    calc_id = response.json()["calculation_id"]

    factory = get_session_factory()
    with factory() as session:
        record = session.get(CalculationInput, calc_id)
        assert record is not None
        assert record.user_id == "google-oauth2|user-a"


def test_list_only_returns_callers_rows(
    client: TestClient, auth_token
) -> None:
    token_a = auth_token(sub="google-oauth2|user-a")
    token_b = auth_token(sub="github|user-b")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    client.post("/api/calculations", json=VALID_PAYLOAD, headers=headers_a)
    client.post("/api/calculations", json=VALID_PAYLOAD, headers=headers_a)
    client.post("/api/calculations", json=VALID_PAYLOAD, headers=headers_b)

    list_a = client.get("/api/calculations", headers=headers_a)
    assert list_a.status_code == 200
    body_a = list_a.json()
    assert body_a["total"] == 2

    list_b = client.get("/api/calculations", headers=headers_b)
    assert list_b.status_code == 200
    body_b = list_b.json()
    assert body_b["total"] == 1


def test_get_others_calculation_returns_404(
    client: TestClient, auth_token
) -> None:
    token_a = auth_token(sub="google-oauth2|user-a")
    token_b = auth_token(sub="github|user-b")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    create = client.post("/api/calculations", json=VALID_PAYLOAD, headers=headers_a)
    calc_id = create.json()["calculation_id"]

    response_b = client.get(f"/api/calculations/{calc_id}", headers=headers_b)
    assert response_b.status_code == 404
    assert response_b.json() == {"detail": "Calculation not found."}


def test_endpoints_reject_unauthenticated_requests(client: TestClient) -> None:
    assert client.post("/api/calculations", json=VALID_PAYLOAD).status_code == 401
    assert client.get("/api/calculations").status_code == 401
    assert client.get(
        "/api/calculations/00000000-0000-0000-0000-000000000000"
    ).status_code == 401
```

- [ ] **Step 2: Run isolation tests, expect failure**

Run: `uv --project backend run pytest tests/api/test_calculations.py -k "user_id or callers_rows or others_calculation or unauthenticated" -v`

Expected: at least 3 of these fail because the endpoints do not yet filter by `user_id` (Task 8) and `POST` does not yet capture the user. The unauthenticated test may already pass on `GET /api/calculations` because of the Task 3 dependency wiring, but POST and detail still need the dependency.

- [ ] **Step 3: Commit (red state, intentional)**

```bash
git add backend/tests/api/test_calculations.py
git commit -m "Phase 12 tests: cross-user isolation (red state, fixed by next task)"
```

---

## Task 8: Wire `require_user` into all three calculations endpoints + filter

**Files:**
- Modify: `backend/app/api/calculations.py`

- [ ] **Step 1: Add `Depends(require_user)` to all three handlers and filter by `user_id`**

In `backend/app/api/calculations.py`:

`create_calculation`: change signature and body so the dependency is present and `user_id` lands on the row:

```python
@router.post(
    "/calculations",
    response_model=CalculationResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(CALCULATIONS_WRITE_RATE_LIMIT)
def create_calculation(
    request: Request,
    payload: HeatmapRequest,
    user_id: str = Depends(require_user),
    session: Session = Depends(get_session),
) -> CalculationResponse:
    # ... unchanged compute block ...
    record = CalculationInput(
        id=calc_id,
        s=payload.S,
        k=payload.K,
        t=payload.T,
        r=payload.r,
        sigma=payload.sigma,
        vol_shock_min=payload.vol_shock[0],
        vol_shock_max=payload.vol_shock[1],
        spot_shock_min=payload.spot_shock[0],
        spot_shock_max=payload.spot_shock[1],
        rows=payload.rows,
        cols=payload.cols,
        user_id=user_id,  # NEW
    )
```

`list_calculations`: filter both the count and the row scan:

```python
@router.get("/calculations", response_model=CalculationListResponse)
@limiter.limit(CALCULATIONS_READ_RATE_LIMIT)
def list_calculations(
    request: Request,
    limit: int = Query(LIST_LIMIT_DEFAULT, ge=1, le=LIST_LIMIT_MAX, description="Page size."),
    offset: int = Query(0, ge=0, le=10_000, description="Number of items to skip."),
    user_id: str = Depends(require_user),
    session: Session = Depends(get_session),
) -> CalculationListResponse:
    total = int(
        session.execute(
            select(func.count(CalculationInput.id)).where(CalculationInput.user_id == user_id)
        ).scalar_one()
    )
    rows = (
        session.execute(
            select(CalculationInput)
            .where(CalculationInput.user_id == user_id)
            .order_by(CalculationInput.created_at.desc(), CalculationInput.id.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    # ... rest of function unchanged ...
```

`read_calculation`: filter the lookup; existing 404 contract is preserved:

```python
@router.get("/calculations/{calculation_id}", response_model=CalculationDetail)
@limiter.limit(CALCULATIONS_READ_RATE_LIMIT)
def read_calculation(
    request: Request,
    calculation_id: str,
    user_id: str = Depends(require_user),
    session: Session = Depends(get_session),
) -> CalculationDetail:
    if not _UUID_RE.match(calculation_id):
        raise HTTPException(status_code=404, detail="Calculation not found.")

    record: CalculationInput | None = (
        session.query(CalculationInput)
        .options(selectinload(CalculationInput.outputs))
        .filter_by(id=calculation_id, user_id=user_id)
        .one_or_none()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Calculation not found.")
    # ... rest of function unchanged ...
```

- [ ] **Step 2: Run isolation tests, expect pass**

Run: `uv --project backend run pytest tests/api/test_calculations.py -v`
Expected: all tests pass.

- [ ] **Step 3: Run the full backend suite**

Run: `uv --project backend run pytest -q`
Expected: 312 + 12 ≈ 324 tests pass (12 new auth + isolation tests). No failures.

- [ ] **Step 4: Lint + type check**

Run:
```bash
uv --project backend run ruff check .
uv --project backend run mypy backend/app
```
Expected: clean.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/calculations.py
git commit -m "Phase 12 backend: gate /api/calculations endpoints, filter by user_id"
```

---

## Task 9: Update `render.yaml` to declare the new env vars

**Files:**
- Modify: `render.yaml`

- [ ] **Step 1: Add env var declarations**

Open `render.yaml`. In the `envVars:` section for the backend service, add:

```yaml
      - key: VEGA_AUTH0_DOMAIN
        sync: false
      - key: VEGA_AUTH0_AUDIENCE
        sync: false
```

(`sync: false` so Render does not overwrite values already set in its dashboard. The user provisions the actual values via the Render dashboard before merge.)

- [ ] **Step 2: Commit**

```bash
git add render.yaml
git commit -m "Phase 12 IaC: declare VEGA_AUTH0_* env vars in render.yaml"
```

---

## Task 10: Backend pause checkpoint

- [ ] **Step 1: Sanity check the backend on its own**

```bash
cd /home/mustafa/src/vega
uv --project backend run pytest -q
uv --project backend run ruff check .
uv --project backend run mypy backend/app
```
Expected: green across the board.

- [ ] **Step 2: Push the branch (do not open PR yet)**

```bash
git push -u origin phase-12-auth-design
```

This puts the work on origin in case the next session opens fresh. No PR is opened until the frontend lands.

- [ ] **Step 3: If pausing here**, update `STATUS.md` Resume notes:

In the "Resume notes" section, write:

```
2026-05-04: Phase 12 paused after backend complete. Last clean commit on phase-12-auth-design: <commit_sha_of_step_2>. Next: Task 11 (frontend deps install) onward.
```

Commit:
```bash
git add STATUS.md
git commit -m "Phase 12 pause: backend done, frontend pending"
git push
```

If continuing in the same window, skip to Task 11.

---

## Task 11: Add `@auth0/auth0-react` dependency

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/.env.example`

- [ ] **Step 1: Install the SDK**

```bash
cd /home/mustafa/src/vega/frontend
pnpm add @auth0/auth0-react
```

Expected: `package.json` and `pnpm-lock.yaml` updated. `@auth0/auth0-react` shows under `dependencies`.

- [ ] **Step 2: Add `.env.example` documenting the new vars**

Create `frontend/.env.example`:

```
# Vite build-time env vars. Copy to .env.local for development.
VITE_API_BASE_URL=http://localhost:8000
VITE_AUTH0_DOMAIN=
VITE_AUTH0_CLIENT_ID=
VITE_AUTH0_AUDIENCE=vega-api
VITE_AUTH0_REDIRECT_URI=http://localhost:5173/callback
```

- [ ] **Step 3: Commit**

```bash
cd /home/mustafa/src/vega
git add frontend/package.json frontend/pnpm-lock.yaml frontend/.env.example
git commit -m "Phase 12 frontend: add @auth0/auth0-react and .env.example"
```

---

## Task 12: Wrap `<App/>` in `<Auth0Provider>` with build-time validation

**Files:**
- Modify: `frontend/src/main.tsx`

- [ ] **Step 1: Replace `main.tsx` contents**

Open `frontend/src/main.tsx`. Replace the file with:

```tsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react'

import './index.css'
import App from './App.tsx'

function readVar(name: string, required: boolean): string {
  const value = (import.meta.env[name] as string | undefined) ?? ''
  const trimmed = typeof value === 'string' ? value.trim() : ''
  if (required && import.meta.env.PROD && trimmed === '') {
    throw new Error(
      `${name} is not set. Production builds require all VITE_AUTH0_* env vars; ` +
        'see docs/setup-guide.md (Auth0 setup).',
    )
  }
  return trimmed
}

const domain = readVar('VITE_AUTH0_DOMAIN', true)
const clientId = readVar('VITE_AUTH0_CLIENT_ID', true)
const audience = readVar('VITE_AUTH0_AUDIENCE', false) || 'vega-api'
const redirectUri =
  readVar('VITE_AUTH0_REDIRECT_URI', false) || `${window.location.origin}/callback`

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Auth0Provider
      domain={domain}
      clientId={clientId}
      authorizationParams={{
        audience,
        redirect_uri: redirectUri,
      }}
      useRefreshTokens={true}
      cacheLocation="memory"
    >
      <App />
    </Auth0Provider>
  </StrictMode>,
)
```

- [ ] **Step 2: Build dev (smoke)**

```bash
cd /home/mustafa/src/vega/frontend
pnpm tsc
```
Expected: no type errors.

- [ ] **Step 3: Commit**

```bash
cd /home/mustafa/src/vega
git add frontend/src/main.tsx
git commit -m "Phase 12 frontend: wrap App in Auth0Provider with prod fail-loud"
```

---

## Task 13: `useAuth0` mock helper for tests

**Files:**
- Create: `frontend/src/test/auth0-mock.ts`

- [ ] **Step 1: Create the mock helper**

Create `frontend/src/test/auth0-mock.ts`:

```ts
import { vi } from 'vitest'

export interface MockAuth0State {
  isAuthenticated: boolean
  isLoading: boolean
  user?: { sub: string; email?: string; name?: string }
  getAccessTokenSilently: ReturnType<typeof vi.fn>
  loginWithRedirect: ReturnType<typeof vi.fn>
  logout: ReturnType<typeof vi.fn>
  handleRedirectCallback: ReturnType<typeof vi.fn>
}

export function makeAuth0Mock(overrides: Partial<MockAuth0State> = {}): MockAuth0State {
  return {
    isAuthenticated: false,
    isLoading: false,
    user: undefined,
    getAccessTokenSilently: vi.fn().mockResolvedValue('test.jwt.token'),
    loginWithRedirect: vi.fn().mockResolvedValue(undefined),
    logout: vi.fn().mockResolvedValue(undefined),
    handleRedirectCallback: vi.fn().mockResolvedValue({ appState: {} }),
    ...overrides,
  }
}

// Module-level mutable state. Tests call `setAuth0MockState(...)` to swap
// the value the mocked `useAuth0()` will return. The `vi.mock(...)` call
// itself MUST live at the top of each test file (vi.mock is hoisted at
// parse time; calling it inside a function does not work).
let currentState: MockAuth0State = makeAuth0Mock()

export function setAuth0MockState(state: MockAuth0State): void {
  currentState = state
}

export function getAuth0MockState(): MockAuth0State {
  return currentState
}

export function resetAuth0MockState(): void {
  currentState = makeAuth0Mock()
}
```

Each test file that uses this helper adds the following at the very top of the file:

```ts
import { vi } from 'vitest'
import { getAuth0MockState } from '../test/auth0-mock'

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => getAuth0MockState(),
  Auth0Provider: ({ children }: { children: unknown }) => children,
}))
```

Tests then call `setAuth0MockState(makeAuth0Mock({ ... }))` to set up each scenario, and `resetAuth0MockState()` in `beforeEach`.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/test/auth0-mock.ts
git commit -m "Phase 12 frontend: useAuth0 test mock helper"
```

---

## Task 14: `authedFetch` wrapper in `lib/api.ts`

**Files:**
- Modify: `frontend/src/lib/api.ts`

The existing `getJson` and `postJson` helpers do not take an injected token. We add an optional `bearerToken` to the `FetchOptions` and route the three calculation calls through it. The token is supplied by callers (which use `useAuth0().getAccessTokenSilently()` and pass the result down).

- [ ] **Step 1: Extend `FetchOptions` to accept a bearer token**

In `frontend/src/lib/api.ts`, find:

```ts
interface FetchOptions {
  baseUrl?: string
  timeoutMs?: number
  signal?: AbortSignal
}
```

Replace with:

```ts
interface FetchOptions {
  baseUrl?: string
  timeoutMs?: number
  signal?: AbortSignal
  bearerToken?: string
}
```

- [ ] **Step 2: Inject `Authorization` header in `getJson` and `postJson`**

In `getJson`, find:

```ts
    response = await fetch(`${baseUrl}${path}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      credentials: 'omit',
      mode: 'cors',
      signal: controller.signal,
    })
```

Replace with:

```ts
    const headers: Record<string, string> = { Accept: 'application/json' }
    if (options.bearerToken) {
      headers.Authorization = `Bearer ${options.bearerToken}`
    }
    response = await fetch(`${baseUrl}${path}`, {
      method: 'GET',
      headers,
      credentials: 'omit',
      mode: 'cors',
      signal: controller.signal,
    })
```

In `postJson`, locate the equivalent block (the `fetch(...)` call inside `postJson`) and apply the same change: build a `headers` record that conditionally includes `Authorization`.

Also surface 401 in `postJson` and `getJson` as a new `PriceError` kind so the UI can route to a sign-in nudge:

In the `PriceErrorKind` union add `'unauthorized'`:

```ts
export type PriceErrorKind =
  | 'validation'
  | 'rate_limit'
  | 'server'
  | 'network'
  | 'timeout'
  | 'aborted'
  | 'not_found'
  | 'upstream_timeout'
  | 'upstream'
  | 'unauthorized'
```

In both `getJson` and `postJson`'s status handling block, add the 401 branch before the generic `server` fallback:

```ts
  if (response.status === 401) {
    throw new PriceError('unauthorized', 'Sign in required.', { status: 401 })
  }
```

- [ ] **Step 3: Run TS check**

```bash
cd /home/mustafa/src/vega/frontend
pnpm tsc
```
Expected: clean.

- [ ] **Step 4: Commit**

```bash
cd /home/mustafa/src/vega
git add frontend/src/lib/api.ts
git commit -m "Phase 12 frontend: authedFetch (bearerToken option) + 401 PriceError kind"
```

---

## Task 15: `<SignInButton/>` and `<UserButton/>` components

**Files:**
- Create: `frontend/src/components/AuthButtons.tsx`

- [ ] **Step 1: Create the component file**

Create `frontend/src/components/AuthButtons.tsx`:

```tsx
import { useAuth0 } from '@auth0/auth0-react'
import type { JSX } from 'react'

export function SignInButton(): JSX.Element {
  const { loginWithRedirect, isLoading } = useAuth0()
  return (
    <button
      type="button"
      data-element="signInButton"
      onClick={() => void loginWithRedirect()}
      disabled={isLoading}
    >
      Sign in
    </button>
  )
}

export function UserButton(): JSX.Element | null {
  const { user, logout, isAuthenticated } = useAuth0()
  if (!isAuthenticated || !user) return null
  return (
    <div data-element="userButton">
      <span aria-label="Signed in as">{user.email ?? user.name ?? user.sub}</span>
      <button
        type="button"
        data-element="signOutButton"
        onClick={() =>
          void logout({ logoutParams: { returnTo: window.location.origin } })
        }
      >
        Sign out
      </button>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/AuthButtons.tsx
git commit -m "Phase 12 frontend: SignInButton and UserButton components"
```

---

## Task 16: Sidebar footer in `LayoutShell`

**Files:**
- Modify: `frontend/src/components/LayoutShell.tsx`
- Modify: `frontend/src/components/LayoutShell.test.tsx`

- [ ] **Step 1: Write failing tests**

Open `frontend/src/components/LayoutShell.test.tsx`. At the very top of the file (before any other imports that may transitively pull `@auth0/auth0-react`), add:

```tsx
import { vi } from 'vitest'
import { getAuth0MockState, makeAuth0Mock, resetAuth0MockState, setAuth0MockState } from '../test/auth0-mock'

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => getAuth0MockState(),
  Auth0Provider: ({ children }: { children: unknown }) => children,
}))
```

Then append the new describe block:

```tsx
describe('LayoutShell auth surface', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })

  it('shows the sign-in button when logged out', () => {
    setAuth0MockState(makeAuth0Mock({ isAuthenticated: false }))
    render(<LayoutShell active="pricing" onNav={() => {}}><div /></LayoutShell>)
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('shows the user button when logged in', () => {
    setAuth0MockState(
      makeAuth0Mock({
        isAuthenticated: true,
        user: { sub: 'google-oauth2|123', email: 'me@example.com' },
      }),
    )
    render(<LayoutShell active="pricing" onNav={() => {}}><div /></LayoutShell>)
    expect(screen.getByText('me@example.com')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run, expect failure**

Run: `pnpm --filter frontend test -- LayoutShell`
Expected: new tests fail because the sidebar still renders the static "Local" footer with no buttons.

- [ ] **Step 3: Edit `LayoutShell.tsx`**

Replace the `data-element="footer"` block with:

```tsx
        <div data-element="footer" aria-label="Account">
          <UserButton />
          {/* SignInButton renders only when logged out via useAuth0 inside */}
          <AuthFooter />
        </div>
```

At the top of the file add:

```tsx
import { useAuth0 } from '@auth0/auth0-react'
import { SignInButton, UserButton } from './AuthButtons'
```

Define `AuthFooter` at the bottom of the file:

```tsx
function AuthFooter() {
  const { isAuthenticated } = useAuth0()
  if (isAuthenticated) return null
  return <SignInButton />
}
```

- [ ] **Step 4: Run, expect pass**

Run: `pnpm --filter frontend test -- LayoutShell`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/LayoutShell.tsx frontend/src/components/LayoutShell.test.tsx
git commit -m "Phase 12 frontend: LayoutShell sidebar footer with auth state"
```

---

## Task 17: `HistoryScreen` branches on auth state

**Files:**
- Modify: `frontend/src/screens/HistoryScreen.tsx`
- Modify: `frontend/src/screens/HistoryScreen.test.tsx`

- [ ] **Step 1: Write failing tests**

Open `frontend/src/screens/HistoryScreen.test.tsx`. At the very top of the file add the mock plumbing (if not already present from an earlier task):

```tsx
import { vi } from 'vitest'
import { getAuth0MockState, makeAuth0Mock, resetAuth0MockState, setAuth0MockState } from '../test/auth0-mock'

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => getAuth0MockState(),
  Auth0Provider: ({ children }: { children: unknown }) => children,
}))
```

Then add the new describe block:

```tsx
describe('HistoryScreen auth gating', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })

  it('renders the empty state when logged out', async () => {
    setAuth0MockState(makeAuth0Mock({ isAuthenticated: false }))
    render(<HistoryScreen />)
    expect(
      await screen.findByText(/sign in to see your saved calculations/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('fetches with a bearer token when logged in', async () => {
    const getToken = vi.fn().mockResolvedValue('jwt-abc')
    setAuth0MockState(
      makeAuth0Mock({
        isAuthenticated: true,
        getAccessTokenSilently: getToken,
        user: { sub: 'github|user-x' },
      }),
    )
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ items: [], total: 0, limit: 20, offset: 0 }),
        { status: 200, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    render(<HistoryScreen />)
    await screen.findByText(/saved calculations/i)
    const call = fetchSpy.mock.calls[0]
    const opts = call?.[1] as RequestInit | undefined
    const headers = (opts?.headers ?? {}) as Record<string, string>
    expect(headers.Authorization).toBe('Bearer jwt-abc')
    fetchSpy.mockRestore()
  })
})
```

- [ ] **Step 2: Run, expect failure**

Run: `pnpm --filter frontend test -- HistoryScreen`
Expected: 2 new tests fail.

- [ ] **Step 3: Edit `HistoryScreen.tsx`**

At the top, add:

```tsx
import { useAuth0 } from '@auth0/auth0-react'
import { SignInButton } from '../components/AuthButtons'
```

In the body of `HistoryScreen`, before the existing `useState` block, add:

```tsx
const { isAuthenticated, getAccessTokenSilently } = useAuth0()
```

Modify the early return at the start of the JSX (or wrap the existing return) so that when `!isAuthenticated`:

```tsx
if (!isAuthenticated) {
  return (
    <section data-component="HistoryScreen">
      <div data-element="emptyState" className="tr-card">
        <h2 className="tr-card-title">Saved calculations</h2>
        <p>Sign in to see your saved calculations.</p>
        <SignInButton />
      </div>
    </section>
  )
}
```

In `loadList` and `loadDetail`, fetch the token and pass it through the `fetchCalculations` and `fetchCalculation` calls:

```tsx
const token = await getAccessTokenSilently()
const result = await fetchCalculations({
  limit: PAGE_SIZE,
  offset: 0,
  signal: controller.signal,
  bearerToken: token,
})
```

(Apply the same pattern to `loadDetail`.)

- [ ] **Step 4: Run, expect pass**

Run: `pnpm --filter frontend test -- HistoryScreen`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/screens/HistoryScreen.tsx frontend/src/screens/HistoryScreen.test.tsx
git commit -m "Phase 12 frontend: HistoryScreen auth-gated empty state and bearer fetch"
```

---

## Task 18: `HeatMapScreen.onSave` branches on auth + pendingSave funnel

**Files:**
- Modify: `frontend/src/screens/HeatMapScreen.tsx`
- Create: `frontend/src/screens/HeatMapScreen.test.tsx`

- [ ] **Step 1: Write failing tests**

Create `frontend/src/screens/HeatMapScreen.test.tsx`:

```tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import {
  getAuth0MockState,
  makeAuth0Mock,
  resetAuth0MockState,
  setAuth0MockState,
} from '../test/auth0-mock'

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => getAuth0MockState(),
  Auth0Provider: ({ children }: { children: unknown }) => children,
}))

import { HeatMapScreen } from './HeatMapScreen'

describe('HeatMapScreen Save button', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })

  it('triggers loginWithRedirect with pendingSave when logged out', async () => {
    const loginWithRedirect = vi.fn().mockResolvedValue(undefined)
    setAuth0MockState(
      makeAuth0Mock({ isAuthenticated: false, loginWithRedirect }),
    )
    render(<HeatMapScreen />)
    // Compute a heat map first so the Save button enables.
    fireEvent.click(screen.getByRole('button', { name: /compute/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /save/i })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => expect(loginWithRedirect).toHaveBeenCalledTimes(1))
    const arg = loginWithRedirect.mock.calls[0]?.[0] as { appState?: { pendingSave?: unknown } }
    expect(arg?.appState?.pendingSave).toBeDefined()
  })

  it('saves directly when logged in', async () => {
    const getToken = vi.fn().mockResolvedValue('jwt-xyz')
    setAuth0MockState(
      makeAuth0Mock({ isAuthenticated: true, getAccessTokenSilently: getToken }),
    )
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({
          calculation_id: '00000000-0000-0000-0000-000000000001',
          call: [[1]],
          put: [[1]],
          model: 'black_scholes',
          sigma_axis: [0.2],
          spot_axis: [100],
        }),
        { status: 201, headers: { 'Content-Type': 'application/json' } },
      ),
    )
    render(<HeatMapScreen />)
    fireEvent.click(screen.getByRole('button', { name: /compute/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /save/i })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => {
      const headers = (fetchSpy.mock.calls.at(-1)?.[1] as RequestInit | undefined)?.headers as
        | Record<string, string>
        | undefined
      expect(headers?.Authorization).toBe('Bearer jwt-xyz')
    })
    fetchSpy.mockRestore()
  })
})
```

(If the existing dev server / heatmap fixtures need a different "Compute" button label, look up the actual `aria-label` in `HeatMapScreen.tsx` and adjust.)

- [ ] **Step 2: Run, expect failure**

Run: `pnpm --filter frontend test -- HeatMapScreen`
Expected: 2 tests fail.

- [ ] **Step 3: Edit `HeatMapScreen.tsx`**

Add at the top:

```tsx
import { useAuth0 } from '@auth0/auth0-react'
```

In `HeatMapScreen` body (before the existing `useState` calls):

```tsx
const { isAuthenticated, getAccessTokenSilently, loginWithRedirect } = useAuth0()
```

Modify `onSave`:

```tsx
const onSave = useCallback(async () => {
  if (response === null) return
  if (!isAuthenticated) {
    await loginWithRedirect({
      appState: { pendingSave: { request, response } },
    })
    return
  }
  inFlightSave.current?.abort()
  const controller = new AbortController()
  inFlightSave.current = controller
  setSaveStatus({ kind: 'saving' })
  try {
    const token = await getAccessTokenSilently()
    const result = await saveCalculation(request, {
      signal: controller.signal,
      bearerToken: token,
    })
    setSaveStatus({ kind: 'saved', calculationId: result.calculation_id })
  } catch (err) {
    const message = err instanceof PriceError ? err.message : 'Could not save.'
    setSaveStatus({ kind: 'error', message })
  }
}, [request, response, isAuthenticated, getAccessTokenSilently, loginWithRedirect])
```

(The `request` variable name must match what HeatMapScreen already passes to `saveCalculation`. Confirm by reading the existing `onSave` body before editing.)

The Save button label gains a logged-out variant. Find the label string and add:

```tsx
const saveLabelText = !isAuthenticated
  ? 'Sign in to save'
  : saveStatus.kind === 'saving' ? 'Saving...' : saveStatus.kind === 'saved' ? 'Saved' : 'Save'
```

- [ ] **Step 4: Run, expect pass**

Run: `pnpm --filter frontend test -- HeatMapScreen`
Expected: 2 tests pass; existing HeatMapScreen tests still pass.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/screens/HeatMapScreen.tsx frontend/src/screens/HeatMapScreen.test.tsx
git commit -m "Phase 12 frontend: HeatMapScreen onSave gates auth, pendingSave funnel"
```

---

## Task 19: `/callback` route handler with `pendingSave` replay

**Files:**
- Create: `frontend/src/lib/auth-callback.tsx`
- Create: `frontend/src/lib/auth-callback.test.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Write failing test**

Create `frontend/src/lib/auth-callback.test.tsx`:

```tsx
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'

import {
  getAuth0MockState,
  makeAuth0Mock,
  resetAuth0MockState,
  setAuth0MockState,
} from '../test/auth0-mock'

vi.mock('@auth0/auth0-react', () => ({
  useAuth0: () => getAuth0MockState(),
  Auth0Provider: ({ children }: { children: unknown }) => children,
}))

import { AuthCallback } from './auth-callback'

describe('AuthCallback', () => {
  beforeEach(() => {
    resetAuth0MockState()
  })

  it('replays pendingSave once and redirects home', async () => {
    const handleRedirectCallback = vi.fn().mockResolvedValue({
      appState: {
        pendingSave: {
          request: {
            S: 100, K: 100, T: 1, r: 0.05, sigma: 0.2,
            vol_shock: [-0.5, 0.5], spot_shock: [-0.3, 0.3], rows: 5, cols: 5,
          },
        },
      },
    })
    const getToken = vi.fn().mockResolvedValue('jwt-cb')
    setAuth0MockState(
      makeAuth0Mock({
        isAuthenticated: true,
        handleRedirectCallback,
        getAccessTokenSilently: getToken,
      }),
    )
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(
      new Response('{"calculation_id":"00000000-0000-0000-0000-000000000001"}', {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const replaceSpy = vi.spyOn(window.history, 'replaceState')

    render(<AuthCallback />)

    await waitFor(() => expect(handleRedirectCallback).toHaveBeenCalled())
    await waitFor(() => expect(fetchSpy).toHaveBeenCalled())
    await waitFor(() =>
      expect(replaceSpy).toHaveBeenCalledWith(expect.anything(), '', '/'),
    )
    fetchSpy.mockRestore()
    replaceSpy.mockRestore()
  })
})
```

- [ ] **Step 2: Run, expect failure**

Run: `pnpm --filter frontend test -- auth-callback`
Expected: FAIL — file does not exist.

- [ ] **Step 3: Create `auth-callback.tsx`**

```tsx
import { useEffect, useRef, useState, type JSX } from 'react'
import { useAuth0 } from '@auth0/auth0-react'

import { saveCalculation, type HeatmapRequest } from './api'

interface PendingSave {
  request: HeatmapRequest
}

function isPendingSave(value: unknown): value is PendingSave {
  if (typeof value !== 'object' || value === null) return false
  const v = value as Record<string, unknown>
  return typeof v.request === 'object' && v.request !== null
}

export function AuthCallback(): JSX.Element {
  const { handleRedirectCallback, getAccessTokenSilently } = useAuth0()
  const [status, setStatus] = useState<'processing' | 'done' | 'error'>('processing')
  const ran = useRef(false)

  useEffect(() => {
    if (ran.current) return
    ran.current = true
    let cancelled = false

    const run = async () => {
      try {
        const result = await handleRedirectCallback()
        const appState = (result as { appState?: unknown } | undefined)?.appState
        const pending = (appState as { pendingSave?: unknown } | undefined)?.pendingSave
        if (isPendingSave(pending)) {
          const token = await getAccessTokenSilently()
          await saveCalculation(pending.request, { bearerToken: token })
        }
        if (cancelled) return
        window.history.replaceState({}, '', '/')
        setStatus('done')
      } catch {
        if (cancelled) return
        setStatus('error')
      }
    }

    void run()
    return () => {
      cancelled = true
    }
  }, [handleRedirectCallback, getAccessTokenSilently])

  if (status === 'error') {
    return <p>Sign-in failed. Please try again.</p>
  }
  return <p>Signing you in…</p>
}
```

- [ ] **Step 4: Update `App.tsx` to render `AuthCallback` at `/callback`**

Open `frontend/src/App.tsx`. Replace with:

```tsx
import { useState, useEffect, type JSX } from 'react'

import { LayoutShell } from './components/LayoutShell'
import { BacktestScreen } from './screens/BacktestScreen'
import { HeatMapScreen } from './screens/HeatMapScreen'
import { HistoryScreen } from './screens/HistoryScreen'
import { PricingScreen } from './screens/PricingScreen'
import { AuthCallback } from './lib/auth-callback'
import type { ScreenId } from './lib/screens'

function App(): JSX.Element {
  const [active, setActive] = useState<ScreenId>('pricing')
  const [path, setPath] = useState<string>(window.location.pathname)

  useEffect(() => {
    const onPop = () => setPath(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  if (path === '/callback') {
    return <AuthCallback />
  }

  return (
    <LayoutShell active={active} onNav={setActive}>
      {active === 'pricing' && <PricingScreen key="pricing" />}
      {active === 'compare' && <PricingScreen key="compare" initialCompare={true} />}
      {active === 'heatmap' && <HeatMapScreen />}
      {active === 'backtest' && <BacktestScreen />}
      {active === 'history' && <HistoryScreen />}
    </LayoutShell>
  )
}

export default App
```

- [ ] **Step 5: Run, expect pass**

Run: `pnpm --filter frontend test -- auth-callback`
Expected: pass.

Run: `pnpm --filter frontend test --run`
Expected: full frontend suite green.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/auth-callback.tsx frontend/src/lib/auth-callback.test.tsx frontend/src/App.tsx
git commit -m "Phase 12 frontend: /callback handler replays pendingSave once"
```

---

## Task 20: CSP `_headers` allows Auth0

**Files:**
- Modify: `frontend/public/_headers`

- [ ] **Step 1: Edit the CSP**

In `frontend/public/_headers`, change the `Content-Security-Policy` line. Specifically:

- `connect-src` becomes `'self' https://*.onrender.com https://*.auth0.com`.
- Add `frame-src https://*.auth0.com` (defense in depth in case the SDK falls back to silent-auth iframes).

After editing, the line reads:

```
  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://s.gravatar.com https://*.auth0.com; font-src 'self' data:; connect-src 'self' https://*.onrender.com https://*.auth0.com; frame-src https://*.auth0.com; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'; upgrade-insecure-requests
```

(Auth0's Universal Login may render the user's social provider avatar from `gravatar.com` or the Auth0 CDN; allow those in `img-src`.)

- [ ] **Step 2: Commit**

```bash
git add frontend/public/_headers
git commit -m "Phase 12 IaC: CSP allows Auth0 (connect-src, frame-src, img-src)"
```

---

## Task 21: Threat model addendum

**Files:**
- Modify: `docs/security/threat-model.md`

- [ ] **Step 1: Add the Phase 12 STRIDE block**

Open `docs/security/threat-model.md`. Add a new section near the bottom:

```markdown
## Phase 12 addendum: authentication and per user history

The `/api/calculations*` endpoints are now gated behind a verified Auth0 JWT. Identity is the JWT `sub` claim; no local user table.

| Category | Threat | Mitigation |
|---|---|---|
| Spoofing | Impersonate another user | RS256 signature verification against Auth0 JWKS, audience check (`vega-api`), issuer check (`https://<tenant>.auth0.com/`), expiry check. |
| Tampering | Modify token payload | Signature verification rejects any modification. |
| Repudiation | Deny saving a calculation | Existing structured logs include request IDs; not separately logged for v1. |
| Information disclosure | Read another user's saved calculation | `WHERE user_id = ?` filter on every query; cross-user lookups return 404 (IDOR-as-not-found) to avoid leaking row existence. |
| Denial of service | Flood saves under a stolen token | Existing per-route per-IP rate limits (12/min write, 60/min read) unchanged. Per-user rate limits explicitly out of scope. |
| Elevation of privilege | Gain admin access | No roles in the system; every authenticated user has identical scope (their own calculations only). |

### Residual risks added in Phase 12

- **Refresh token cookie** is set by Auth0's domain. Its security posture (httpOnly, Secure, SameSite, rotation) is Auth0's responsibility. Vega cannot harden it further.
- **Auth0 tenant takeover** would let an attacker mint valid JWTs. Mitigated by Auth0's own controls (tenant admin MFA on the maintainer's account).
```

- [ ] **Step 2: Commit**

```bash
git add docs/security/threat-model.md
git commit -m "Phase 12 docs: STRIDE addendum for auth surface"
```

---

## Task 22: Setup guide gets an Auth0 section

**Files:**
- Modify: `docs/setup-guide.md`

- [ ] **Step 1: Add the Auth0 section**

Append to `docs/setup-guide.md`:

```markdown
## Auth0 setup (Phase 12)

Vega uses Auth0 for sign-in. Provision a free tenant and register two artifacts: a Single Page Application (the frontend) and an API (the backend audience).

1. Create an Auth0 tenant at <https://manage.auth0.com>. Free tier covers 7,500 monthly active users; Vega will not approach this.
2. **Create the API**: Applications → APIs → Create API. Name `Vega API`, identifier `vega-api`, signing algorithm `RS256`. The identifier is the `audience` value the frontend and backend share.
3. **Create the SPA**: Applications → Applications → Create Application. Type `Single Page Web Applications`. After creation, set:
   - Allowed Callback URLs: `http://localhost:5173/callback, https://vega-2rd.pages.dev/callback`.
   - Allowed Logout URLs: `http://localhost:5173, https://vega-2rd.pages.dev`.
   - Allowed Web Origins: `http://localhost:5173, https://vega-2rd.pages.dev`.
   - Refresh Token Rotation: enabled. Refresh Token Expiration: rotating.
4. **Enable identity providers**: Authentication → Social → enable Google and GitHub. No magic link, no email plus password.

### Frontend env vars (Cloudflare Pages, build-time)

```
VITE_AUTH0_DOMAIN=<tenant>.us.auth0.com
VITE_AUTH0_CLIENT_ID=<spa client id>
VITE_AUTH0_AUDIENCE=vega-api
VITE_AUTH0_REDIRECT_URI=https://vega-2rd.pages.dev/callback
```

A production build without `VITE_AUTH0_DOMAIN` or `VITE_AUTH0_CLIENT_ID` aborts (fail-loud).

### Backend env vars (Render service env)

```
VEGA_AUTH0_DOMAIN=<tenant>.us.auth0.com
VEGA_AUTH0_AUDIENCE=vega-api
```

Production startup fails loud if either is missing when `VEGA_ENVIRONMENT=production`.

### Local dev

Copy `frontend/.env.example` to `frontend/.env.local` and fill in the SPA values. The backend reads its values from your shell env when you run `uv --project backend run uvicorn app.main:app --reload`.
```

- [ ] **Step 2: Commit**

```bash
git add docs/setup-guide.md
git commit -m "Phase 12 docs: Auth0 setup section in setup-guide"
```

---

## Task 23: Final smoke and lint pass

- [ ] **Step 1: Backend full suite + lint + types**

```bash
cd /home/mustafa/src/vega
uv --project backend run pytest -q
uv --project backend run ruff check .
uv --project backend run mypy backend/app
```
Expected: all green. Test count ~324 (312 + 12).

- [ ] **Step 2: Frontend full suite + lint + types + build**

```bash
cd /home/mustafa/src/vega/frontend
pnpm test --run
pnpm lint
pnpm tsc
pnpm build
```
Expected: all green. Test count ~126 (120 + 6).

- [ ] **Step 3: Audit**

```bash
cd /home/mustafa/src/vega
uv --project backend run pip-audit
cd frontend && pnpm audit
```
Expected: clean. If `pip-audit` flags `pyjwt` or `cryptography`, bump to a clean version.

---

## Task 24: Close Phase 12

**Files:**
- Modify: `STATUS.md`
- Modify: `/home/mustafa/src/tracker/total_token_usage.md` (outside repo; see CLAUDE.md "Updating the token usage tracker")

- [ ] **Step 1: Flip Phase 12 row to `completed`**

In `STATUS.md`:
- Phase 12 row status `in progress` → `completed`. Fill in `Completed on` with `2026-05-04` (or the actual date if it slipped).
- Update the "Last updated" line.
- Update "Next phase" to: `**No spec phase remaining.** Phase 12 closed v1+1; the next deferred polish item from `future-ideas.md` is "Logo, favicon, and tab title".`

- [ ] **Step 2: Append a Phase 12 block to the token tracker**

Per `CLAUDE.md`, read `/home/mustafa/src/tracker/total_token_usage.md` to match its existing format, then append a Phase 12 block following the per-agent + PM-estimate pattern.

- [ ] **Step 3: Commit**

```bash
git add STATUS.md
git commit -m "Phase 12 close: STATUS.md updated, v1+1 shipped"
```

(Token tracker lives outside the repo; commit only the `STATUS.md` change.)

- [ ] **Step 4: Open the PR**

```bash
git push
gh pr create --title "Phase 12: authentication and per user history" --body "$(cat <<'EOF'
## Summary

- Auth0 + Google/GitHub OAuth via @auth0/auth0-react.
- Backend require_user dependency, JWKS verification (RS256), audience and issuer checks.
- calculation_inputs gains user_id NOT NULL plus composite (user_id, created_at DESC) index.
- Existing rows dropped at migration; spec policy.
- Logged-out UX: Save and History stay visible; clicking either triggers loginWithRedirect with appState.pendingSave so the save replays after the redirect.
- CSP, threat model, setup guide, render.yaml, STATUS.md updated.

## Test plan

- [ ] backend pytest green, ~324 tests
- [ ] frontend vitest green, ~126 tests
- [ ] pip-audit clean
- [ ] pnpm audit clean
- [ ] manual sign in via Google in dev
- [ ] manual sign in via GitHub in dev
- [ ] manual save flow logged-out -> login -> save replays
- [ ] manual cross-user 404 check
EOF
)"
```

- [ ] **Step 5: Watch checks; admin merge when green**

```bash
gh pr checks <N> --watch --interval 10
gh pr merge <N> --squash --delete-branch --admin
git checkout main && git pull --ff-only
```

- [ ] **Step 6: Verify production**

After Cloudflare Pages and Render redeploy:
- Visit `https://vega-2rd.pages.dev/`. Confirm the public screens work without sign-in.
- Click Sign in, complete Google flow, confirm landing on the same page with a user button in the sidebar.
- Click Save on a heatmap, confirm 201, check History.
- Sign out, confirm reverting to the empty state on History.

---

## Self-review against the spec

Mapping each spec section to a task:

- **Goal / Non goals**: covered as the natural shape of the work; non-goals are not implemented (no email-password, no per-user rate limits).
- **Auth perimeter table**: tasks 8 (backend) and 16-19 (frontend) implement the full table.
- **Architecture / Provider and identity methods**: tasks 11-12 wire `@auth0/auth0-react` with the correct provider; identity methods (Google, GitHub) configured in the Auth0 dashboard per task 22.
- **Architecture / Frontend (env vars, fail-loud, token storage)**: task 12.
- **Architecture / Backend (auth.py, env vars, fail-loud, no local user table)**: tasks 2, 3.
- **Token verification details (pyjwt[crypto], JWKS TTL, RS256, audience/issuer/exp checks)**: task 1 (dep) and task 3 (impl).
- **Data model (truncate, user_id NOT NULL VARCHAR(64), composite index)**: tasks 4 (migration) and 5 (ORM).
- **API surface (POST/GET/GET-by-id with require_user, IDOR-as-404, rate limits unchanged)**: tasks 3 and 8; tested in tasks 6, 7.
- **Frontend changes table**: tasks 12 (main.tsx), 14 (api.ts authedFetch), 15-16 (LayoutShell + AuthButtons), 17 (HistoryScreen), 18 (HeatMapScreen), 19 (auth-callback + App.tsx).
- **Data flow (sign in / save logged-in / save logged-out / history / sign out)**: tasks 16, 17, 18, 19 cover all four flows; sign-out is in `<UserButton/>`.
- **Error handling table**: 401 generic message in task 3; SDK boundary toast on token failure can be surfaced inside `AuthCallback` (task 19); IDOR 404 in task 8.
- **Testing (backend auth tests, isolation tests, JWT fixture, frontend tests)**: tasks 3, 5, 6, 7, 16, 17, 18, 19.
- **Threat model addendum**: task 21.
- **Phase model and operational changes (STATUS.md, _headers CSP, setup-guide, audit clean)**: tasks 0, 9, 20, 22, 23, 24.
- **Acceptance criteria 1-9**: task 23 (suites + audit) and task 24 (STATUS, manual prod verification).

No spec requirement is unaddressed. No types or method names are inconsistent across tasks.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-04-auth-and-per-user-history.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Good for this plan because it has 24 tasks and a natural pause point at Task 10.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints. Good if you want to keep context in one window.

Which approach?
