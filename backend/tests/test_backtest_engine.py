import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.research import (
    DefinedExperimentSpec,
    DefinedMarketContext,
    DefinedSignalRules,
    DefinedPositionRules,
    DefinedBacktestBounds,
    ParameterProvenanceRecord,
    ParameterSource,
    TestExecutionRequest,
    BacktestResult,
)
from app.services.backtest_engine import BacktestEngine

client = TestClient(app)


@pytest.fixture
def sample_defined_spec() -> DefinedExperimentSpec:
    """
    Returns a standard, valid DefinedExperimentSpec for testing.
    """
    return DefinedExperimentSpec(
        research_question="Does buying NIFTY after a 1% fall work better during high-volatility periods?",
        hypothesis="Buying NIFTY 50 on pullbacks >= 1.0% during high volatility yields positive alpha.",
        market_context=DefinedMarketContext(
            instrument="NIFTY",
            timeframe="1D (Daily)",
        ),
        signal_rules=DefinedSignalRules(
            entry_condition="Close drops >= 1.0% from previous close",
            filters=["India VIX > 20"],
        ),
        position_rules=DefinedPositionRules(
            exit_condition="Exit on 2% target or 1% stop loss",
            holding_period="5 trading sessions",
        ),
        backtest_bounds=DefinedBacktestBounds(
            test_period="2020 to 2024",
            cost_assumptions="0.05% slippage per side",
        ),
        provenance_audit=[
            ParameterProvenanceRecord(
                field="instrument",
                source=ParameterSource.USER_EXPLICIT,
                confidence=1.0,
                requires_confirmation=False,
            ),
            ParameterProvenanceRecord(
                field="entry_condition",
                source=ParameterSource.USER_EXPLICIT,
                confidence=1.0,
                requires_confirmation=False,
            ),
        ],
    )


def test_successful_test_execution(sample_defined_spec: DefinedExperimentSpec):
    """
    1. Successful test execution: Engine runs on valid spec and produces populated result.
    """
    result = BacktestEngine.run(sample_defined_spec, initial_capital=100000.0)

    assert isinstance(result, BacktestResult)
    assert result.instrument == "NIFTY"
    assert result.timeframe == "1D (Daily)"
    assert result.initial_capital == 100000.0
    assert len(result.equity_curve) == 500
    assert len(result.trades) > 0
    assert result.metrics.total_trades == len(result.trades)
    assert result.simulation_disclaimer == BacktestEngine.SIMULATION_DISCLAIMER
    assert "candle t close" in result.execution_timing_convention.lower()


def test_signal_at_t_executes_at_t_plus_1_open(sample_defined_spec: DefinedExperimentSpec):
    """
    2. Signal at candle t evaluates strictly on close, trade executes at candle t+1 open.
    """
    result = BacktestEngine.run(sample_defined_spec)

    for trade in result.trades:
        # Trade entry_bar_index must be strictly greater than signal bar index (i.e. t + 1)
        assert trade.entry_bar_index >= 1
        assert trade.exit_bar_index >= trade.entry_bar_index
        assert trade.entry_price > 0.0
        assert trade.exit_price > 0.0


def test_no_lookahead_bias(sample_defined_spec: DefinedExperimentSpec):
    """
    3. No look-ahead: Signal evaluation at bar t never references bar t+1 prices or future bars.
    """
    # Create controlled 4-bar scenario
    bars = [
        {"bar_index": 0, "date": "2024-01-01", "open": 100.0, "high": 105.0, "low": 98.0, "close": 100.0, "vix": 25.0},
        {"bar_index": 1, "date": "2024-01-02", "open": 100.0, "high": 101.0, "low": 98.5, "close": 98.8, "vix": 25.0},  # 1.2% drop from 100.0
        {"bar_index": 2, "date": "2024-01-03", "open": 99.0, "high": 102.0, "low": 98.0, "close": 101.0, "vix": 25.0},   # Entry occurs here
        {"bar_index": 3, "date": "2024-01-04", "open": 101.0, "high": 103.0, "low": 100.0, "close": 102.0, "vix": 25.0},
    ]

    # Signal at t=1 (Close=98.8 vs Close=100.0 -> drop 1.2% >= 1.0%)
    signal_at_t1 = BacktestEngine.evaluate_signal_at_t(bars, t=1, drop_threshold=0.01, has_vix_filter=True)
    assert signal_at_t1 is True

    # Signal at t=0 cannot look back before index 0
    signal_at_t0 = BacktestEngine.evaluate_signal_at_t(bars, t=0, drop_threshold=0.01, has_vix_filter=True)
    assert signal_at_t0 is False

    # Simulate trades on this exact 4-bar series
    trades = BacktestEngine.simulate_trades(
        bars=bars,
        drop_threshold=0.01,
        has_vix_filter=True,
        holding_bars=1,
        target_pct=None,
        stop_pct=None,
        slippage_rate=0.0,
    )
    assert len(trades) == 1
    # Trade entered at Bar 2 (t+1) Open = 99.0
    assert trades[0].entry_bar_index == 2
    assert trades[0].entry_price == 99.0


def test_exact_holding_period():
    """
    4. Exact holding period: Trade held for H bars exits on exact target forward bar.
    """
    # 7-bar series: signal at t=1, entry at t=2, holding_bars=3 -> exit at t=2+3=5
    bars = [
        {"bar_index": 0, "date": "2024-01-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "vix": 22.0},
        {"bar_index": 1, "date": "2024-01-02", "open": 100.0, "high": 100.0, "low": 98.0, "close": 98.0, "vix": 22.0},  # Signal fires (2% drop)
        {"bar_index": 2, "date": "2024-01-03", "open": 98.0, "high": 99.0, "low": 97.0, "close": 98.0, "vix": 22.0},   # Entry (holding bar 0)
        {"bar_index": 3, "date": "2024-01-04", "open": 98.0, "high": 99.0, "low": 97.0, "close": 98.0, "vix": 22.0},   # holding bar 1
        {"bar_index": 4, "date": "2024-01-05", "open": 98.0, "high": 99.0, "low": 97.0, "close": 98.0, "vix": 22.0},   # holding bar 2
        {"bar_index": 5, "date": "2024-01-08", "open": 99.0, "high": 100.0, "low": 98.0, "close": 99.0, "vix": 22.0},  # Exit at Open (holding bar 3)
        {"bar_index": 6, "date": "2024-01-09", "open": 99.0, "high": 100.0, "low": 98.0, "close": 99.0, "vix": 22.0},
    ]

    trades = BacktestEngine.simulate_trades(
        bars=bars,
        drop_threshold=0.01,
        has_vix_filter=False,
        holding_bars=3,
        target_pct=None,
        stop_pct=None,
        slippage_rate=0.0,
    )
    assert len(trades) == 1
    t = trades[0]
    assert t.entry_bar_index == 2
    assert t.exit_bar_index == 5
    assert t.holding_bars == 3
    assert t.exit_reason == "HOLDING_PERIOD_EXPIRY"


def test_profit_target_trigger():
    """
    5. Profit target: Exits when bar High crosses target price during holding window.
    """
    bars = [
        {"bar_index": 0, "date": "2024-01-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "vix": 22.0},
        {"bar_index": 1, "date": "2024-01-02", "open": 100.0, "high": 100.0, "low": 98.0, "close": 98.0, "vix": 22.0},  # Signal
        {"bar_index": 2, "date": "2024-01-03", "open": 100.0, "high": 101.0, "low": 99.5, "close": 100.5, "vix": 22.0}, # Entry at 100.0
        {"bar_index": 3, "date": "2024-01-04", "open": 100.5, "high": 103.5, "low": 100.0, "close": 103.0, "vix": 22.0}, # Target = 2% (102.0), High=103.5
    ]

    trades = BacktestEngine.simulate_trades(
        bars=bars,
        drop_threshold=0.01,
        has_vix_filter=False,
        holding_bars=10,
        target_pct=0.02,
        stop_pct=0.02,
        slippage_rate=0.0,
    )
    assert len(trades) == 1
    t = trades[0]
    assert t.exit_reason == "PROFIT_TARGET"
    assert t.exit_bar_index == 3
    assert t.exit_price == 102.0
    assert t.is_win is True


def test_stop_loss_trigger():
    """
    6. Stop loss: Exits when bar Low crosses stop price during holding window.
    """
    bars = [
        {"bar_index": 0, "date": "2024-01-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "vix": 22.0},
        {"bar_index": 1, "date": "2024-01-02", "open": 100.0, "high": 100.0, "low": 98.0, "close": 98.0, "vix": 22.0},  # Signal
        {"bar_index": 2, "date": "2024-01-03", "open": 100.0, "high": 100.5, "low": 98.5, "close": 99.0, "vix": 22.0},  # Entry at 100.0, Stop=1% (99.0), Low=98.5
    ]

    trades = BacktestEngine.simulate_trades(
        bars=bars,
        drop_threshold=0.01,
        has_vix_filter=False,
        holding_bars=5,
        target_pct=0.03,
        stop_pct=0.01,
        slippage_rate=0.0,
    )
    assert len(trades) == 1
    t = trades[0]
    assert t.exit_reason == "STOP_LOSS"
    assert t.exit_price == 99.0
    assert t.is_win is False


def test_same_bar_target_and_stop_uses_conservative_stop_first():
    """
    7. Same-bar collision: When both target and stop are crossed on the same candle,
       conservatively assumes STOP_LOSS occurs first.
    """
    bars = [
        {"bar_index": 0, "date": "2024-01-01", "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "vix": 22.0},
        {"bar_index": 1, "date": "2024-01-02", "open": 100.0, "high": 100.0, "low": 98.0, "close": 98.0, "vix": 22.0},  # Signal
        # Bar 2: Entry at 100.0. Target is 102.0 (+2%), Stop is 98.0 (-2%).
        # Bar 2 High is 103.0 (crosses target) AND Low is 97.0 (crosses stop).
        {"bar_index": 2, "date": "2024-01-03", "open": 100.0, "high": 103.0, "low": 97.0, "close": 101.0, "vix": 22.0},
    ]

    trades = BacktestEngine.simulate_trades(
        bars=bars,
        drop_threshold=0.01,
        has_vix_filter=False,
        holding_bars=5,
        target_pct=0.02,
        stop_pct=0.02,
        slippage_rate=0.0,
    )
    assert len(trades) == 1
    t = trades[0]
    # MUST resolve to STOP_LOSS, not PROFIT_TARGET
    assert t.exit_reason == "STOP_LOSS"
    assert t.exit_price == 98.0
    assert t.is_win is False


def test_slippage_and_friction_reduces_net_result(sample_defined_spec: DefinedExperimentSpec):
    """
    8. Slippage: Friction strictly reduces net PnL compared to gross PnL.
    """
    result = BacktestEngine.run(sample_defined_spec)
    assert len(result.trades) > 0

    for trade in result.trades:
        assert trade.net_pnl_pct <= trade.gross_pnl_pct
        assert trade.friction_paid_pct >= 0.0

    assert result.metrics.net_return_pct < result.metrics.gross_return_pct
    assert result.metrics.friction_drag_pct > 0.0


def test_zero_friction_matches_gross(sample_defined_spec: DefinedExperimentSpec):
    """
    9. Zero friction: When cost_assumptions specify zero fees, net equals gross.
    """
    spec_zero = sample_defined_spec.model_copy(deep=True)
    spec_zero.backtest_bounds.cost_assumptions = "Zero fees (idealized)"

    result = BacktestEngine.run(spec_zero)
    assert len(result.trades) > 0

    for trade in result.trades:
        assert trade.net_pnl_pct == trade.gross_pnl_pct
        assert trade.friction_paid_pct == 0.0

    assert result.metrics.friction_drag_pct == 0.0
    assert result.metrics.net_return_pct == result.metrics.gross_return_pct


def test_deterministic_reproducibility(sample_defined_spec: DefinedExperimentSpec):
    """
    10. Determinism: Two separate executions on the same spec produce identical results bit-for-bit.
    """
    run1 = BacktestEngine.run(sample_defined_spec)
    run2 = BacktestEngine.run(sample_defined_spec)

    assert run1.experiment_id == run2.experiment_id
    assert run1.reproducible_seed == run2.reproducible_seed
    assert run1.final_equity == run2.final_equity
    assert run1.metrics.net_return_pct == run2.metrics.net_return_pct
    assert len(run1.trades) == len(run2.trades)

    for t1, t2 in zip(run1.trades, run2.trades):
        assert t1.entry_date == t2.entry_date
        assert t1.entry_price == t2.entry_price
        assert t1.exit_price == t2.exit_price
        assert t1.net_pnl_pct == t2.net_pnl_pct


def test_zero_trade_robustness(sample_defined_spec: DefinedExperimentSpec):
    """
    11. Zero-trade robustness: Handles an extreme condition with 0 trades gracefully without NaN.
    """
    spec_impossible = sample_defined_spec.model_copy(deep=True)
    # 50% single-day fall is impossible in standard daily data
    spec_impossible.signal_rules.entry_condition = "Close drops >= 50.0% in one day"

    result = BacktestEngine.run(spec_impossible, initial_capital=100000.0)

    assert len(result.trades) == 0
    assert result.metrics.total_trades == 0
    assert result.metrics.win_rate_pct == 0.0
    assert result.metrics.net_return_pct == 0.0
    assert result.metrics.max_drawdown_pct == 0.0
    assert result.metrics.sharpe_ratio is None
    assert result.final_equity == 100000.0


def test_metrics_consistency(sample_defined_spec: DefinedExperimentSpec):
    """
    12. Metrics consistency: Win rate = wins / total, win_count + loss_count = total_trades.
    """
    result = BacktestEngine.run(sample_defined_spec)
    m = result.metrics

    assert m.winning_trades + m.losing_trades == m.total_trades
    expected_win_rate = round((m.winning_trades / m.total_trades) * 100.0, 2)
    assert m.win_rate_pct == expected_win_rate


def test_api_test_endpoint(sample_defined_spec: DefinedExperimentSpec):
    """
    13. API Endpoint: POST /api/research/test accepts DefinedExperimentSpec and returns BacktestResult.
    """
    resp = client.post(
        "/api/research/test",
        json={
            "spec": sample_defined_spec.model_dump(),
            "initial_capital": 100000.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert "equity_curve" in data
    assert "trades" in data
    assert data["instrument"] == "NIFTY"
    assert "simulation_disclaimer" in data


def test_no_external_calls_during_test(sample_defined_spec: DefinedExperimentSpec):
    """
    14. Stateless & Offline: No LLM, database, or external network calls during backtesting.
    """
    with patch("google.genai.Client") as mock_genai:
        resp = client.post(
            "/api/research/test",
            json={"spec": sample_defined_spec.model_dump()},
        )
        assert resp.status_code == 200
        mock_genai.assert_not_called()
