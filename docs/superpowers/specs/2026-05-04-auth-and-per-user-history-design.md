# Phase 12 design: authentication and per user history

**Status**: design approved 2026-05-04, awaiting implementation plan.
**Owner**: Project Manager.
**Source idea**: `future-ideas.md` entry "Authentication and per user history".
**Phase**: new Phase 12 to be added to `STATUS.md` after this design lands.

## Goal

Each Vega visitor can sign in (Google or GitHub OAuth via Auth0) and gets a private, per user history of saved heat map calculations. The pricer, heat map visualization, Greeks panel, model compare, and backtest stay fully public so the demo remains useful for casual visitors. Sign in is required only to save a calculation and to use the History screen. Cross user reads are impossible at the API layer.

## Non goals

- Email plus password login, password reset, account lockout (OAuth only).
- Per user rate limits (per IP rate limits stay as they are today).
- Sharing a saved calculation with another user.
- Account deletion or data export (GDPR style flows). If real traffic ever materializes this becomes the next item.
- Migrating any existing calculations into the new schema (existing rows are dropped at migration time, see "Data model").

## Auth perimeter

| Endpoint | Auth required? |
|---|---|
| `POST /api/price` | No |
| `POST /api/heatmap` | No |
| `GET /api/tickers` | No |
| `POST /api/backtest` | No |
| `POST /api/calculations` | **Yes** |
| `GET /api/calculations` | **Yes** |
| `GET /api/calculations/{id}` | **Yes** |

Frontend mirrors this: sidebar nav and the Pricing, Compare, Heatmap, and Backtest screens are public. The Save button on the heatmap and the History screen are auth gated.

## Architecture

### Provider and identity methods

- **Provider**: Auth0 (free tier, 7,500 MAU; Vega will not approach this).
- **Identity methods**: Google OAuth and GitHub OAuth only. No magic link, no email plus password.
- **Why Auth0 over Clerk**: both are free at Vega traffic; Auth0's name carries more weight in finance and legacy enterprise hiring, which is the resume audience for this project.

### Frontend

- Library: `@auth0/auth0-react`.
- Wrap the app in `<Auth0Provider>` configured with `domain`, `clientId`, `audience: "vega-api"`, `redirect_uri: <origin>/callback`. All four come from Vite env vars (`VITE_AUTH0_DOMAIN`, `VITE_AUTH0_CLIENT_ID`, `VITE_AUTH0_AUDIENCE`, `VITE_AUTH0_REDIRECT_URI`).
- Production fail loud: missing `VITE_AUTH0_DOMAIN` or `VITE_AUTH0_CLIENT_ID` at build time aborts the Vite build. Mirrors the existing `VEGA_CORS_ORIGINS` and `VITE_API_BASE_URL` fail loud pattern.
- Token storage: access token (JWT) held in memory by the SDK. Refresh token in an httpOnly cookie set by Auth0's domain. Refresh Token Rotation enabled in the Auth0 application settings.

### Backend

- New module `app/core/auth.py` exposing:
  - A startup hook that fetches Auth0's JWKS once and caches the keys.
  - A `require_user(request: Request) -> str` FastAPI dependency that reads `Authorization: Bearer <jwt>`, verifies signature, audience, issuer, and expiry, and returns the JWT's `sub` claim. Raises `HTTPException(401, detail="Authentication required.")` on any failure.
- New env vars (Render service env, with the existing `VEGA_*` prefix):
  - `VEGA_AUTH0_DOMAIN` (e.g. `mustafan4x.us.auth0.com`).
  - `VEGA_AUTH0_AUDIENCE` (e.g. `vega-api`).
  - Production fail loud: both must be set when `VEGA_ENVIRONMENT=production`. Pattern matches the existing `_validate_production` in `app/core/config.py`.
- No local user table. The JWT `sub` claim (e.g. `google-oauth2|123456789`, `github|987654321`) is the user identity stored on the calculation rows. Auth0 owns the entire credential surface; Vega never sees passwords.

### Token verification details

- Library: `pyjwt[crypto]`. Modern, actively maintained, smaller footprint than `python-jose`, and bundles `cryptography` for RS256 verification via the extras flag.
- JWKS fetched from `https://<VEGA_AUTH0_DOMAIN>/.well-known/jwks.json` once at startup, cached in process memory. A simple TTL refresh (every 24 hours) handles Auth0's key rotation; on key miss the verifier refetches once before failing.
- Verifies: signature against the matching JWK by `kid`, `aud == VEGA_AUTH0_AUDIENCE`, `iss == https://<VEGA_AUTH0_DOMAIN>/`, `exp` not past, `nbf` and `iat` sane.

## Data model

One Alembic migration:

1. `TRUNCATE calculation_outputs, calculation_inputs CASCADE`. Drops all existing rows. Approved policy: clean slate (existing data is smoke test rows from Phases 6 to 11).
2. `ALTER TABLE calculation_inputs ADD COLUMN user_id VARCHAR(64) NOT NULL`. The Auth0 `sub` is at most 64 chars in practice (provider prefix plus opaque ID).
3. `CREATE INDEX ix_calculation_inputs_user_id_created_at ON calculation_inputs (user_id, created_at DESC)`. Replaces the default ordering scan with an index friendly `WHERE user_id = ? ORDER BY created_at DESC` for the History list.

ORM model `CalculationInput` (in `backend/app/db/models.py`) gains:

```python
user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=False)  # composite index above covers it
```

`CalculationOutput` is unchanged. Cross user isolation flows from the parent FK plus the `user_id` filter on the parent.

## API surface changes

### `POST /api/calculations`

- Adds `user_id: str = Depends(require_user)` to the function signature.
- Sets `record.user_id = user_id` on the new `CalculationInput`.
- Returns 401 on missing or invalid JWT.
- Existing rate limit unchanged (`12/minute` per IP).

### `GET /api/calculations`

- Adds `user_id: str = Depends(require_user)`.
- Both the count and the row query gain `WHERE user_id = :user_id`.
- Returns 401 on missing or invalid JWT.
- Existing rate limit unchanged (`60/minute` per IP).

### `GET /api/calculations/{id}`

- Adds `user_id: str = Depends(require_user)`.
- Lookup adds `AND user_id = :user_id`.
- Returns **404** (not 403) when the row exists but belongs to another user. This preserves the existing not found contract for unknown IDs and avoids leaking the existence of other users' calculations (IDOR mitigation; mirrors the standard pattern in the OWASP API Security Top 10 for object level authorization).
- Existing rate limit unchanged (`60/minute` per IP).

## Frontend changes (concrete file list)

| File | Change |
|---|---|
| `frontend/src/main.tsx` | Wrap `<App/>` in `<Auth0Provider>`. Add Vite env var validation. |
| `frontend/src/lib/api.ts` | Factor `authedFetch` wrapper that calls `getAccessTokenSilently()` and adds the bearer header. Route `fetchCalculations`, `fetchCalculation`, `saveCalculation` through it. Public endpoints (`/api/price`, `/api/heatmap`, `/api/tickers`, `/api/backtest`) stay on bare `fetch`. |
| `frontend/src/components/LayoutShell.tsx` | Add a sidebar footer block: when logged in, render avatar plus email plus "Sign out"; when logged out, render a "Sign in" button that fires `loginWithRedirect`. |
| `frontend/src/screens/HistoryScreen.tsx` | Top level branch on `isAuthenticated`. Logged out renders an empty state card "Sign in to see your saved calculations" with a sign in button. Logged in renders the existing list. |
| `frontend/src/screens/HeatMapScreen.tsx` (the `onSave` handler at line 105) | Click handler: if `isAuthenticated`, call `saveCalculation` directly (existing path). Else call `loginWithRedirect({ appState: { pendingSave: <payload> } })`. The disabled state on the button (`canSave`) gains a logged-out branch that reads "Sign in to save" rather than disabling. |
| `frontend/src/lib/auth-callback.tsx` (new) | Tiny route handler at `/callback`: process the SDK's redirect, read `appState.pendingSave`, replay the save once, clear it. The app is single route today; a manual `window.location.pathname === '/callback'` check in `App.tsx` is enough until a router is introduced. |

## Data flow

### Sign in

1. User clicks "Sign in" in the sidebar (or clicks Save / History while logged out).
2. SDK calls `loginWithRedirect()`. Browser redirects to Auth0 Universal Login.
3. User picks Google or GitHub. Auth0 handles the OAuth dance.
4. Auth0 redirects to `https://vega-2rd.pages.dev/callback?code=...`.
5. SDK exchanges the auth code for an access token plus refresh token.
6. The user lands back on the screen they came from (the SDK's `appState` carries the original location).

### Save (logged in)

1. User clicks Save on the heatmap.
2. Frontend calls `getAccessTokenSilently()` to get a fresh JWT.
3. `POST /api/calculations` with `Authorization: Bearer <jwt>`.
4. Backend verifies the token, extracts `sub`, writes the row with `user_id = sub`, returns the new `calculation_id`.

### Save (logged out, the "try then sign up" funnel)

1. User clicks Save.
2. SDK fires `loginWithRedirect({ appState: { pendingSave: <heatmapPayload> } })`.
3. After Auth0 returns to `/callback`, the redirect handler reads `appState.pendingSave`, replays the save automatically, clears the `appState`.
4. User sees the heatmap saved with no second click.

### History

- Logged in: `GET /api/calculations` with bearer, render the list, click a row to fetch `GET /api/calculations/{id}`, render the saved grid (existing UI).
- Logged out: empty state card with "Sign in to see your saved calculations". Nav item stays visible.

### Sign out

1. User clicks the sidebar avatar dropdown's "Sign out".
2. SDK calls `logout({ logoutParams: { returnTo: window.location.origin } })`.
3. Auth0 invalidates its session, redirects back to the homepage.
4. Frontend clears the in memory token. Refresh token cookie is wiped by Auth0's logout endpoint.

## Error handling

| Condition | Behavior |
|---|---|
| JWT missing | 401, `{"detail": "Authentication required."}`. No echo of which header was missing. |
| JWT signature invalid, wrong `aud`, wrong `iss`, expired | 401, same generic message. No detail leakage. |
| Token exchange or refresh fails on the SDK side | SDK throws; the `<Auth0Provider>` boundary surfaces it; frontend renders a toast "Sign in failed, try again" plus a retry button. |
| IDOR attempt (`GET /api/calculations/{id}` for someone else's row) | 404, matches the existing not found contract; does not leak existence. |
| Auth0 outage | Gated endpoints return 401 because the SDK cannot fetch a token. Public endpoints keep working. The History screen empty state swaps to "Sign in is temporarily unavailable; please try again in a minute" when `getAccessTokenSilently()` rejects. |
| Rate limit | Existing per route caps unchanged; per IP, not per user. |

## Testing

### Backend

- `tests/api/test_auth.py` (new): JWKS verification happy path, expired JWT (401), wrong audience (401), wrong issuer (401), unsigned token (401), missing token (401).
- `tests/api/test_calculations.py` (update): every existing test gains a "logged in via fake JWT" fixture. New tests:
  - Cross user isolation: user A cannot read user B's calculation; `GET /api/calculations/{id}` returns 404.
  - List filter: user A's `GET /api/calculations` excludes user B's rows; total count is filtered.
  - Write attribution: a `POST` from user A's token writes a row whose `user_id == A.sub`.
- JWT test fixture: build tokens signed with a per test RSA key pair. Monkey patch the backend's JWKS loader in tests to return that public key. Auth0 itself is never hit during tests. The fixture ships in `tests/conftest.py` for shared use.

### Frontend

- `<Auth0Provider>` mocked via `@auth0/auth0-react` test utilities (the package exports a `useAuth0` mock helper). All component tests stub `isAuthenticated`, `getAccessTokenSilently`, and `loginWithRedirect`.
- `HistoryScreen.test.tsx` (update): logged out renders empty state; logged in renders the list and `fetchCalculations` is called with a bearer token in the headers.
- Heatmap save site test (update): logged out click fires `loginWithRedirect`; logged in click calls `saveCalculation` with the bearer.
- `auth-callback.test.tsx` (new): the `appState.pendingSave` replay path happens once and is cleared.

### Test budget

Existing 312 backend plus 120 frontend tests must continue to pass. New test count estimate: roughly 12 new backend tests (auth dependency suite plus calculation isolation) and roughly 6 new frontend tests (auth state branches). Final counts confirmed at implementation close.

## Threat model addendum

`docs/security/threat-model.md` gets a new STRIDE pass for the auth surface:

| Category | Threat | Mitigation |
|---|---|---|
| Spoofing | Impersonate another user | JWT signature verification against Auth0 JWKS. |
| Tampering | Modify token payload | JWT signature; backend re verifies on every request. |
| Repudiation | Deny saving a calculation | Out of scope; existing structured logs already capture request IDs. |
| Information disclosure | Read another user's saved calc | `WHERE user_id = ?` on every query plus IDOR returns 404. |
| Denial of service | Flood saves under one account | Existing per route per IP rate limits unchanged. Per user rate limits explicit non goal for v1. |
| Elevation of privilege | Gain admin powers | No roles in the system. Every authenticated user has the same scope (their own calculations). |

New residual risk: refresh token cookie is set by Auth0's domain, so its security posture is Auth0's responsibility. Vega cannot harden it further; this is documented in the residuals table at the bottom of `docs/security/threat-model.md`.

## Phase model and operational changes

- `STATUS.md` gains a row: **Phase 12, Authentication and per user history, status `not started`, window cost `~1 full window`**. The "Next phase" header switches from "v1 is shipped" to Phase 12.
- The natural pause point inside the window, if needed: after backend tests pass and before the frontend SDK is wired. That commit is a clean checkpoint (the API has the new gates, the frontend still works against the old unauth'd endpoints because the gated endpoints are now 401, but the public endpoints are unaffected). The Resume notes section of `STATUS.md` records the commit ref if we pause.
- `docs/setup-guide.md` gains an "Auth0 setup" section listing the Application type (SPA), API audience, callback URLs (`http://localhost:5173/callback` for dev, `https://vega-2rd.pages.dev/callback` for prod), and the four Vite env vars plus the two `VEGA_AUTH0_*` env vars on Render.
- `_headers` (Cloudflare Pages) updates: CSP `connect-src` adds `https://<tenant>.auth0.com`. Other directives unchanged.
- `pip-audit` and `pnpm audit` must stay clean after the new dependency adds (`pyjwt[crypto]` or `python-jose`, plus `@auth0/auth0-react`).

## Acceptance criteria

The phase ships when all of these hold:

1. A logged out visitor can use the Pricer, Heatmap, Greeks, Model Compare, and Backtest screens with no behavior change versus today.
2. A logged out visitor clicks Save on the heatmap, completes Auth0 login (Google or GitHub), lands back on the heatmap screen, and the calculation is saved (no second click required).
3. A logged in visitor's History screen lists only their own saved calculations.
4. A logged in visitor cannot read another user's saved calculation by guessing the UUID (returns 404).
5. The full backend test suite plus the full frontend test suite pass.
6. `pip-audit` and `pnpm audit` clean.
7. Code Reviewer signs off on the PR.
8. Security Engineer signs off on the threat model addendum.
9. `STATUS.md` Phase 12 row marked completed; token usage tracker has a Phase 12 block.
