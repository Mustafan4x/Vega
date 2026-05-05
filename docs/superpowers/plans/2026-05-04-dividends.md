# Dividends (continuous yield q) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add continuous dividend yield `q` as a first-class input across all three pricers, all four pricing endpoints, the persistence schema, every frontend form that takes pricing inputs, and the Greeks panel (which gains a sixth row, `psi`). Default `q = 0.0` everywhere preserves v1 behavior bit-for-bit.

**Architecture:** Bottom-up TDD. Math kernels first (each pricer takes `q`, validated against a small set of new Hull reference cases). Then the API layer (`PriceRequest`, `HeatmapRequest`, `BacktestPayload` each gain `q`; `PriceResponse.GreeksDisplay` gains `psi_per_pct`). Then persistence (`CalculationInput.q` column with Alembic migration that backfills existing rows to `0.0`). Then frontend (`InputForm`, `HeatMapControls`, `BacktestForm`, `GreeksPanel`, `HistoryScreen`). Finally docs and verification. One feature branch (`dividends-q`, already created), one PR, admin merge per CLAUDE.md push protocol.

**Tech Stack:** Python 3.12 + FastAPI + Pydantic + SQLAlchemy 2.x + Alembic + numpy + uv on the backend; React 18 + Vite + TypeScript + Tailwind + Vitest + Testing Library on the frontend. No new dependencies.

**Branch:** `dividends-q` (already exists; commit `4ce9be8` is the design spec).

**Spec:** `docs/superpowers/specs/2026-05-04-dividends-design.md`.

**Baseline test counts (must hold or grow):** backend 329 pass; frontend 127 pass.

---

## File map

**Math layer (modify):**
- `backend/app/pricing/black_scholes.py`
- `backend/app/pricing/black_scholes_vec.py`
- `backend/app/pricing/binomial.py`
- `backend/app/pricing/monte_carlo.py`

**API layer (modify):**
- `backend/app/api/price.py`
- `backend/app/api/heatmap.py`
- `backend/app/api/calculations.py`
- `backend/app/api/backtest.py`

**Backtest engine (modify):**
- `backend/app/backtest/engine.py`

**Persistence (modify + create):**
- `backend/app/db/models.py` (modify)
- `backend/alembic/versions/<rev>_add_q_to_calculation_inputs.py` (create)

**Backend tests (modify):**
- `backend/tests/pricing/test_black_scholes_math.py`
- `backend/tests/pricing/test_greeks.py`
- `backend/tests/pricing/test_black_scholes_vec.py`
- `backend/tests/pricing/test_binomial.py`
- `backend/tests/pricing/test_monte_carlo.py`
- `backend/tests/api/test_price.py`
- `backend/tests/api/test_heatmap.py`
- `backend/tests/api/test_calculations.py`
- `backend/tests/api/test_backtest.py`
- `backend/tests/backtest/test_engine.py` (or whatever the existing file is named)
- `backend/tests/db/test_models.py`

**Frontend (modify):**
- `frontend/src/lib/api.ts`
- `frontend/src/components/InputForm.tsx`
- `frontend/src/components/InputForm.test.tsx`
- `frontend/src/components/HeatMapControls.tsx`
- `frontend/src/components/HeatMapControls.test.tsx`
- `frontend/src/components/BacktestForm.tsx`
- `frontend/src/components/BacktestForm.test.tsx`
- `frontend/src/components/GreeksPanel.tsx`
- `frontend/src/components/GreeksPanel.test.tsx`
- `frontend/src/screens/HeatMapScreen.tsx` (caller adjustments only)
- `frontend/src/screens/HistoryScreen.tsx`
- `frontend/src/screens/HistoryScreen.test.tsx`

**Docs (modify + create):**
- `docs/math/black-scholes.md` (modify)
- `docs/risk/conventions.md` (modify)
- `docs/api.md` (modify)
- `docs/adr/0005-dividends-as-continuous-yield.md` (create)
- `future-ideas.md` (modify, gitignored)

---

## Conventions and reference values

**Hull reference cases for `q != 0`** (used across the math tests). Computed from Hull 10e Chapter 17 with the dividend-adjusted formulas; verified analytically. Keep these constants in one shared module-level block per test file so the tests are easy to audit.

```
Case A: S=100, K=100, T=1, r=0.05, sigma=0.20, q=0.03
  call ≈ 9.2270   put ≈ 6.3294
  d1 = (ln(1) + (0.05 - 0.03 + 0.5*0.04)*1) / (0.20*1) = 0.2000
  d2 = 0.0000

Case B: S=42, K=40, T=0.5, r=0.10, sigma=0.20, q=0.02
  call ≈ 4.4998   put ≈ 1.1419

Case C: S=100, K=110, T=0.25, r=0.05, sigma=0.30, q=0.05
  call ≈ 2.6283   put ≈ 11.4928

Case D: S=80, K=70, T=2.0, r=0.04, sigma=0.25, q=-0.01  (negative q)
  call ≈ 17.4869  put ≈ 2.4093
```

The implementer MUST recompute these to ~5 significant figures before pinning them in test code. Do not trust the values above blindly: use the formulas in the spec section "Math layer" plus a Python REPL with `math.exp`, `math.log`, `math.sqrt`, and `math.erf` to verify each pair. Pin only after the Risk Reviewer's eyeball check during local development.

**Tolerances** (match the project's existing conventions in the same files):
- Closed-form BS: `pytest.approx(expected, abs=1e-6)`.
- Greeks at the canonical reference: `abs=1e-3` (matches existing `REF_*` constant style).
- Binomial vs BS convergence: `abs=0.01` at 500 steps (matches existing test).
- Monte Carlo vs BS convergence: `abs=0.05` at 100k paths (matches existing test).
- Parity: `abs=1e-9`.

**TDD discipline:** every task that adds behavior writes a failing test first, runs it to confirm failure, implements minimally, runs to confirm pass, then commits. Tasks that purely rename or reshape existing code may skip the failing-test step but must still run the existing suite to confirm no regression before committing.

**Commit message style:** lower case, present tense, one line. No `Co-Authored-By`, no Generated-with-Claude footer (per `CLAUDE.md`). Example: `dividends: add q to black_scholes scalar pricer and reference tests`.

---

## Task 0: Open the work, confirm baseline

**Files:**
- None (sanity checks only).

- [ ] **Step 1: Verify branch and clean state.**

```bash
git status
git branch --show-current
```

Expected: `dividends-q` is the current branch; working tree clean (the design spec was committed in `4ce9be8`).

- [ ] **Step 2: Verify backend baseline test count.**

```bash
uv --project backend run pytest -q 2>&1 | tail -5
```

Expected: 329 passed (the post-Phase-12 baseline per `STATUS.md`).

- [ ] **Step 3: Verify frontend baseline test count.**

```bash
pnpm --filter frontend test --run 2>&1 | tail -10
```

Expected: 127 passed.

- [ ] **Step 4: No commit. Move to Task 1.**

---

## Task 1: Black Scholes scalar pricer accepts `q`

**Files:**
- Modify: `backend/app/pricing/black_scholes.py` (lines 40-109; `_validate_inputs`, `black_scholes_call`, `black_scholes_put`, the `_greeks_components` helper signature)
- Test: `backend/tests/pricing/test_black_scholes_math.py`

- [ ] **Step 1: Write the failing reference-value test.**

Append to `backend/tests/pricing/test_black_scholes_math.py` (above the put-call parity section):

```python
# =============================================================================
# Continuous dividend yield (q != 0): Hull 10e Chapter 17 reference values
# =============================================================================

@pytest.mark.parametrize(
    "S, K, T, r, sigma, q, expected_call, expected_put",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.03, 9.2270, 6.3294),
        (42.0, 40.0, 0.5, 0.10, 0.20, 0.02, 4.4998, 1.1419),
        (100.0, 110.0, 0.25, 0.05, 0.30, 0.05, 2.6283, 11.4928),
        (80.0, 70.0, 2.0, 0.04, 0.25, -0.01, 17.4869, 2.4093),
    ],
)
def test_call_put_with_dividend_yield(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float,
    expected_call: float,
    expected_put: float,
) -> None:
    """Hull 10e Chapter 17 closed-form values with continuous dividend yield."""
    call = black_scholes_call(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
    put = black_scholes_put(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
    assert call == pytest.approx(expected_call, abs=1e-4)
    assert put == pytest.approx(expected_put, abs=1e-4)


def test_q_zero_matches_no_dividend_path() -> None:
    """q == 0.0 is bit-identical to omitting q (default value preserved)."""
    no_q = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20)
    with_q_zero = black_scholes_call(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, q=0.0)
    assert no_q == with_q_zero
```

- [ ] **Step 2: Run the new test, verify failure.**

```bash
uv --project backend run pytest backend/tests/pricing/test_black_scholes_math.py::test_call_put_with_dividend_yield -v
```

Expected: FAIL with `TypeError: black_scholes_call() got an unexpected keyword argument 'q'` (or similar).

- [ ] **Step 3: Implement `q` in the scalar pricer.**

Edit `backend/app/pricing/black_scholes.py`. Three changes:

1. Extend `_validate_inputs` signature to accept `q` (the kernel only checks finiteness; the API layer enforces bounds):

```python
def _validate_inputs(S: float, K: float, T: float, sigma: float, q: float) -> None:
    if S < 0:
        raise ValueError(f"S must be non negative, got S={S}")
    if K <= 0:
        raise ValueError(f"K must be strictly positive (the formula divides by K), got K={K}")
    if T < 0:
        raise ValueError(f"T must be non negative, got T={T}")
    if sigma < 0:
        raise ValueError(f"sigma must be non negative, got sigma={sigma}")
    if not math.isfinite(q):
        raise ValueError(f"q must be finite, got q={q}")
```

2. Replace `black_scholes_call`:

```python
def black_scholes_call(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0
) -> float:
    """Price a European call option under the Black Scholes model.

    See ``docs/math/black-scholes.md`` for the formula, conventions, and edge cases.
    Continuous dividend yield ``q`` defaults to 0 to preserve pre-feature behavior.
    """
    _validate_inputs(S, K, T, sigma, q)

    if T == 0.0:
        return max(S - K, 0.0)

    discounted_strike = K * math.exp(-r * T)
    fwd_S = S * math.exp(-q * T)

    if S == 0.0:
        return 0.0

    if sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return max(fwd_S - discounted_strike, 0.0)

    sigma_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return fwd_S * _norm_cdf(d1) - discounted_strike * _norm_cdf(d2)
```

3. Replace `black_scholes_put`:

```python
def black_scholes_put(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0
) -> float:
    """Price a European put option under the Black Scholes model.

    See ``docs/math/black-scholes.md`` for the formula, conventions, and edge cases.
    Continuous dividend yield ``q`` defaults to 0 to preserve pre-feature behavior.
    """
    _validate_inputs(S, K, T, sigma, q)

    if T == 0.0:
        return max(K - S, 0.0)

    discounted_strike = K * math.exp(-r * T)
    fwd_S = S * math.exp(-q * T)

    if S == 0.0:
        return discounted_strike

    if sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return max(discounted_strike - fwd_S, 0.0)

    sigma_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return discounted_strike * _norm_cdf(-d2) - fwd_S * _norm_cdf(-d1)
```

- [ ] **Step 4: Run the new test, verify pass.**

```bash
uv --project backend run pytest backend/tests/pricing/test_black_scholes_math.py::test_call_put_with_dividend_yield backend/tests/pricing/test_black_scholes_math.py::test_q_zero_matches_no_dividend_path -v
```

Expected: 5 passed (4 parametrized cases + the q=0 equivalence).

- [ ] **Step 5: Run the whole BS scalar test file to confirm no regression.**

```bash
uv --project backend run pytest backend/tests/pricing/test_black_scholes_math.py -q
```

Expected: All previously passing tests still pass; new tests pass.

- [ ] **Step 6: Commit.**

```bash
git add backend/app/pricing/black_scholes.py backend/tests/pricing/test_black_scholes_math.py
git commit -m "dividends: add q parameter to black_scholes call and put with hull reference tests"
```

---

## Task 2: Black Scholes Greeks accept `q` and gain `psi`

**Files:**
- Modify: `backend/app/pricing/black_scholes.py` (the `Greeks` dataclass, `_greeks_components`, `_zero_greeks`, `black_scholes_call_greeks`, `black_scholes_put_greeks`)
- Test: `backend/tests/pricing/test_greeks.py`

- [ ] **Step 1: Write failing tests for psi and dividend-modified Greeks.**

Append to `backend/tests/pricing/test_greeks.py`:

```python
# =============================================================================
# Continuous dividend yield (q != 0): psi and dividend-adjusted Greeks
# =============================================================================

# Reference inputs with dividend: S=K=100, T=1, r=0.05, sigma=0.20, q=0.03.
# d1 = (ln(1) + (0.05 - 0.03 + 0.5*0.04)*1) / (0.20*1) = 0.2000
# d2 = 0.0000
# N(0.20) ≈ 0.5793   N(-0.20) ≈ 0.4207
# phi(0.20) ≈ 0.3910
# exp(-q*T) = exp(-0.03) ≈ 0.9704
# exp(-r*T) = exp(-0.05) ≈ 0.9512
# psi_call = -T * S * exp(-q*T) * N(d1) = -1 * 100 * 0.9704 * 0.5793 ≈ -56.221
# psi_put  =  T * S * exp(-q*T) * N(-d1) = 1 * 100 * 0.9704 * 0.4207 ≈ 40.825

REF_DIV_INPUTS = (100.0, 100.0, 1.0, 0.05, 0.20, 0.03)
REF_DIV_CALL_DELTA = 0.5623   # exp(-q*T) * N(d1) ≈ 0.9704 * 0.5793
REF_DIV_PUT_DELTA = -0.4081   # exp(-q*T) * (N(d1) - 1) ≈ 0.9704 * (-0.4207)
REF_DIV_PSI_CALL = -56.221
REF_DIV_PSI_PUT = 40.825


def test_call_psi_at_dividend_reference() -> None:
    g = black_scholes_call_greeks(*REF_DIV_INPUTS)
    assert g.psi == pytest.approx(REF_DIV_PSI_CALL, abs=1e-2)


def test_put_psi_at_dividend_reference() -> None:
    g = black_scholes_put_greeks(*REF_DIV_INPUTS)
    assert g.psi == pytest.approx(REF_DIV_PSI_PUT, abs=1e-2)


def test_call_delta_at_dividend_reference() -> None:
    g = black_scholes_call_greeks(*REF_DIV_INPUTS)
    assert g.delta == pytest.approx(REF_DIV_CALL_DELTA, abs=1e-3)


def test_put_delta_at_dividend_reference() -> None:
    g = black_scholes_put_greeks(*REF_DIV_INPUTS)
    assert g.delta == pytest.approx(REF_DIV_PUT_DELTA, abs=1e-3)


def test_psi_zero_when_q_zero() -> None:
    """psi == 0 reduces gracefully when q == 0 because the underlying derivative
    is still defined; psi is just the analytical formula evaluated at q=0,
    which is non-zero. This test checks the formula reduces correctly:
    psi_call(q=0) == -T * S * N(d1) at standard inputs."""
    g = black_scholes_call_greeks(100.0, 100.0, 1.0, 0.05, 0.20, q=0.0)
    # d1 at q=0, S=K=100, T=1, r=0.05, sigma=0.20 = 0.35; N(0.35) ≈ 0.6368
    # psi_call(q=0) = -1 * 100 * 1 * 0.6368 = -63.68
    assert g.psi == pytest.approx(-63.68, abs=0.05)


def test_q_zero_greeks_match_no_dividend_path() -> None:
    """All five existing Greeks at q=0 are bit-identical to omitting q."""
    no_q = black_scholes_call_greeks(100.0, 100.0, 1.0, 0.05, 0.20)
    with_q = black_scholes_call_greeks(100.0, 100.0, 1.0, 0.05, 0.20, q=0.0)
    assert no_q.delta == with_q.delta
    assert no_q.gamma == with_q.gamma
    assert no_q.vega == with_q.vega
    assert no_q.theta == with_q.theta
    assert no_q.rho == with_q.rho
```

Then update the existing parity test in the same file to cover `q != 0`. Replace the `test_put_call_parity_for_call_price` parametrize block with one that adds a `q` axis:

```python
@pytest.mark.parametrize(
    "S, K, T, r, sigma, q",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.0),
        (42.0, 40.0, 0.5, 0.10, 0.20, 0.02),
        (52.0, 50.0, 0.25, 0.12, 0.30, 0.05),
        (80.0, 70.0, 2.0, 0.04, 0.25, -0.01),
    ],
)
def test_put_call_parity_for_call_price(
    S: float, K: float, T: float, r: float, sigma: float, q: float
) -> None:
    """Put call parity with continuous dividend yield:
    C - P == S * exp(-q*T) - K * exp(-r*T) within 1e-9.
    """
    call = black_scholes_call(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
    put = black_scholes_put(S=S, K=K, T=T, r=r, sigma=sigma, q=q)
    expected = S * math.exp(-q * T) - K * math.exp(-r * T)
    assert (call - put) == pytest.approx(expected, abs=1e-9)
```

(Locate the existing test at `test_greeks.py:97`. Use Read first to see its exact current form before editing.)

Also update `test_put_call_delta_relationship` (same file, around line 116) so the relationship `delta_call - delta_put == exp(-q*T)` is asserted (it equals 1 when q==0):

```python
@pytest.mark.parametrize(
    "S, K, T, r, sigma, q",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.0),
        (42.0, 40.0, 0.5, 0.10, 0.20, 0.02),
        (52.0, 50.0, 0.25, 0.12, 0.30, 0.05),
    ],
)
def test_put_call_delta_relationship(
    S: float, K: float, T: float, r: float, sigma: float, q: float
) -> None:
    """delta_call - delta_put == exp(-q*T) (reduces to 1 when q==0)."""
    call_g = black_scholes_call_greeks(S, K, T, r, sigma, q)
    put_g = black_scholes_put_greeks(S, K, T, r, sigma, q)
    assert (call_g.delta - put_g.delta) == pytest.approx(math.exp(-q * T), abs=1e-9)
```

- [ ] **Step 2: Run the new tests, verify failure.**

```bash
uv --project backend run pytest backend/tests/pricing/test_greeks.py -v 2>&1 | tail -30
```

Expected: failures referencing `'Greeks' object has no attribute 'psi'` and `unexpected keyword argument 'q'`.

- [ ] **Step 3: Update the `Greeks` dataclass and helpers.**

Edit `backend/app/pricing/black_scholes.py`:

```python
@dataclass(frozen=True)
class Greeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    psi: float
```

```python
def _greeks_components(
    S: float, K: float, T: float, r: float, sigma: float, q: float
) -> tuple[float, float, float, float, float]:
    """Return (d1, d2, N'(d1), discounted_strike, fwd_S)."""
    sigma_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / sigma_sqrt_t
    d2 = d1 - sigma_sqrt_t
    return d1, d2, _norm_pdf(d1), K * math.exp(-r * T), S * math.exp(-q * T)
```

```python
def _zero_greeks() -> Greeks:
    return Greeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0, rho=0.0, psi=0.0)
```

- [ ] **Step 4: Update `black_scholes_call_greeks` and `black_scholes_put_greeks`.**

```python
def black_scholes_call_greeks(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0
) -> Greeks:
    """Closed form Greeks for a European call. Math units (see module docstring)."""
    _validate_inputs(S, K, T, sigma, q)
    if T == 0.0 or S == 0.0 or sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return _zero_greeks()

    d1, d2, npdf_d1, discounted_strike, fwd_S = _greeks_components(S, K, T, r, sigma, q)
    sqrt_t = math.sqrt(T)

    delta = math.exp(-q * T) * _norm_cdf(d1)
    gamma = math.exp(-q * T) * npdf_d1 / (S * sigma * sqrt_t)
    vega = fwd_S * sqrt_t * npdf_d1
    theta = (
        -fwd_S * npdf_d1 * sigma / (2.0 * sqrt_t)
        - r * discounted_strike * _norm_cdf(d2)
        + q * fwd_S * _norm_cdf(d1)
    )
    rho = T * discounted_strike * _norm_cdf(d2)
    psi = -T * fwd_S * _norm_cdf(d1)
    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho, psi=psi)


def black_scholes_put_greeks(
    S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0
) -> Greeks:
    """Closed form Greeks for a European put. Math units (see module docstring)."""
    _validate_inputs(S, K, T, sigma, q)
    if T == 0.0 or S == 0.0 or sigma <= _SIGMA_DETERMINISTIC_THRESHOLD:
        return _zero_greeks()

    d1, d2, npdf_d1, discounted_strike, fwd_S = _greeks_components(S, K, T, r, sigma, q)
    sqrt_t = math.sqrt(T)

    delta = math.exp(-q * T) * (_norm_cdf(d1) - 1.0)
    gamma = math.exp(-q * T) * npdf_d1 / (S * sigma * sqrt_t)
    vega = fwd_S * sqrt_t * npdf_d1
    theta = (
        -fwd_S * npdf_d1 * sigma / (2.0 * sqrt_t)
        + r * discounted_strike * _norm_cdf(-d2)
        - q * fwd_S * _norm_cdf(-d1)
    )
    rho = -T * discounted_strike * _norm_cdf(-d2)
    psi = T * fwd_S * _norm_cdf(-d1)
    return Greeks(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho, psi=psi)
```

- [ ] **Step 5: Run the Greeks tests, verify pass.**

```bash
uv --project backend run pytest backend/tests/pricing/test_greeks.py -v 2>&1 | tail -40
```

Expected: all pass, including the new psi tests, the q=0 equivalence test, and the updated parity/delta-relationship tests.

- [ ] **Step 6: Commit.**

```bash
git add backend/app/pricing/black_scholes.py backend/tests/pricing/test_greeks.py
git commit -m "dividends: add psi greek and q parameter to black_scholes greeks"
```

---

## Task 3: Vectorized Black Scholes accepts `q`

**Files:**
- Modify: `backend/app/pricing/black_scholes_vec.py`
- Test: `backend/tests/pricing/test_black_scholes_vec.py`

- [ ] **Step 1: Read the existing `test_black_scholes_vec.py` to find the cell-for-cell parity test.**

```bash
grep -n "def test\|scalar\|matches" backend/tests/pricing/test_black_scholes_vec.py | head -20
```

Note the function name(s) used to assert "vec matches scalar" so the new test follows the same naming.

- [ ] **Step 2: Write the failing test that exercises q != 0 in the vec path.**

Append to `backend/tests/pricing/test_black_scholes_vec.py`:

```python
@pytest.mark.parametrize("q", [0.0, 0.02, 0.05, -0.01])
def test_vec_matches_scalar_with_dividend_yield(q: float) -> None:
    """Cell for cell parity between vectorized and scalar BS for non zero q."""
    S_axis = np.array([80.0, 100.0, 120.0])
    sigma_axis = np.array([0.15, 0.20, 0.30])
    K, T, r = 100.0, 1.0, 0.05

    call_vec = black_scholes_call_vec(S_axis, K, T, r, sigma_axis, q=q)
    put_vec = black_scholes_put_vec(S_axis, K, T, r, sigma_axis, q=q)

    for i, sigma in enumerate(sigma_axis):
        for j, S in enumerate(S_axis):
            assert call_vec[i, j] == pytest.approx(
                black_scholes_call(float(S), K, T, r, float(sigma), q=q), abs=1e-9
            )
            assert put_vec[i, j] == pytest.approx(
                black_scholes_put(float(S), K, T, r, float(sigma), q=q), abs=1e-9
            )
```

If `numpy as np`, `pytest`, `black_scholes_call`, `black_scholes_put`, `black_scholes_call_vec`, and `black_scholes_put_vec` are not already imported at the top of the file, add them.

- [ ] **Step 3: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/pricing/test_black_scholes_vec.py::test_vec_matches_scalar_with_dividend_yield -v
```

Expected: FAIL with `unexpected keyword argument 'q'`.

- [ ] **Step 4: Implement `q` in `black_scholes_call_vec` and `black_scholes_put_vec`.**

Edit `backend/app/pricing/black_scholes_vec.py`. The change is: each function gains `q: float = 0.0` after `sigma_axis`, the call substitutes `S * exp(-q*T)` for the `fwd_S` term, and `d1` uses `(r - q + 0.5*sigma^2)*T` in the numerator.

Replace `black_scholes_call_vec` body from `# After _grid call`:

```python
def black_scholes_call_vec(
    S_axis: FloatArray | list[float],
    K: float,
    T: float,
    r: float,
    sigma_axis: FloatArray | list[float],
    q: float = 0.0,
) -> FloatArray:
    s_arr = np.asarray(S_axis, dtype=np.float64)
    sig_arr = np.asarray(sigma_axis, dtype=np.float64)
    _validate(s_arr, K, T, sig_arr)

    S, sigma = _grid(s_arr, sig_arr)

    if T == 0.0:
        return cast(FloatArray, np.maximum(S - K, 0.0) + np.zeros_like(sigma))

    discounted_strike = K * math.exp(-r * T)
    fwd_S = S * math.exp(-q * T)
    deterministic = np.maximum(fwd_S - discounted_strike, 0.0)
    deterministic = np.where(S == 0.0, 0.0, deterministic)

    sqrt_t = math.sqrt(T)
    sigma_safe = np.where(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, 1.0, sigma)
    S_safe = np.where(S == 0.0, 1.0, S)
    fwd_S_safe = S_safe * math.exp(-q * T)
    d1 = (
        np.log(S_safe / K) + (r - q + 0.5 * sigma_safe * sigma_safe) * T
    ) / (sigma_safe * sqrt_t)
    d2 = d1 - sigma_safe * sqrt_t
    bs_value = fwd_S_safe * _norm_cdf(d1) - discounted_strike * _norm_cdf(d2)

    out = np.broadcast_to(bs_value, (sig_arr.size, s_arr.size)).copy()
    sigma_zero = np.broadcast_to(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, out.shape)
    s_zero = np.broadcast_to(S == 0.0, out.shape)
    deterministic_grid = np.broadcast_to(deterministic, out.shape)
    return cast(FloatArray, np.where(sigma_zero | s_zero, deterministic_grid, out))
```

`black_scholes_put_vec` mirrors:

```python
def black_scholes_put_vec(
    S_axis: FloatArray | list[float],
    K: float,
    T: float,
    r: float,
    sigma_axis: FloatArray | list[float],
    q: float = 0.0,
) -> FloatArray:
    s_arr = np.asarray(S_axis, dtype=np.float64)
    sig_arr = np.asarray(sigma_axis, dtype=np.float64)
    _validate(s_arr, K, T, sig_arr)

    S, sigma = _grid(s_arr, sig_arr)

    if T == 0.0:
        return cast(FloatArray, np.maximum(K - S, 0.0) + np.zeros_like(sigma))

    discounted_strike = K * math.exp(-r * T)
    fwd_S = S * math.exp(-q * T)
    deterministic = np.maximum(discounted_strike - fwd_S, 0.0)
    deterministic = np.where(S == 0.0, discounted_strike, deterministic)

    sqrt_t = math.sqrt(T)
    sigma_safe = np.where(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, 1.0, sigma)
    S_safe = np.where(S == 0.0, 1.0, S)
    fwd_S_safe = S_safe * math.exp(-q * T)
    d1 = (
        np.log(S_safe / K) + (r - q + 0.5 * sigma_safe * sigma_safe) * T
    ) / (sigma_safe * sqrt_t)
    d2 = d1 - sigma_safe * sqrt_t
    bs_value = discounted_strike * _norm_cdf(-d2) - fwd_S_safe * _norm_cdf(-d1)

    out = np.broadcast_to(bs_value, (sig_arr.size, s_arr.size)).copy()
    sigma_zero = np.broadcast_to(sigma <= _SIGMA_DETERMINISTIC_THRESHOLD, out.shape)
    s_zero = np.broadcast_to(S == 0.0, out.shape)
    deterministic_grid = np.broadcast_to(deterministic, out.shape)
    return cast(FloatArray, np.where(sigma_zero | s_zero, deterministic_grid, out))
```

- [ ] **Step 5: Run, verify pass.**

```bash
uv --project backend run pytest backend/tests/pricing/test_black_scholes_vec.py -v
```

Expected: all pass, including all four parametrized q cases.

- [ ] **Step 6: Commit.**

```bash
git add backend/app/pricing/black_scholes_vec.py backend/tests/pricing/test_black_scholes_vec.py
git commit -m "dividends: add q to vectorized black_scholes pricer"
```

---

## Task 4: Binomial CRR pricer accepts `q`

**Files:**
- Modify: `backend/app/pricing/binomial.py`
- Test: `backend/tests/pricing/test_binomial.py`

- [ ] **Step 1: Write failing tests for binomial convergence with q != 0.**

Append to `backend/tests/pricing/test_binomial.py`:

```python
@pytest.mark.parametrize(
    "S, K, T, r, sigma, q",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.03),
        (100.0, 110.0, 0.25, 0.05, 0.30, 0.05),
        (80.0, 70.0, 2.0, 0.04, 0.25, -0.01),
    ],
)
def test_binomial_converges_to_bs_with_dividend_yield(
    S: float, K: float, T: float, r: float, sigma: float, q: float
) -> None:
    """At 500 steps, the CRR tree price agrees with closed form BS within 1 cent."""
    bs_call = black_scholes_call(S, K, T, r, sigma, q=q)
    bs_put = black_scholes_put(S, K, T, r, sigma, q=q)
    bn_call = binomial_call(S, K, T, r, sigma, q=q, steps=500)
    bn_put = binomial_put(S, K, T, r, sigma, q=q, steps=500)
    assert bn_call == pytest.approx(bs_call, abs=0.01)
    assert bn_put == pytest.approx(bs_put, abs=0.01)


def test_binomial_q_zero_matches_no_dividend_path() -> None:
    """q=0 keyword preserves pre-feature numerical results bit-for-bit."""
    no_q = binomial_call(100.0, 100.0, 1.0, 0.05, 0.20, steps=500)
    with_q = binomial_call(100.0, 100.0, 1.0, 0.05, 0.20, q=0.0, steps=500)
    assert no_q == with_q
```

If `black_scholes_call` and `black_scholes_put` are not already imported in this file, add them at the top:

```python
from app.pricing.black_scholes import black_scholes_call, black_scholes_put
```

- [ ] **Step 2: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/pricing/test_binomial.py::test_binomial_converges_to_bs_with_dividend_yield -v
```

Expected: FAIL with `unexpected keyword argument 'q'`.

- [ ] **Step 3: Implement q in binomial.py.**

Edit `backend/app/pricing/binomial.py`. Three changes:

1. Add `q: float = 0.0` to `binomial_call` and `binomial_put` signatures, threaded through to `_crr_price`.
2. Update `_crr_price`'s probability calculation: `a = math.exp((r - q) * dt)` instead of `math.exp(r * dt)`.
3. Update the `sigma == 0` deterministic branch: `forward = S * math.exp((r - q) * T)` instead of `S * math.exp(r * T)`.

Replace `_crr_price`:

```python
def _crr_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    steps: int,
    is_call: bool,
    q: float = 0.0,
) -> float:
    _validate(S, K, T, sigma, steps)

    if T == 0.0:
        return _intrinsic(S, K, is_call)

    if S == 0.0:
        return 0.0 if is_call else K * math.exp(-r * T)

    if sigma <= 1e-12:
        forward = S * math.exp((r - q) * T)
        intrinsic = forward - K if is_call else K - forward
        return max(intrinsic, 0.0) * math.exp(-r * T)

    dt = T / steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1.0 / u
    a = math.exp((r - q) * dt)
    p = (a - d) / (u - d)
    if not (0.0 < p < 1.0):
        forward = S * math.exp((r - q) * T)
        intrinsic = forward - K if is_call else K - forward
        return max(intrinsic, 0.0) * math.exp(-r * T)

    discount = math.exp(-r * dt)

    j = np.arange(steps + 1)
    terminal = S * (u ** (steps - j)) * (d**j)
    if is_call:
        values = np.maximum(terminal - K, 0.0)
    else:
        values = np.maximum(K - terminal, 0.0)

    for _ in range(steps):
        values = discount * (p * values[:-1] + (1.0 - p) * values[1:])

    return float(values[0])
```

Replace public `binomial_call` and `binomial_put`:

```python
def binomial_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    steps: int = DEFAULT_STEPS,
    q: float = 0.0,
) -> float:
    """Price a European call under the CRR binomial tree."""
    return _crr_price(S, K, T, r, sigma, steps, is_call=True, q=q)


def binomial_put(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    steps: int = DEFAULT_STEPS,
    q: float = 0.0,
) -> float:
    """Price a European put under the CRR binomial tree."""
    return _crr_price(S, K, T, r, sigma, steps, is_call=False, q=q)
```

- [ ] **Step 4: Run, verify pass.**

```bash
uv --project backend run pytest backend/tests/pricing/test_binomial.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add backend/app/pricing/binomial.py backend/tests/pricing/test_binomial.py
git commit -m "dividends: add q to binomial crr pricer"
```

---

## Task 5: Monte Carlo pricer accepts `q`

**Files:**
- Modify: `backend/app/pricing/monte_carlo.py`
- Test: `backend/tests/pricing/test_monte_carlo.py`

- [ ] **Step 1: Write failing test for MC convergence with q != 0.**

Append to `backend/tests/pricing/test_monte_carlo.py`:

```python
@pytest.mark.parametrize(
    "S, K, T, r, sigma, q",
    [
        (100.0, 100.0, 1.0, 0.05, 0.20, 0.03),
        (100.0, 110.0, 0.25, 0.05, 0.30, 0.05),
    ],
)
def test_monte_carlo_converges_to_bs_with_dividend_yield(
    S: float, K: float, T: float, r: float, sigma: float, q: float
) -> None:
    """100k paths with antithetic variates agree with closed form BS within 5 cents."""
    bs_call = black_scholes_call(S, K, T, r, sigma, q=q)
    bs_put = black_scholes_put(S, K, T, r, sigma, q=q)
    mc_call = monte_carlo_call(S, K, T, r, sigma, q=q, paths=100_000, seed=4242)
    mc_put = monte_carlo_put(S, K, T, r, sigma, q=q, paths=100_000, seed=4242)
    assert mc_call == pytest.approx(bs_call, abs=0.05)
    assert mc_put == pytest.approx(bs_put, abs=0.05)


def test_monte_carlo_q_zero_matches_no_dividend_path() -> None:
    """q=0 keyword preserves pre-feature numerical results bit-for-bit (same seed)."""
    no_q = monte_carlo_call(100.0, 100.0, 1.0, 0.05, 0.20, paths=100_000, seed=4242)
    with_q = monte_carlo_call(100.0, 100.0, 1.0, 0.05, 0.20, q=0.0, paths=100_000, seed=4242)
    assert no_q == with_q
```

If imports are missing add:

```python
from app.pricing.black_scholes import black_scholes_call, black_scholes_put
```

- [ ] **Step 2: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/pricing/test_monte_carlo.py::test_monte_carlo_converges_to_bs_with_dividend_yield -v
```

Expected: FAIL with `unexpected keyword argument 'q'`.

- [ ] **Step 3: Implement q in monte_carlo.py.**

Edit `backend/app/pricing/monte_carlo.py`. Three changes:

1. Add `q: float = 0.0` to public functions and `_mc_price`.
2. Update the `sigma == 0` deterministic branch: `forward = S * math.exp((r - q) * T)`.
3. Update the GBM drift: `drift = (r - q - 0.5 * sigma * sigma) * T`.

Replace `_mc_price`:

```python
def _mc_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    paths: int,
    seed: int | None,
    is_call: bool,
    q: float = 0.0,
) -> float:
    _validate(S, K, T, sigma, paths)

    if T == 0.0:
        return _intrinsic(S, K, is_call)

    if S == 0.0:
        return 0.0 if is_call else K * math.exp(-r * T)

    if sigma <= 1e-12:
        forward = S * math.exp((r - q) * T)
        intrinsic = forward - K if is_call else K - forward
        return max(intrinsic, 0.0) * math.exp(-r * T)

    half = (paths + 1) // 2
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(half)
    z_full = np.concatenate([z, -z])

    drift = (r - q - 0.5 * sigma * sigma) * T
    diffusion = sigma * math.sqrt(T)
    s_t = S * np.exp(drift + diffusion * z_full)

    payoff = np.maximum(s_t - K, 0.0) if is_call else np.maximum(K - s_t, 0.0)
    discounted = math.exp(-r * T) * float(np.mean(payoff))
    return discounted
```

Replace public functions:

```python
def monte_carlo_call(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    paths: int = DEFAULT_PATHS,
    seed: int | None = None,
    q: float = 0.0,
) -> float:
    """Price a European call by Monte Carlo (GBM, antithetic variates)."""
    return _mc_price(S, K, T, r, sigma, paths, seed, is_call=True, q=q)


def monte_carlo_put(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    *,
    paths: int = DEFAULT_PATHS,
    seed: int | None = None,
    q: float = 0.0,
) -> float:
    """Price a European put by Monte Carlo (GBM, antithetic variates)."""
    return _mc_price(S, K, T, r, sigma, paths, seed, is_call=False, q=q)
```

- [ ] **Step 4: Run, verify pass.**

```bash
uv --project backend run pytest backend/tests/pricing/test_monte_carlo.py -q
```

Expected: all pass.

- [ ] **Step 5: Run the full pricing test suite to confirm no regression across pricers.**

```bash
uv --project backend run pytest backend/tests/pricing/ -q
```

Expected: all pass; total count grew by the new tests added in Tasks 1 to 5.

- [ ] **Step 6: Commit.**

```bash
git add backend/app/pricing/monte_carlo.py backend/tests/pricing/test_monte_carlo.py
git commit -m "dividends: add q to monte carlo pricer"
```

---

## Task 6: `POST /api/price` exposes `q` and `psi_per_pct`

**Files:**
- Modify: `backend/app/api/price.py`
- Test: `backend/tests/api/test_price.py`

- [ ] **Step 1: Write failing tests for q validation and psi_per_pct in the response.**

Append to `backend/tests/api/test_price.py` (use the existing test conventions for the FastAPI client; check the file's first 30 lines if you are unsure of the client fixture name):

```python
def test_price_accepts_q_and_returns_psi_per_pct(client) -> None:
    payload = {
        "S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20, "q": 0.03,
    }
    res = client.post("/api/price", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["call"] == pytest.approx(9.227, abs=0.05)
    assert body["put"] == pytest.approx(6.329, abs=0.05)
    assert "psi_per_pct" in body["call_greeks"]
    assert "psi_per_pct" in body["put_greeks"]
    # psi for the call at the dividend reference is roughly -56.2 textbook units;
    # divided by 100 gives per-1%-q units.
    assert body["call_greeks"]["psi_per_pct"] == pytest.approx(-0.562, abs=0.005)
    assert body["put_greeks"]["psi_per_pct"] == pytest.approx(0.408, abs=0.005)


def test_price_q_defaults_to_zero(client) -> None:
    """Omitting q yields the same numbers as q=0.0 (backwards compat)."""
    payload = {"S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20}
    res_no_q = client.post("/api/price", json=payload).json()
    res_q_zero = client.post("/api/price", json={**payload, "q": 0.0}).json()
    assert res_no_q == res_q_zero


@pytest.mark.parametrize("bad_q", [1.5, -1.5, float("inf"), float("nan")])
def test_price_rejects_out_of_range_q(client, bad_q: float) -> None:
    payload = {"S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20, "q": bad_q}
    res = client.post("/api/price", json=payload)
    assert res.status_code == 422
```

If `pytest` is not yet imported in `test_price.py`, add `import pytest` at the top. Note: NaN and Infinity must be sent as JSON numbers; FastAPI rejects them at the JSON parsing layer because Pydantic's `allow_inf_nan=False` is set on the field. If the test client's JSON encoder rejects `float('nan')` or `float('inf')` before the request is sent, fall back to sending the raw string `'NaN'` / `'Infinity'` via `data=` and the appropriate content type, OR drop those two parametrize cases from this test (the bound check on `1.5` and `-1.5` already proves the validator is wired). Pick the approach that matches how other tests in this file handle non-finite values; do not invent a new pattern.

- [ ] **Step 2: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/api/test_price.py::test_price_accepts_q_and_returns_psi_per_pct -v
```

Expected: FAIL (the response has no `psi_per_pct`; payload field `q` may be accepted as extra and silently ignored, or rejected by `extra='forbid'`).

- [ ] **Step 3: Add q to PriceRequest, psi_per_pct to GreeksDisplay, thread through helpers.**

Edit `backend/app/api/price.py`:

1. In `PriceRequest`, add (after the `sigma` field):

```python
    q: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        allow_inf_nan=False,
        description="Continuous dividend yield (annualized, continuous).",
    )
```

2. In `GreeksDisplay`, add a field:

```python
    psi_per_pct: float
```

3. In `_to_display`, add the conversion:

```python
def _to_display(g: MathGreeks) -> GreeksDisplay:
    return GreeksDisplay(
        delta=g.delta,
        gamma=g.gamma,
        theta_per_day=g.theta / 365.0,
        vega_per_pct=g.vega * 0.01,
        rho_per_pct=g.rho * 0.01,
        psi_per_pct=g.psi * 0.01,
    )
```

4. Replace `_price_call_put` to thread `q`:

```python
def _price_call_put(
    model: PricingModel,
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    q: float,
) -> tuple[float, float]:
    if model == "black_scholes":
        return (
            black_scholes_call(S, K, T, r, sigma, q=q),
            black_scholes_put(S, K, T, r, sigma, q=q),
        )
    if model == "binomial":
        return (
            binomial_call(S, K, T, r, sigma, q=q, steps=_BINOMIAL_STEPS),
            binomial_put(S, K, T, r, sigma, q=q, steps=_BINOMIAL_STEPS),
        )
    return (
        monte_carlo_call(S, K, T, r, sigma, q=q, paths=_MC_PATHS, seed=_MC_SEED),
        monte_carlo_put(S, K, T, r, sigma, q=q, paths=_MC_PATHS, seed=_MC_SEED),
    )
```

5. Replace the `price` handler:

```python
@router.post("/price", response_model=PriceResponse)
def price(payload: PriceRequest) -> PriceResponse:
    call, put = _price_call_put(
        payload.model, payload.S, payload.K, payload.T, payload.r, payload.sigma, payload.q
    )
    call_g = black_scholes_call_greeks(
        payload.S, payload.K, payload.T, payload.r, payload.sigma, q=payload.q
    )
    put_g = black_scholes_put_greeks(
        payload.S, payload.K, payload.T, payload.r, payload.sigma, q=payload.q
    )
    return PriceResponse(
        call=call,
        put=put,
        model=payload.model,
        call_greeks=_to_display(call_g),
        put_greeks=_to_display(put_g),
    )
```

- [ ] **Step 4: Run, verify pass.**

```bash
uv --project backend run pytest backend/tests/api/test_price.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add backend/app/api/price.py backend/tests/api/test_price.py
git commit -m "dividends: add q to /api/price request and psi_per_pct to greeks display"
```

---

## Task 7: `POST /api/heatmap` accepts `q`

**Files:**
- Modify: `backend/app/api/heatmap.py`
- Test: `backend/tests/api/test_heatmap.py`

- [ ] **Step 1: Write failing tests.**

Append to `backend/tests/api/test_heatmap.py`:

```python
def test_heatmap_accepts_q_and_shifts_values(client) -> None:
    """Same heatmap with q=0.05 produces lower call values than q=0."""
    base = {
        "S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20,
        "vol_shock": [-0.5, 0.5], "spot_shock": [-0.2, 0.2],
        "rows": 5, "cols": 5,
    }
    no_div = client.post("/api/heatmap", json=base).json()
    with_div = client.post("/api/heatmap", json={**base, "q": 0.05}).json()
    # Center cell call value with q=0.05 should be strictly less than with q=0.
    assert with_div["call"][2][2] < no_div["call"][2][2]


def test_heatmap_q_defaults_to_zero(client) -> None:
    base = {
        "S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20,
        "vol_shock": [-0.5, 0.5], "spot_shock": [-0.2, 0.2],
        "rows": 5, "cols": 5,
    }
    res_no_q = client.post("/api/heatmap", json=base).json()
    res_q_zero = client.post("/api/heatmap", json={**base, "q": 0.0}).json()
    assert res_no_q == res_q_zero


@pytest.mark.parametrize("bad_q", [1.5, -1.5])
def test_heatmap_rejects_out_of_range_q(client, bad_q: float) -> None:
    payload = {
        "S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20,
        "vol_shock": [-0.5, 0.5], "spot_shock": [-0.2, 0.2],
        "rows": 5, "cols": 5, "q": bad_q,
    }
    res = client.post("/api/heatmap", json=payload)
    assert res.status_code == 422
```

- [ ] **Step 2: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/api/test_heatmap.py::test_heatmap_accepts_q_and_shifts_values -v
```

Expected: FAIL (q not yet on the request model; values may even compare equal because q is silently ignored).

- [ ] **Step 3: Implement.**

Edit `backend/app/api/heatmap.py`:

1. Add `q` to `HeatmapRequest` after `sigma`:

```python
    q: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        allow_inf_nan=False,
        description="Continuous dividend yield (annualized, continuous).",
    )
```

2. Update the three grid helpers and `_grid_for_model` to accept and thread `q`:

```python
def _grid_black_scholes(
    spot_axis: np.ndarray, sigma_axis: np.ndarray, K: float, T: float, r: float, q: float
) -> tuple[np.ndarray, np.ndarray]:
    call = black_scholes_call_vec(spot_axis, K, T, r, sigma_axis, q=q)
    put = black_scholes_put_vec(spot_axis, K, T, r, sigma_axis, q=q)
    return call, put


def _grid_binomial(
    spot_axis: np.ndarray, sigma_axis: np.ndarray, K: float, T: float, r: float, q: float
) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = sigma_axis.size, spot_axis.size
    call = np.zeros((rows, cols))
    put = np.zeros((rows, cols))
    for i in range(rows):
        for j in range(cols):
            call[i, j] = binomial_call(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                steps=_HEATMAP_BINOMIAL_STEPS,
            )
            put[i, j] = binomial_put(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                steps=_HEATMAP_BINOMIAL_STEPS,
            )
    return call, put


def _grid_monte_carlo(
    spot_axis: np.ndarray, sigma_axis: np.ndarray, K: float, T: float, r: float, q: float
) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = sigma_axis.size, spot_axis.size
    call = np.zeros((rows, cols))
    put = np.zeros((rows, cols))
    for i in range(rows):
        for j in range(cols):
            cell_seed = _HEATMAP_MC_SEED + i * MAX_DIMENSION + j
            call[i, j] = monte_carlo_call(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                paths=_HEATMAP_MC_PATHS,
                seed=cell_seed,
            )
            put[i, j] = monte_carlo_put(
                float(spot_axis[j]),
                K,
                T,
                r,
                float(sigma_axis[i]),
                q=q,
                paths=_HEATMAP_MC_PATHS,
                seed=cell_seed,
            )
    return call, put


def _grid_for_model(
    model: PricingModel,
    spot_axis: np.ndarray,
    sigma_axis: np.ndarray,
    K: float,
    T: float,
    r: float,
    q: float,
) -> tuple[np.ndarray, np.ndarray]:
    if model == "black_scholes":
        return _grid_black_scholes(spot_axis, sigma_axis, K, T, r, q)
    if model == "binomial":
        return _grid_binomial(spot_axis, sigma_axis, K, T, r, q)
    return _grid_monte_carlo(spot_axis, sigma_axis, K, T, r, q)
```

3. Update the `heatmap` handler to pass `payload.q`:

```python
    call, put = _grid_for_model(
        payload.model, spot_axis, sigma_axis, payload.K, payload.T, payload.r, payload.q
    )
```

- [ ] **Step 4: Run, verify pass.**

```bash
uv --project backend run pytest backend/tests/api/test_heatmap.py -q
```

Expected: all pass.

- [ ] **Step 5: Commit.**

```bash
git add backend/app/api/heatmap.py backend/tests/api/test_heatmap.py
git commit -m "dividends: add q to /api/heatmap request and thread to all three pricers"
```

---

## Task 8: Backtest engine and `POST /api/backtest` accept `q`

**Files:**
- Modify: `backend/app/backtest/engine.py`
- Modify: `backend/app/api/backtest.py`
- Test: `backend/tests/backtest/test_engine.py` (or whatever file currently tests `run_backtest`)
- Test: `backend/tests/api/test_backtest.py`

- [ ] **Step 1: Locate the existing engine test file.**

```bash
ls backend/tests/backtest/
```

If the file is named differently (e.g. `test_run_backtest.py`), use that name in steps 2 to 6 below.

- [ ] **Step 2: Write failing engine tests for q.**

Append to the engine test file:

```python
def test_run_backtest_accepts_q_and_lowers_long_call_basis() -> None:
    """A positive q lowers the entry basis for a long call (the underlying drifts
    slower under the dividend-adjusted measure, so the option is cheaper)."""
    req_no_div = BacktestRequest(
        strategy=Strategy.LONG_CALL,
        dates=("2025-01-02", "2025-01-03", "2025-01-06"),
        closes=(100.0, 101.0, 102.0),
        sigma=0.20,
        r=0.05,
        dte_days=30,
    )
    req_with_div = BacktestRequest(
        strategy=Strategy.LONG_CALL,
        dates=("2025-01-02", "2025-01-03", "2025-01-06"),
        closes=(100.0, 101.0, 102.0),
        sigma=0.20,
        r=0.05,
        dte_days=30,
        q=0.05,
    )
    res_no_div = run_backtest(req_no_div)
    res_with_div = run_backtest(req_with_div)
    assert res_with_div.entry_basis < res_no_div.entry_basis


def test_run_backtest_q_zero_matches_no_q() -> None:
    common = dict(
        strategy=Strategy.LONG_CALL,
        dates=("2025-01-02", "2025-01-03", "2025-01-06"),
        closes=(100.0, 101.0, 102.0),
        sigma=0.20,
        r=0.05,
        dte_days=30,
    )
    no_q = run_backtest(BacktestRequest(**common))
    with_q = run_backtest(BacktestRequest(**common, q=0.0))
    assert no_q.entry_basis == with_q.entry_basis
    assert no_q.position_value == with_q.position_value
```

If `BacktestRequest`, `Strategy`, `run_backtest` are not already imported, add them at the top:

```python
from app.backtest.engine import BacktestRequest, Strategy, run_backtest
```

- [ ] **Step 3: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/backtest/ -k "q" -v
```

Expected: FAIL (`BacktestRequest()` does not accept `q`).

- [ ] **Step 4: Update `BacktestRequest`, `_validate`, `_leg_value`, `run_backtest`.**

Edit `backend/app/backtest/engine.py`:

1. `BacktestRequest`:

```python
@dataclass(frozen=True)
class BacktestRequest:
    strategy: Strategy
    dates: tuple[str, ...]
    closes: tuple[float, ...]
    sigma: float
    r: float
    dte_days: int
    q: float = 0.0
```

2. `_validate` adds the q bound check (after the existing `r` check):

```python
    if req.q < -1.0 or req.q > 1.0:
        raise ValueError(f"q out of supported range, got q={req.q}.")
    if not math.isfinite(req.q):
        raise ValueError(f"q must be finite, got q={req.q}.")
```

3. `_leg_value` signature gains `q`:

```python
def _leg_value(
    leg: Leg, S: float, K: float, T: float, r: float, sigma: float, q: float
) -> float:
    if leg.kind == "call":
        v = black_scholes_call(S, K, T, r, sigma, q=q)
    elif leg.kind == "put":
        v = black_scholes_put(S, K, T, r, sigma, q=q)
    else:
        raise ValueError(f"unknown leg kind: {leg.kind!r}")
    return leg.sign * v
```

4. `run_backtest` threads `req.q`:

```python
def run_backtest(req: BacktestRequest) -> BacktestResult:
    _validate(req)

    legs = STRATEGY_LEGS[req.strategy]
    entry_close = req.closes[0]
    entry_date = date.fromisoformat(req.dates[0])
    expiry_date = entry_date + timedelta(days=req.dte_days)
    K = entry_close

    T_entry = req.dte_days / DAYS_PER_YEAR
    entry_basis = 0.0
    for leg in legs:
        entry_basis += _leg_value(leg, entry_close, K, T_entry, req.r, req.sigma, req.q)

    dates_out: list[str] = []
    spot_out: list[float] = []
    position_out: list[float] = []
    pnl_out: list[float] = []
    for date_iso, close in zip(req.dates, req.closes, strict=True):
        d = date.fromisoformat(date_iso)
        days_remaining = (expiry_date - d).days
        T = max(days_remaining, 0) / DAYS_PER_YEAR
        position_value = 0.0
        for leg in legs:
            position_value += _leg_value(leg, close, K, T, req.r, req.sigma, req.q)
        dates_out.append(date_iso)
        spot_out.append(close)
        position_out.append(position_value)
        pnl_out.append(position_value - entry_basis)

    return BacktestResult(
        strategy=req.strategy,
        legs=legs,
        dates=tuple(dates_out),
        spot=tuple(spot_out),
        position_value=tuple(position_out),
        pnl=tuple(pnl_out),
        strike=K,
        entry_basis=entry_basis,
        entry_date=req.dates[0],
        expiry_date=expiry_date.isoformat(),
    )
```

- [ ] **Step 5: Run engine tests.**

```bash
uv --project backend run pytest backend/tests/backtest/ -q
```

Expected: all pass.

- [ ] **Step 6: Write failing API tests for q on /api/backtest.**

Append to `backend/tests/api/test_backtest.py`:

```python
def test_backtest_accepts_q(client, monkeypatch) -> None:
    """Smoke test: q is accepted by the API and threaded into the engine.

    Reuse whatever historical-lookup mock the existing tests use; do not hit
    yfinance from a unit test.
    """
    # IMPORTANT: copy the historical-lookup override pattern from an existing
    # passing test in this file (e.g. test_backtest_returns_pnl). Do not
    # invent a new override pattern here.
    payload = {
        "symbol": "AAPL",
        "strategy": "long_call",
        "start_date": "2025-01-02",
        "end_date": "2025-01-06",
        "sigma": 0.20,
        "r": 0.05,
        "dte_days": 30,
        "q": 0.03,
    }
    res = client.post("/api/backtest", json=payload)
    assert res.status_code == 200


def test_backtest_q_defaults_to_zero(client, monkeypatch) -> None:
    """Omitting q keeps the same numerical result as q=0 for the same inputs."""
    base = {
        "symbol": "AAPL",
        "strategy": "long_call",
        "start_date": "2025-01-02",
        "end_date": "2025-01-06",
        "sigma": 0.20,
        "r": 0.05,
        "dte_days": 30,
    }
    res_no_q = client.post("/api/backtest", json=base).json()
    res_q_zero = client.post("/api/backtest", json={**base, "q": 0.0}).json()
    assert res_no_q == res_q_zero


@pytest.mark.parametrize("bad_q", [1.5, -1.5])
def test_backtest_rejects_out_of_range_q(client, bad_q: float) -> None:
    payload = {
        "symbol": "AAPL",
        "strategy": "long_call",
        "start_date": "2025-01-02",
        "end_date": "2025-01-06",
        "sigma": 0.20,
        "r": 0.05,
        "dte_days": 30,
        "q": bad_q,
    }
    res = client.post("/api/backtest", json=payload)
    assert res.status_code == 422
```

Read the current `test_backtest.py` to find the historical-lookup mock fixture (likely a `dependency_overrides` setup or a monkeypatch on `get_default_historical_lookup`). Use the same pattern in the two smoke tests above.

- [ ] **Step 7: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/api/test_backtest.py -k "q" -v
```

Expected: FAIL on the first two tests (`q` rejected as extra by `extra='forbid'`).

- [ ] **Step 8: Update `BacktestPayload` and the handler in `backend/app/api/backtest.py`.**

Add `q` to `BacktestPayload` after `r`:

```python
    q: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        allow_inf_nan=False,
        description="Continuous dividend yield (annualized, continuous).",
    )
```

Update the `EngineRequest(...)` construction inside the handler to include `q=payload.q`:

```python
        result = run_backtest(
            EngineRequest(
                strategy=payload.strategy,
                dates=series.dates,
                closes=series.closes,
                sigma=payload.sigma,
                r=payload.r,
                dte_days=payload.dte_days,
                q=payload.q,
            )
        )
```

- [ ] **Step 9: Run, verify pass.**

```bash
uv --project backend run pytest backend/tests/api/test_backtest.py -q
```

Expected: all pass.

- [ ] **Step 10: Commit.**

```bash
git add backend/app/backtest/engine.py backend/app/api/backtest.py backend/tests/backtest/ backend/tests/api/test_backtest.py
git commit -m "dividends: add q to backtest engine and /api/backtest endpoint"
```

---

## Task 9: Persistence: `q` column on `calculation_inputs` plus migration

**Files:**
- Modify: `backend/app/db/models.py`
- Create: `backend/alembic/versions/<rev>_add_q_to_calculation_inputs.py`
- Test: `backend/tests/db/test_models.py`

- [ ] **Step 1: Read the existing Phase 12 migration as a template.**

```bash
cat backend/alembic/versions/3c1e7a3e9d78_phase12_user_id_and_per_user_index.py
```

Note the import style, the `op.add_column` / `op.drop_column` pattern, the `down_revision` pointer, and how it handles SQLite (the project uses SQLite in tests, Postgres in production).

- [ ] **Step 2: Generate a new Alembic revision.**

```bash
cd backend && uv run alembic revision -m "add q to calculation_inputs"
cd ..
```

This creates a new file under `backend/alembic/versions/`. Note its full filename (the autogenerated prefix is unique).

- [ ] **Step 3: Fill in the new migration body.**

Edit the new revision file. Replace its `upgrade` and `downgrade` functions:

```python
def upgrade() -> None:
    op.add_column(
        "calculation_inputs",
        sa.Column("q", sa.Float(), server_default="0.0", nullable=False),
    )


def downgrade() -> None:
    with op.batch_alter_table("calculation_inputs") as batch_op:
        batch_op.drop_column("q")
```

The `batch_alter_table` in `downgrade` is needed for SQLite (which cannot drop a column without rebuilding the table); Postgres handles either form. The Phase 12 migration's note on this still applies.

Confirm `down_revision` points at the most recent existing revision (`3c1e7a3e9d78` per the file we read in Step 1; double-check by running `uv run alembic history` from `backend/`).

- [ ] **Step 4: Update `CalculationInput` in `backend/app/db/models.py`.**

After the `cols` field and before `user_id`, add:

```python
    q: Mapped[float] = mapped_column(Float, nullable=False, server_default="0.0")
```

- [ ] **Step 5: Write a failing migration test.**

Append to `backend/tests/db/test_models.py`:

```python
def test_calculation_input_has_q_column_with_zero_default(session) -> None:
    """A new CalculationInput row without an explicit q gets q == 0.0 from the
    server default. Existing rows from before the migration are backfilled
    to 0.0 by the same default."""
    record = CalculationInput(
        id="00000000-0000-0000-0000-000000000001",
        s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.20,
        vol_shock_min=-0.5, vol_shock_max=0.5,
        spot_shock_min=-0.2, spot_shock_max=0.2,
        rows=5, cols=5,
        user_id="auth0|test",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    assert record.q == 0.0


def test_calculation_input_q_round_trips(session) -> None:
    record = CalculationInput(
        id="00000000-0000-0000-0000-000000000002",
        s=100.0, k=100.0, t=1.0, r=0.05, sigma=0.20,
        vol_shock_min=-0.5, vol_shock_max=0.5,
        spot_shock_min=-0.2, spot_shock_max=0.2,
        rows=5, cols=5,
        q=0.03,
        user_id="auth0|test",
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    assert record.q == 0.03
```

If `CalculationInput` is not imported, add `from app.db import CalculationInput`. If a `session` fixture does not exist in this file's `conftest.py`, copy the pattern used by adjacent tests; do not invent a new fixture.

- [ ] **Step 6: Run, verify failure (the column does not exist yet at the SQLite level).**

```bash
uv --project backend run pytest backend/tests/db/test_models.py -q
```

Expected: FAIL (the column is on the model but the test SQLite schema may need re-creation; the test fixture should call `Base.metadata.create_all`, which the model change makes adequate).

If the test fixture runs migrations instead of `create_all`, the migration must be applied; verify by checking the conftest for the db tests.

- [ ] **Step 7: Run the migration locally to verify it applies cleanly.**

```bash
cd backend && uv run alembic upgrade head && cd ..
```

Expected: the new revision applies without error.

- [ ] **Step 8: Re-run the db tests, verify pass.**

```bash
uv --project backend run pytest backend/tests/db/test_models.py -q
```

Expected: all pass.

- [ ] **Step 9: Commit.**

```bash
git add backend/app/db/models.py backend/alembic/versions/ backend/tests/db/test_models.py
git commit -m "dividends: add q column to calculation_inputs with backfill-zero migration"
```

---

## Task 10: `POST /api/calculations` captures `q`; list/detail echo it

**Files:**
- Modify: `backend/app/api/calculations.py`
- Test: `backend/tests/api/test_calculations.py`

- [ ] **Step 1: Write failing tests.**

Append to `backend/tests/api/test_calculations.py` (use the existing `auth_headers` and `client` fixtures):

```python
def test_create_calculation_persists_q(client, auth_headers) -> None:
    payload = {
        "S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20, "q": 0.03,
        "vol_shock": [-0.5, 0.5], "spot_shock": [-0.2, 0.2],
        "rows": 3, "cols": 3,
    }
    create_res = client.post("/api/calculations", json=payload, headers=auth_headers)
    assert create_res.status_code == 201
    calc_id = create_res.json()["calculation_id"]

    detail_res = client.get(f"/api/calculations/{calc_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["q"] == pytest.approx(0.03, abs=1e-9)


def test_list_calculations_includes_q(client, auth_headers) -> None:
    payload = {
        "S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20, "q": 0.025,
        "vol_shock": [-0.5, 0.5], "spot_shock": [-0.2, 0.2],
        "rows": 3, "cols": 3,
    }
    client.post("/api/calculations", json=payload, headers=auth_headers)
    res = client.get("/api/calculations", headers=auth_headers).json()
    assert any(item["q"] == pytest.approx(0.025, abs=1e-9) for item in res["items"])


def test_calculation_q_defaults_to_zero(client, auth_headers) -> None:
    """Save without q; detail returns q == 0.0."""
    payload = {
        "S": 100.0, "K": 100.0, "T": 1.0, "r": 0.05, "sigma": 0.20,
        "vol_shock": [-0.5, 0.5], "spot_shock": [-0.2, 0.2],
        "rows": 3, "cols": 3,
    }
    create_res = client.post("/api/calculations", json=payload, headers=auth_headers)
    calc_id = create_res.json()["calculation_id"]
    detail_res = client.get(f"/api/calculations/{calc_id}", headers=auth_headers)
    assert detail_res.json()["q"] == 0.0
```

- [ ] **Step 2: Run, verify failure.**

```bash
uv --project backend run pytest backend/tests/api/test_calculations.py -k "q" -v
```

Expected: FAIL (response body has no `q` key; persistence does not write `q`).

- [ ] **Step 3: Implement.**

Edit `backend/app/api/calculations.py`:

1. Add `q: float` to `CalculationDetail` and `CalculationSummary` (after `sigma`):

```python
class CalculationDetail(BaseModel):
    calculation_id: str
    s: float
    k: float
    t: float
    r: float
    sigma: float
    q: float
    rows: int
    cols: int
    call: list[list[float]]
    put: list[list[float]]
    sigma_axis: list[float]
    spot_axis: list[float]


class CalculationSummary(BaseModel):
    calculation_id: str
    created_at: str
    s: float
    k: float
    t: float
    r: float
    sigma: float
    q: float
    rows: int
    cols: int
```

2. In `create_calculation`, capture `payload.q` on the `CalculationInput`:

```python
    record = CalculationInput(
        id=calc_id,
        s=payload.S,
        k=payload.K,
        t=payload.T,
        r=payload.r,
        sigma=payload.sigma,
        q=payload.q,
        vol_shock_min=payload.vol_shock[0],
        vol_shock_max=payload.vol_shock[1],
        spot_shock_min=payload.spot_shock[0],
        spot_shock_max=payload.spot_shock[1],
        rows=payload.rows,
        cols=payload.cols,
        user_id=user_id,
    )
```

   Also pass `q=payload.q` into the two `black_scholes_*_vec` calls so the persisted grid is computed under the requested dividend yield:

```python
    call = black_scholes_call_vec(
        spot_axis, payload.K, payload.T, payload.r, sigma_axis, q=payload.q
    )
    put = black_scholes_put_vec(
        spot_axis, payload.K, payload.T, payload.r, sigma_axis, q=payload.q
    )
```

3. In `list_calculations`, echo `q` in the `CalculationSummary`:

```python
    items = [
        CalculationSummary(
            calculation_id=row.id,
            created_at=row.created_at.isoformat() if row.created_at is not None else "",
            s=row.s,
            k=row.k,
            t=row.t,
            r=row.r,
            sigma=row.sigma,
            q=row.q,
            rows=row.rows,
            cols=row.cols,
        )
        for row in rows
    ]
```

4. In `read_calculation`, echo `q` in the `CalculationDetail`:

```python
    return CalculationDetail(
        calculation_id=record.id,
        s=record.s,
        k=record.k,
        t=record.t,
        r=record.r,
        sigma=record.sigma,
        q=record.q,
        rows=record.rows,
        cols=record.cols,
        call=call_grid,
        put=put_grid,
        sigma_axis=sigma_axis,
        spot_axis=spot_axis,
    )
```

- [ ] **Step 4: Run, verify pass.**

```bash
uv --project backend run pytest backend/tests/api/test_calculations.py -q
```

Expected: all pass.

- [ ] **Step 5: Run the full backend suite to confirm no regression.**

```bash
uv --project backend run pytest -q 2>&1 | tail -5
```

Expected: count >= 329 + (sum of new tests added in Tasks 1-10), all pass.

- [ ] **Step 6: Commit.**

```bash
git add backend/app/api/calculations.py backend/tests/api/test_calculations.py
git commit -m "dividends: persist q on /api/calculations and echo in list and detail"
```

---

## Task 11: Frontend api types extend `q`

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Read the file to identify the request and response types to extend.**

```bash
grep -n "interface\|type \|export " frontend/src/lib/api.ts | head -40
```

- [ ] **Step 2: Extend each request type with `q?: number` and each response type that gains `q` or `psi_per_pct`.**

Add `q?: number` to the four request types: the price request type, the heatmap request type, the calculation save type (if separate), and the backtest request type.

Add `q: number` to the calculation detail and calculation summary response types.

Add `psi_per_pct: number` to the GreeksDisplay response type.

Use Read to find the exact names; do not guess. The naming is consistent with the API field names.

- [ ] **Step 3: No new test file; the api types are exercised by every component test in subsequent tasks.**

- [ ] **Step 4: Run frontend type check to confirm the type changes compile.**

```bash
pnpm --filter frontend tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 5: Commit.**

```bash
git add frontend/src/lib/api.ts
git commit -m "dividends: extend frontend api types with q and psi_per_pct"
```

---

## Task 12: `InputForm` adds `q` field

**Files:**
- Modify: `frontend/src/components/InputForm.tsx`
- Test: `frontend/src/components/InputForm.test.tsx`

- [ ] **Step 1: Write failing test.**

Append to `frontend/src/components/InputForm.test.tsx`:

```tsx
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { InputForm } from './InputForm'

describe('InputForm dividend yield', () => {
  it('renders a Dividend Yield (q) field', () => {
    const onChange = vi.fn()
    const onCalculate = vi.fn()
    render(
      <InputForm
        inputs={{ S: 100, K: 100, T: 1, r: 0.05, sigma: 0.2, q: 0 }}
        invalid={new Set()}
        pending={false}
        onChange={onChange}
        onCalculate={onCalculate}
      />
    )
    expect(screen.getByLabelText(/Dividend Yield \(q\)/i)).toBeInTheDocument()
  })

  it('converts percent input to decimal on change', () => {
    const onChange = vi.fn()
    const onCalculate = vi.fn()
    render(
      <InputForm
        inputs={{ S: 100, K: 100, T: 1, r: 0.05, sigma: 0.2, q: 0 }}
        invalid={new Set()}
        pending={false}
        onChange={onChange}
        onCalculate={onCalculate}
      />
    )
    const qInput = screen.getByLabelText(/Dividend Yield \(q\)/i) as HTMLInputElement
    fireEvent.change(qInput, { target: { value: '3' } })
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ q: expect.closeTo(0.03, 6) })
    )
  })
})
```

If the existing tests in `InputForm.test.tsx` use a different convention (e.g. `expect.toBe` instead of `closeTo`), match it. Read the file first.

- [ ] **Step 2: Run, verify failure.**

```bash
pnpm --filter frontend test --run InputForm.test.tsx
```

Expected: FAIL (no `q` field in the component; `inputs` prop doesn't accept `q`).

- [ ] **Step 3: Update `InputForm.tsx`.**

Add the q field after the r field:

```tsx
<NumField
  label="Dividend Yield (q)"
  suffix="%"
  value={Number((inputs.q * 100).toFixed(3))}
  invalid={invalid.has('q')}
  onChange={(v) => setField('q', v / 100)}
/>
```

- [ ] **Step 4: Run, verify pass.**

```bash
pnpm --filter frontend test --run InputForm.test.tsx
```

Expected: pass, including the existing tests in this file.

- [ ] **Step 5: Commit.**

```bash
git add frontend/src/components/InputForm.tsx frontend/src/components/InputForm.test.tsx
git commit -m "dividends: add q field to inputform with percent to decimal conversion"
```

---

## Task 13: `GreeksPanel` renders `psi` row

**Files:**
- Modify: `frontend/src/components/GreeksPanel.tsx`
- Test: `frontend/src/components/GreeksPanel.test.tsx`

- [ ] **Step 1: Read the existing `GreeksPanel.tsx` and `GreeksPanel.test.tsx` to understand the row pattern and test fixtures.**

```bash
sed -n '1,80p' frontend/src/components/GreeksPanel.tsx
sed -n '1,60p' frontend/src/components/GreeksPanel.test.tsx
```

Note how the five existing rows are rendered (likely a hardcoded list of `{label, value, suffix}` triples or a per-Greek block). Mirror that pattern for `psi`.

- [ ] **Step 2: Write failing test.**

Append to `GreeksPanel.test.tsx`:

```tsx
it('renders a psi row for the call greek', () => {
  render(
    <GreeksPanel
      callGreeks={{
        delta: 0.6, gamma: 0.02, theta_per_day: -0.02, vega_per_pct: 0.4,
        rho_per_pct: 0.5, psi_per_pct: -0.56,
      }}
      putGreeks={{
        delta: -0.4, gamma: 0.02, theta_per_day: -0.005, vega_per_pct: 0.4,
        rho_per_pct: -0.4, psi_per_pct: 0.41,
      }}
    />
  )
  expect(screen.getAllByText(/psi/i).length).toBeGreaterThanOrEqual(1)
})

it('formats psi_per_pct with the per 1% q label', () => {
  render(
    <GreeksPanel
      callGreeks={{
        delta: 0.6, gamma: 0.02, theta_per_day: -0.02, vega_per_pct: 0.4,
        rho_per_pct: 0.5, psi_per_pct: -0.56,
      }}
      putGreeks={{
        delta: -0.4, gamma: 0.02, theta_per_day: -0.005, vega_per_pct: 0.4,
        rho_per_pct: -0.4, psi_per_pct: 0.41,
      }}
    />
  )
  // Whichever assertion the file already uses for "per 1% r" on rho, mirror
  // it here for "per 1% q" on psi. If the existing rho test uses
  // getByText(/per 1% r/i), do the same with /per 1% q/i.
  expect(screen.getAllByText(/per 1% q/i).length).toBeGreaterThanOrEqual(1)
})
```

If the existing tests use a different prop shape or name (e.g. they pass a single `prices` object), mirror that.

- [ ] **Step 3: Run, verify failure.**

```bash
pnpm --filter frontend test --run GreeksPanel.test.tsx
```

Expected: FAIL (no psi row).

- [ ] **Step 4: Add the psi row to `GreeksPanel.tsx`.**

Replicate the existing rho row pattern with:
- label: `psi`
- value: `callGreeks.psi_per_pct` (and `putGreeks.psi_per_pct`)
- suffix: `per 1% q`

If the panel uses a hardcoded array of metric specs, append a new entry. If it uses one JSX block per Greek, append a new block at the bottom of the existing five.

- [ ] **Step 5: Run, verify pass.**

```bash
pnpm --filter frontend test --run GreeksPanel.test.tsx
```

Expected: pass.

- [ ] **Step 6: Commit.**

```bash
git add frontend/src/components/GreeksPanel.tsx frontend/src/components/GreeksPanel.test.tsx
git commit -m "dividends: add psi row to greeks panel"
```

---

## Task 14: `HeatMapControls` (and `HeatMapScreen` wiring) add `q` field

**Files:**
- Modify: `frontend/src/components/HeatMapControls.tsx`
- Test: `frontend/src/components/HeatMapControls.test.tsx`
- Modify: `frontend/src/screens/HeatMapScreen.tsx` (if it owns the inputs state shape)

- [ ] **Step 1: Read the components and screen to find the inputs state shape and where the q field will live.**

```bash
grep -n "interface\|type\|sigma\|r:\|S:" frontend/src/components/HeatMapControls.tsx | head -20
grep -n "useState\|HeatmapRequest\|inputs" frontend/src/screens/HeatMapScreen.tsx | head -10
```

- [ ] **Step 2: Write a failing test for the q field in HeatMapControls.**

Append to `HeatMapControls.test.tsx`:

```tsx
it('renders a Dividend Yield (q) field that converts percent to decimal on change', () => {
  // Mirror the prop shape of the existing tests in this file. Confirm by
  // reading the file's first test before writing this one.
  const onChange = vi.fn()
  render(/* ... existing fixture but with q: 0 in the inputs ... */)
  const qInput = screen.getByLabelText(/Dividend Yield \(q\)/i) as HTMLInputElement
  fireEvent.change(qInput, { target: { value: '5' } })
  expect(onChange).toHaveBeenCalledWith(
    expect.objectContaining({ q: expect.closeTo(0.05, 6) })
  )
})
```

- [ ] **Step 3: Run, verify failure.**

```bash
pnpm --filter frontend test --run HeatMapControls.test.tsx
```

- [ ] **Step 4: Add the q field to HeatMapControls.tsx.**

Mirror the InputForm pattern from Task 12: a NumField for `q`, percent-to-decimal at the boundary.

- [ ] **Step 5: Update HeatMapScreen.tsx.**

If `HeatMapScreen.tsx` initializes the inputs state shape, add `q: 0` to the initial state. If it constructs the request object before calling the API, ensure `q` is passed through.

- [ ] **Step 6: Run, verify pass.**

```bash
pnpm --filter frontend test --run HeatMapControls.test.tsx
pnpm --filter frontend test --run HeatMapScreen.test.tsx
```

- [ ] **Step 7: Commit.**

```bash
git add frontend/src/components/HeatMapControls.tsx frontend/src/components/HeatMapControls.test.tsx frontend/src/screens/HeatMapScreen.tsx
git commit -m "dividends: add q field to heatmap controls and wire through screen"
```

---

## Task 15: `BacktestForm` adds `q` field

**Files:**
- Modify: `frontend/src/components/BacktestForm.tsx`
- Test: `frontend/src/components/BacktestForm.test.tsx`

- [ ] **Step 1: Read the form and test to see the existing field pattern.**

```bash
grep -n "label=\|onChange\|inputs" frontend/src/components/BacktestForm.tsx | head -20
```

- [ ] **Step 2: Write failing test for the q field.**

Append to `BacktestForm.test.tsx`:

```tsx
it('renders a Dividend Yield (q) field that converts percent to decimal on change', () => {
  const onChange = vi.fn()
  // Mirror existing test scaffold; pass q: 0 in the inputs.
  render(/* ... */)
  const qInput = screen.getByLabelText(/Dividend Yield \(q\)/i) as HTMLInputElement
  fireEvent.change(qInput, { target: { value: '4' } })
  expect(onChange).toHaveBeenCalledWith(
    expect.objectContaining({ q: expect.closeTo(0.04, 6) })
  )
})
```

- [ ] **Step 3: Run, verify failure.**

```bash
pnpm --filter frontend test --run BacktestForm.test.tsx
```

- [ ] **Step 4: Add the q field to `BacktestForm.tsx` next to r.**

Same NumField pattern as InputForm.

- [ ] **Step 5: Run, verify pass.**

- [ ] **Step 6: Commit.**

```bash
git add frontend/src/components/BacktestForm.tsx frontend/src/components/BacktestForm.test.tsx
git commit -m "dividends: add q field to backtest form"
```

---

## Task 16: `HistoryScreen` renders `q` in summary card and detail view

**Files:**
- Modify: `frontend/src/screens/HistoryScreen.tsx`
- Test: `frontend/src/screens/HistoryScreen.test.tsx`

- [ ] **Step 1: Read the existing summary card and detail view markup.**

```bash
grep -n "sigma\|r:\|toFixed\|%" frontend/src/screens/HistoryScreen.tsx | head -30
```

Note the percent formatting used for `r` and `sigma`. Mirror it for `q`.

- [ ] **Step 2: Write failing tests.**

Append to `HistoryScreen.test.tsx`:

```tsx
it('renders q in the summary card as a percent', () => {
  // Use the existing mock for the calculations list endpoint; add a `q: 0.025`
  // field to one of the items so we can assert on it.
  // ...
  expect(screen.getByText(/2\.5%/)).toBeInTheDocument()
})

it('renders q in the detail view as a percent including 0.0%', () => {
  // ...
  expect(screen.getByText(/0\.0%/)).toBeInTheDocument()
})
```

The existing tests in this file mock `fetchCalculations` and `fetchCalculation`; mirror their setup. Read the file's first test to confirm the mock shape, including what `q` values to inject.

- [ ] **Step 3: Run, verify failure.**

```bash
pnpm --filter frontend test --run HistoryScreen.test.tsx
```

- [ ] **Step 4: Update HistoryScreen.tsx to render q.**

In whichever JSX block renders the summary fields for each item:

```tsx
<dt>q</dt>
<dd>{`${(item.q * 100).toFixed(1)}%`}</dd>
```

In the detail view block, mirror the same.

- [ ] **Step 5: Run, verify pass.**

- [ ] **Step 6: Commit.**

```bash
git add frontend/src/screens/HistoryScreen.tsx frontend/src/screens/HistoryScreen.test.tsx
git commit -m "dividends: render q in history summary card and detail view"
```

---

## Task 17: Docs (math, conventions, api, ADR)

**Files:**
- Modify: `docs/math/black-scholes.md`
- Modify: `docs/risk/conventions.md`
- Modify: `docs/api.md`
- Create: `docs/adr/0005-dividends-as-continuous-yield.md`

- [ ] **Step 1: Append a "Continuous dividend yield" section to `docs/math/black-scholes.md`.**

Read the existing file first to match its tone and section structure. The new section should include:

- The substitution `S → S * exp(-q*T)` in d1 and d2.
- The full call/put formulas with q.
- The full Greek formulas with q including the new psi.
- The updated put-call parity identity: `C - P = S * exp(-q*T) - K * exp(-r*T)`.
- A citation to Hull 10e Chapter 17.

- [ ] **Step 2: Update `docs/risk/conventions.md`.**

Read the file. Find the line that says "dividends assumed zero in v1" or similar. Replace it with:

> Continuous dividend yield `q` is a first-class input across all pricers and endpoints; the default `q = 0` preserves the original v1 semantics. Discrete-dividend modeling (event-driven re-pricing on ex-dividend dates) remains out of scope. The put-call parity identity used in tests and reviews is `C - P = S * exp(-q*T) - K * exp(-r*T)`.

- [ ] **Step 3: Update `docs/api.md`.**

For each of the four endpoints (`/api/price`, `/api/heatmap`, `/api/calculations`, `/api/backtest`), add `q` to the request schema documentation with the same description used in the Pydantic field. Add `psi_per_pct` to the `GreeksDisplay` shape in the `/api/price` response section. Add a one-paragraph note that `q = 0` is the default for backwards compatibility and that omitting `q` produces identical results to v1.

- [ ] **Step 4: Create the ADR at `docs/adr/0005-dividends-as-continuous-yield.md`.**

```markdown
# ADR 0005: Dividends modeled as a continuous yield

## Status
Accepted.

## Context
The v1 build assumed European options on a non-dividend-paying stock. Pricing AAPL or any other dividend-paying ticker therefore disagreed with market quotes by a meaningful amount. The next step is to support dividends without significantly expanding the math surface or the test reference set.

Two modeling choices were considered:

1. **Continuous dividend yield `q`** (Merton 1973 generalization of Black Scholes). One scalar parameter; the math substitution is `S → S * exp(-q * T)` in the formula. Closed form remains valid. Documented in Hull, Wilmott, Natenberg.
2. **Discrete dividends with ex-dividend dates.** Re-prices the underlying around each ex-dividend date with a downward jump equal to the cash dividend. Requires an event-driven re-pricing loop, a per-ticker dividend timeline, and bigger changes to the binomial and Monte Carlo paths.

A third question was whether to expose the dividend Greek (`psi`, the analytical derivative of option value with respect to `q`). Two paths: skip it, or compute and display it as a sixth row in the Greeks panel.

A fourth question was whether to auto-fill `q` from yfinance's `dividendYield` when a ticker is selected.

## Decision
- Adopt the continuous dividend yield `q` as a first-class input across all pricers, all four endpoints, persistence, and every frontend form.
- Compute `psi` analytically and display it as a sixth row in the Greeks panel (per 1% q, mirroring the existing `vega_per_pct` and `rho_per_pct` convention).
- Do NOT auto-fill `q` from yfinance. The `dividendYield` field is occasionally null and reflects trailing rather than expected forward yield. A deferred entry in `future-ideas.md` captures this for revisit.
- Default `q = 0.0` everywhere preserves v1 behavior bit-for-bit when the field is omitted.

## Consequences
- The math docs gain a continuous-yield section; the conventions doc updates the dividend assumption.
- The persistence schema gains a `q` column; existing rows backfill to `0.0` (no truncation needed; pre-feature rows were priced under `q = 0`).
- The Pricing screen now has six inputs and the Greeks panel has six rows, pushing harder against the deferred "Pricing screen fits without scrolling" idea but not addressing it.
- Adding discrete dividends later remains possible (a separate `discrete_dividends: list[(date, amount)]` field could be added without breaking the existing API surface).
- The Risk and Financial Correctness Reviewer signs off this change per `SPEC.md` coordination rule 5.
```

- [ ] **Step 5: Commit.**

```bash
git add docs/math/black-scholes.md docs/risk/conventions.md docs/api.md docs/adr/0005-dividends-as-continuous-yield.md
git commit -m "dividends: docs (math, conventions, api, adr 0005)"
```

---

## Task 18: Update `future-ideas.md` (gitignored, repo root)

**Files:**
- Modify: `/home/mustafa/src/vega/future-ideas.md`

- [ ] **Step 1: Replace the existing "Dividends in the pricing model" entry with a one-liner saying it shipped, and add a NEW deferred entry for yfinance auto-fill.**

The "Dividends in the pricing model" section currently spans lines 53-61 (approximately). Replace it with:

```markdown
## Dividends in the pricing model

Shipped 2026-05-04 (continuous yield `q` across all three pricers, four endpoints, persistence, and every frontend form; `psi` Greek added to the panel; default `q = 0` preserves v1 behavior). Discrete-dividend modeling remains out of scope; see ADR 0005.

## Auto-fill `q` from yfinance dividend yield

**Idea**: when the user picks a ticker via the autocomplete, also auto-fill the dividend yield field `q` from yfinance's `dividendYield` (in addition to the existing auto-fill of `S`).

**Why deferred**: yfinance's `dividendYield` is occasionally null, sometimes stale, and reflects the trailing twelve months rather than the expected forward yield (which is what Black Scholes actually wants). Silently auto-filling a wrong-feeling number for AAPL is worse than asking the user for one.

**When to revisit**: if a future improvement to the ticker service can pull a forward dividend estimate (or if an explicit "auto-fill from trailing yield" button feels worth adding next to the q field). A small UI affordance ("auto-filled from trailing yield, edit if needed") would also resolve the surprise concern.

**Notes for the implementer**: extend `app/services/tickers.py` to return `dividend_yield` alongside the existing fields, extend the `/api/tickers/{symbol}` response schema, extend the `TickerAutocomplete` component to pipe the value into the form's `q` field. UI affordance recommended over silent auto-fill.
```

- [ ] **Step 2: Verify the change is local-only (gitignored).**

```bash
git status future-ideas.md
```

Expected: nothing reported (the file is in `.gitignore`).

- [ ] **Step 3: No commit.**

`future-ideas.md` is gitignored. Do not stage it.

---

## Task 19: Final verification (full local test + lint + audit pass)

**Files:**
- None (verification only).

- [ ] **Step 1: Backend pytest, ruff, mypy.**

```bash
uv --project backend run pytest -q 2>&1 | tail -10
uv --project backend run ruff check backend
uv --project backend run mypy backend
```

Expected:
- pytest: all pass (count is baseline 329 plus the sum of new tests added in Tasks 1 to 10; rough estimate 25 to 30 new backend tests).
- ruff: clean.
- mypy: clean except for the two pre-existing `yfinance import-untyped` warnings noted in `STATUS.md`.

- [ ] **Step 2: Frontend test, lint, tsc, build.**

```bash
pnpm --filter frontend test --run 2>&1 | tail -10
pnpm --filter frontend lint
pnpm --filter frontend tsc --noEmit
pnpm --filter frontend build
```

Expected: all clean.

- [ ] **Step 3: Audits.**

```bash
uv --project backend run pip-audit
pnpm --filter frontend audit --prod
```

Expected: clean (no new dependencies were added; this should match the post-Phase-12 baseline).

- [ ] **Step 4: If any of Steps 1-3 fail, fix the failure before continuing. Do not proceed to PR with red checks.**

---

## Task 20: Update STATUS.md and open PR

**Files:**
- Modify: `STATUS.md` (just the "Last updated" and the Design sync log; the dividends work is post Phase 11/12 polish, not a numbered phase, so do NOT add a row to the phase table)

- [ ] **Step 1: Update `STATUS.md`.**

Change the `**Last updated**:` line to today's date. Append a one-line entry to the **Design sync log** if the change touched any visual surface (it does: the GreeksPanel grew a row, and the three forms each grew a field). Format:

```
2026-05-04 A: dividends q field added to InputForm, HeatMapControls, BacktestForm; psi row added to GreeksPanel; q rendered in HistoryScreen summary and detail.
```

Update the "Next phase" section: the next deferred polish item per the gitignored ideas file is "Logo, favicon, and tab title" (unchanged from before this work).

- [ ] **Step 2: Commit STATUS.md change.**

```bash
git add STATUS.md
git commit -m "status: dividends shipped; design sync log entry"
```

- [ ] **Step 3: Push the branch.**

```bash
git push -u origin dividends-q
```

- [ ] **Step 4: Open the PR with `gh pr create`.**

```bash
gh pr create --title "Dividends: continuous yield q across the pricer" --body "$(cat <<'EOF'
## Summary

Adds a continuous dividend yield `q` as a first-class input across all three pricers (Black Scholes scalar + vec, binomial CRR, Monte Carlo), all four pricing endpoints (`/api/price`, `/api/heatmap`, `/api/calculations`, `/api/backtest`), the persistence schema (`calculation_inputs.q` column with backfill-zero migration), and every frontend form that takes pricing inputs (`InputForm`, `HeatMapControls`, `BacktestForm`). The Greeks panel gains a sixth row, `psi`, displayed per 1% q. Default `q = 0.0` everywhere preserves v1 behavior bit-for-bit when the field is omitted.

## Design and ADR

- Spec: `docs/superpowers/specs/2026-05-04-dividends-design.md`.
- Plan: `docs/superpowers/plans/2026-05-04-dividends.md`.
- ADR: `docs/adr/0005-dividends-as-continuous-yield.md`.

## Risk Reviewer gate

This PR touches pricing math and P&L; per `SPEC.md` coordination rule 5 the Risk and Financial Correctness Reviewer signs off before merge.

## Test plan

- [ ] Backend: `uv --project backend run pytest -q` is green; new tests cover Hull reference values for `q != 0`, the new put-call parity identity, the psi Greek formulas at the dividend reference, the q=0 backwards-compatibility path on every pricer, validation rejection of out-of-range q, and persistence round-trip of q.
- [ ] Frontend: `pnpm --filter frontend test --run` is green; new tests cover the q field on `InputForm`, `HeatMapControls`, `BacktestForm`, the psi row on `GreeksPanel`, and q rendering on the history summary and detail.
- [ ] Audits: `pip-audit` and `pnpm audit` are clean.
- [ ] Manual smoke against the live deploy (`vega-2rd.pages.dev`): type AAPL, set q to 0.5%, verify call price drops vs q=0; save the calculation; verify the saved row's q comes back on the History screen.
EOF
)"
```

- [ ] **Step 5: Watch CI checks.**

```bash
gh pr checks <N> --watch --interval 10
```

Where `<N>` is the PR number returned by Step 4.

Expected: all required checks (Backend, Frontend, Secrets scan, Python SAST, SAST semgrep) report `pass`.

- [ ] **Step 6: Admin merge.**

Once all required checks are green:

```bash
gh pr merge <N> --squash --delete-branch --admin
```

Per the standing CLAUDE.md push protocol, `--admin` is pre-authorized for this solo repo because the "1 review required" branch protection rule is structurally unsatisfiable. Do not skip required checks.

- [ ] **Step 7: Sync local main.**

```bash
git checkout main
git pull --ff-only
```

Confirm the squash commit is on main.

- [ ] **Step 8: Report to the user.**

Report: PR number, squash SHA on main, two-sentence summary of what shipped.

---

## Self-review (run by the planner before handoff)

**Spec coverage check:**

| Spec section | Plan task(s) |
|---|---|
| Math layer: scalar BS | Task 1 |
| Math layer: Greeks + psi | Task 2 |
| Math layer: vectorized BS | Task 3 |
| Math layer: binomial | Task 4 |
| Math layer: Monte Carlo | Task 5 |
| API: /api/price | Task 6 |
| API: /api/heatmap | Task 7 |
| API: /api/backtest + backtest engine | Task 8 |
| Persistence: schema, migration, model | Task 9 |
| API: /api/calculations | Task 10 |
| Frontend: api types | Task 11 |
| Frontend: InputForm | Task 12 |
| Frontend: GreeksPanel | Task 13 |
| Frontend: HeatMapControls + HeatMapScreen | Task 14 |
| Frontend: BacktestForm | Task 15 |
| Frontend: HistoryScreen | Task 16 |
| Docs: math, conventions, api, ADR | Task 17 |
| future-ideas.md update | Task 18 |
| Final verification | Task 19 |
| STATUS.md + PR | Task 20 |

All ten acceptance criteria from the spec map to tasks above (criterion 1 to 4 covered by Tasks 1-10; 5 covered by Task 2; 6 by Task 13; 7 by Task 9; 8 by Task 16; 9 by Tasks 12, 14, 15; 10 by Task 19 and the Risk Reviewer step in Task 20).

**Type consistency:** Every task uses `q: float = 0.0` for backend signatures, `q?: number` for frontend optional types and `q: number` for response shapes; `psi` for the math-layer Greek field, `psi_per_pct` for the API and frontend display field. Names match across tasks.

**Placeholder scan:** No "TBD", "TODO", "fill in details" left in the plan. Two locations note "use the same pattern as existing tests" for fixtures (auth_headers, dependency_overrides for historical lookup, GreeksPanel test prop shape, HistoryScreen mocks); these are intentional pointers to existing code rather than placeholders, since fabricating fixtures the project does not use would be worse than referring the implementer to the existing files.

---

**End of plan.**
