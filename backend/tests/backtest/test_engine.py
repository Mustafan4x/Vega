"""Tests for the pure backtest engine.

The engine takes a daily price series and a strategy spec and
produces a P&L curve under the long holder convention from
``docs/risk/conventions.md`` and ``docs/risk/sanity-cases.md``.

The engine itself is deterministic and pure: same inputs in,
same numbers out. yfinance integration lives in
``app.services.historical``; the engine never talks to anything.
"""

from __future__ import annotations

import math

import pytest

from app.backtest.engine import (
    BacktestRequest,
    Strategy,
    run_backtest,
)
from app.pricing.black_scholes import black_scholes_call, black_scholes_put

# Synthetic flat price series so closed form expectations are easy.
FLAT_DATES = ("2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08")
FLAT_CLOSES = (100.0, 100.0, 100.0, 100.0, 100.0)


def _request(strategy: Strategy, sigma: float = 0.2, dte_days: int = 30) -> BacktestRequest:
    return BacktestRequest(
        strategy=strategy,
        dates=FLAT_DATES,
        closes=FLAT_CLOSES,
        sigma=sigma,
        r=0.05,
        dte_days=dte_days,
    )


def test_long_call_returns_curve_with_one_point_per_date() -> None:
    result = run_backtest(_request(Strategy.LONG_CALL))

    assert len(result.dates) == len(FLAT_DATES)
    assert len(result.spot) == len(FLAT_DATES)
    assert len(result.position_value) == len(FLAT_DATES)
    assert len(result.pnl) == len(FLAT_DATES)


def test_long_call_starts_at_zero_pnl() -> None:
    # On the entry day, position value equals cost, so P&L is zero.
    result = run_backtest(_request(Strategy.LONG_CALL))

    assert result.pnl[0] == pytest.approx(0.0, abs=1e-9)


def test_long_call_pnl_zero_on_flat_series_at_entry() -> None:
    result = run_backtest(_request(Strategy.LONG_CALL))

    # On a flat series, the option value drops with time decay so
    # the long call P&L should be negative at later dates.
    assert all(p <= 1e-9 for p in result.pnl)
    # Final P&L should be the negative of the time decay over the
    # series length, which is small but non zero.
    assert result.pnl[-1] < 0


def test_strategy_metadata_lists_legs() -> None:
    result = run_backtest(_request(Strategy.STRADDLE))

    assert len(result.legs) == 2
    kinds = sorted(leg.kind for leg in result.legs)
    assert kinds == ["call", "put"]


def test_long_put_pnl_matches_intrinsic_payoff_at_expiry() -> None:
    # Step the underlying down at the last date so the long put has
    # intrinsic value equal to (K - S) at expiry.
    dates = ("2026-01-02", "2026-01-30", "2026-02-01")  # day 0, day 28, day 30 = expiry
    closes = (100.0, 95.0, 90.0)
    request = BacktestRequest(
        strategy=Strategy.LONG_PUT,
        dates=dates,
        closes=closes,
        sigma=0.2,
        r=0.05,
        dte_days=30,
    )

    result = run_backtest(request)

    # Entry premium = BS put at S=K=100, T=30/365, r=0.05, sigma=0.2.
    entry_put = black_scholes_put(100.0, 100.0, 30.0 / 365.0, 0.05, 0.20)
    # At expiry the put is worth max(K - S, 0) = max(100 - 90, 0) = 10.
    # So the P&L is intrinsic minus entry premium.
    expected_terminal_pnl = 10.0 - entry_put
    assert result.pnl[-1] == pytest.approx(expected_terminal_pnl, abs=0.01)


def test_long_call_pnl_matches_intrinsic_payoff_at_expiry() -> None:
    dates = ("2026-01-02", "2026-01-15", "2026-02-01")  # entry, mid, expiry
    closes = (100.0, 105.0, 115.0)
    request = BacktestRequest(
        strategy=Strategy.LONG_CALL,
        dates=dates,
        closes=closes,
        sigma=0.2,
        r=0.05,
        dte_days=30,
    )

    result = run_backtest(request)

    entry_call = black_scholes_call(100.0, 100.0, 30.0 / 365.0, 0.05, 0.20)
    expected_terminal_pnl = 15.0 - entry_call
    assert result.pnl[-1] == pytest.approx(expected_terminal_pnl, abs=0.01)


def test_straddle_terminal_pnl_is_call_minus_basis() -> None:
    # Big up move: only the call has intrinsic; put expires worthless.
    dates = ("2026-01-02", "2026-02-01")
    closes = (100.0, 130.0)
    request = BacktestRequest(
        strategy=Strategy.STRADDLE,
        dates=dates,
        closes=closes,
        sigma=0.2,
        r=0.05,
        dte_days=30,
    )

    result = run_backtest(request)

    entry_call = black_scholes_call(100.0, 100.0, 30.0 / 365.0, 0.05, 0.20)
    entry_put = black_scholes_put(100.0, 100.0, 30.0 / 365.0, 0.05, 0.20)
    basis = entry_call + entry_put
    expected = (130.0 - 100.0) - basis  # call intrinsic 30, put intrinsic 0
    assert result.pnl[-1] == pytest.approx(expected, abs=0.01)


def test_strikes_at_entry_spot() -> None:
    result = run_backtest(_request(Strategy.LONG_CALL))

    assert result.strike == pytest.approx(100.0)


def test_pnl_signs_for_long_call_increasing_spot() -> None:
    # Strictly increasing spot before expiry: long call P&L should
    # eventually go positive once intrinsic exceeds time decay.
    dates = ("2026-01-02", "2026-01-15", "2026-01-30", "2026-02-01")
    closes = (100.0, 110.0, 130.0, 150.0)
    request = BacktestRequest(
        strategy=Strategy.LONG_CALL,
        dates=dates,
        closes=closes,
        sigma=0.2,
        r=0.05,
        dte_days=30,
    )

    result = run_backtest(request)

    assert result.pnl[-1] > 0
    # Big up move dominates time decay.
    assert result.pnl[-1] > result.pnl[0]


def test_rejects_empty_dates() -> None:
    with pytest.raises(ValueError):
        run_backtest(
            BacktestRequest(
                strategy=Strategy.LONG_CALL,
                dates=(),
                closes=(),
                sigma=0.2,
                r=0.05,
                dte_days=30,
            )
        )


def test_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        run_backtest(
            BacktestRequest(
                strategy=Strategy.LONG_CALL,
                dates=("2026-01-02",),
                closes=(100.0, 101.0),
                sigma=0.2,
                r=0.05,
                dte_days=30,
            )
        )


def test_rejects_non_positive_dte() -> None:
    with pytest.raises(ValueError):
        run_backtest(
            BacktestRequest(
                strategy=Strategy.LONG_CALL,
                dates=FLAT_DATES,
                closes=FLAT_CLOSES,
                sigma=0.2,
                r=0.05,
                dte_days=0,
            )
        )


def test_rejects_negative_sigma() -> None:
    with pytest.raises(ValueError):
        run_backtest(
            BacktestRequest(
                strategy=Strategy.LONG_CALL,
                dates=FLAT_DATES,
                closes=FLAT_CLOSES,
                sigma=-0.1,
                r=0.05,
                dte_days=30,
            )
        )


def test_rejects_non_positive_close_price() -> None:
    with pytest.raises(ValueError):
        run_backtest(
            BacktestRequest(
                strategy=Strategy.LONG_CALL,
                dates=("2026-01-02", "2026-01-05"),
                closes=(100.0, 0.0),
                sigma=0.2,
                r=0.05,
                dte_days=30,
            )
        )


def test_returns_metadata_on_basis_and_strike() -> None:
    result = run_backtest(_request(Strategy.STRADDLE))

    # Straddle basis is call + put at the money.
    expected_basis = black_scholes_call(100.0, 100.0, 30.0 / 365.0, 0.05, 0.2) + black_scholes_put(
        100.0, 100.0, 30.0 / 365.0, 0.05, 0.2
    )
    assert result.entry_basis == pytest.approx(expected_basis, abs=1e-6)
    assert result.strike == pytest.approx(100.0)
    assert result.entry_date == "2026-01-02"
    assert result.expiry_date == _expected_expiry("2026-01-02", 30)


def _expected_expiry(entry: str, dte: int) -> str:
    from datetime import date as d
    from datetime import timedelta

    e = d.fromisoformat(entry)
    exp = e + timedelta(days=dte)
    return exp.isoformat()


def test_finite_values_only() -> None:
    result = run_backtest(_request(Strategy.LONG_CALL))

    assert all(math.isfinite(v) for v in result.position_value)
    assert all(math.isfinite(v) for v in result.pnl)
    assert all(math.isfinite(v) for v in result.spot)


def test_engine_perf_max_dates_straddle_under_50_ms() -> None:
    # Worst case for the pure engine: max-cap series length and the
    # straddle (two BS marks per day). Bound is intentionally loose
    # (measured ~5 ms locally) so this test catches an accidental
    # quadratic without flaking on slow CI.
    import time
    from datetime import date, timedelta

    n = 1300  # MAX_DATES
    start = date(2020, 1, 1)
    dates = tuple((start + timedelta(days=i)).isoformat() for i in range(n))
    closes = tuple(100.0 + 0.01 * i for i in range(n))
    request = BacktestRequest(
        strategy=Strategy.STRADDLE,
        dates=dates,
        closes=closes,
        sigma=0.20,
        r=0.05,
        dte_days=365,
    )

    t0 = time.perf_counter()
    run_backtest(request)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 50.0, f"engine took {elapsed_ms:.1f} ms, expected under 50 ms"
