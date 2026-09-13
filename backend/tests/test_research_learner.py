import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.research import (
    BacktestResult,
    BacktestMetrics,
    DefinedExperimentSpec,
    DefinedMarketContext,
    DefinedSignalRules,
    DefinedPositionRules,
    DefinedBacktestBounds,
    EvidenceLevel,
    ParameterProvenanceRecord,
    ParameterSource,
    SimulatedTrade,
    EquityPoint,
)
from app.services.research_learner import ResearchLearner

client = TestClient(app)


@pytest.fixture
def sample_spec() -> DefinedExperimentSpec:
    return DefinedExperimentSpec(
        research_question="Does buying after a 2% drop yield positive returns?",
        hypothesis="Mean reversion hypothesis on index pullback",
        market_context=DefinedMarketContext(instrument="NIFTY", timeframe="1D"),
        signal_rules=DefinedSignalRules(entry_condition="Close drops >= 2.0% in one day", filters=[]),
        position_rules=DefinedPositionRules(
            exit_condition="Profit target 2.0% or Stop loss 1.0%",
            holding_period="5 trading days maximum",
        ),
        backtest_bounds=DefinedBacktestBounds(
            test_period="2020-01-01 to 2024-01-01",
            cost_assumptions="0.05% slippage per side",
        ),
        provenance_audit=[
            ParameterProvenanceRecord(
                field="instrument",
                source=ParameterSource.USER_EXPLICIT,
                confidence=1.0,
                requires_confirmation=False,
            )
        ],
    )


@pytest.fixture
def base_metrics() -> BacktestMetrics:
    return BacktestMetrics(
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        win_rate_pct=60.0,
        net_return_pct=5.5,
        gross_return_pct=7.0,
        friction_drag_pct=1.5,
        profit_factor=1.85,
        max_drawdown_pct=3.2,
        avg_trade_return_pct=0.55,
        avg_holding_bars=3.8,
        sharpe_ratio=1.42,
    )


@pytest.fixture
def sample_backtest_result(base_metrics: BacktestMetrics) -> BacktestResult:
    return BacktestResult(
        experiment_id="EXP-TEST1234",
        instrument="NIFTY",
        timeframe="1D",
        test_period="2020-01-01 to 2024-01-01",
        initial_capital=100000.0,
        final_equity=105500.0,
        metrics=base_metrics,
        equity_curve=[
            EquityPoint(date="2020-01-02", equity=100000.0, drawdown_pct=0.0, in_trade=False),
            EquityPoint(date="2020-01-03", equity=105500.0, drawdown_pct=0.0, in_trade=False),
        ],
        trades=[
            SimulatedTrade(
                trade_id=1,
                entry_bar_index=1,
                entry_date="2020-01-02",
                entry_price=100.0,
                exit_bar_index=4,
                exit_date="2020-01-05",
                exit_price=102.0,
                exit_reason="PROFIT_TARGET",
                gross_pnl_pct=0.02,
                net_pnl_pct=0.019,
                friction_paid_pct=0.001,
                holding_bars=3,
                is_win=True,
            )
        ],
        execution_timing_convention="Signal on candle t close -> Entry on candle t+1 open",
        simulation_disclaimer="Deterministic synthetic reference data. Results are illustrative and do not represent real market performance or live execution.",
        reproducible_seed=12345678,
    )


def test_evidence_level_mutually_exclusive_priority():
    """
    1. Tests strict mutually exclusive priority order:
       - 0 trades -> SYNTHETIC_INSUFFICIENT_DATA
       - < 3 trades -> SYNTHETIC_INSUFFICIENT_DATA
       - gross > 0 and net <= 0 -> SYNTHETIC_FRICTION_DOMINATED
       - net <= 0 -> SYNTHETIC_NEGATIVE_EDGE
       - else -> SYNTHETIC_CANDIDATE_FOR_REAL_DATA
    """
    # 0 trades
    m0 = BacktestMetrics(
        total_trades=0, winning_trades=0, losing_trades=0, win_rate_pct=0.0,
        net_return_pct=0.0, gross_return_pct=0.0, friction_drag_pct=0.0,
        profit_factor=0.0, max_drawdown_pct=0.0, avg_trade_return_pct=0.0,
        avg_holding_bars=0.0, sharpe_ratio=None,
    )
    assert ResearchLearner.evaluate_evidence_level(m0) == EvidenceLevel.SYNTHETIC_INSUFFICIENT_DATA

    # 1 trade (even with positive return)
    m1 = BacktestMetrics(
        total_trades=1, winning_trades=1, losing_trades=0, win_rate_pct=100.0,
        net_return_pct=5.0, gross_return_pct=5.1, friction_drag_pct=0.1,
        profit_factor=99.99, max_drawdown_pct=0.0, avg_trade_return_pct=5.0,
        avg_holding_bars=2.0, sharpe_ratio=None,
    )
    assert ResearchLearner.evaluate_evidence_level(m1) == EvidenceLevel.SYNTHETIC_INSUFFICIENT_DATA

    # 2 trades
    m2 = m1.model_copy(update={"total_trades": 2, "winning_trades": 2})
    assert ResearchLearner.evaluate_evidence_level(m2) == EvidenceLevel.SYNTHETIC_INSUFFICIENT_DATA

    # 3 trades, gross > 0, net <= 0 -> SYNTHETIC_FRICTION_DOMINATED
    m_fric = BacktestMetrics(
        total_trades=5, winning_trades=3, losing_trades=2, win_rate_pct=60.0,
        net_return_pct=-0.5, gross_return_pct=1.2, friction_drag_pct=1.7,
        profit_factor=0.9, max_drawdown_pct=2.0, avg_trade_return_pct=-0.1,
        avg_holding_bars=3.0, sharpe_ratio=-0.1,
    )
    assert ResearchLearner.evaluate_evidence_level(m_fric) == EvidenceLevel.SYNTHETIC_FRICTION_DOMINATED

    # 3 trades, gross <= 0, net <= 0 -> SYNTHETIC_NEGATIVE_EDGE
    m_neg = BacktestMetrics(
        total_trades=5, winning_trades=1, losing_trades=4, win_rate_pct=20.0,
        net_return_pct=-4.0, gross_return_pct=-3.0, friction_drag_pct=1.0,
        profit_factor=0.3, max_drawdown_pct=5.0, avg_trade_return_pct=-0.8,
        avg_holding_bars=4.0, sharpe_ratio=-1.1,
    )
    assert ResearchLearner.evaluate_evidence_level(m_neg) == EvidenceLevel.SYNTHETIC_NEGATIVE_EDGE

    # 5 trades, gross > 0, net > 0 -> SYNTHETIC_CANDIDATE_FOR_REAL_DATA
    m_pos = BacktestMetrics(
        total_trades=5, winning_trades=4, losing_trades=1, win_rate_pct=80.0,
        net_return_pct=3.5, gross_return_pct=4.2, friction_drag_pct=0.7,
        profit_factor=3.2, max_drawdown_pct=1.5, avg_trade_return_pct=0.7,
        avg_holding_bars=3.0, sharpe_ratio=1.6,
    )
    assert ResearchLearner.evaluate_evidence_level(m_pos) == EvidenceLevel.SYNTHETIC_CANDIDATE_FOR_REAL_DATA


def test_zero_trades_handled_honestly(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    2. When total_trades == 0, report does not fabricate performance observations.
    """
    zero_result = sample_backtest_result.model_copy(deep=True)
    zero_result.metrics = BacktestMetrics(
        total_trades=0, winning_trades=0, losing_trades=0, win_rate_pct=0.0,
        net_return_pct=0.0, gross_return_pct=0.0, friction_drag_pct=0.0,
        profit_factor=0.0, max_drawdown_pct=0.0, avg_trade_return_pct=0.0,
        avg_holding_bars=0.0, sharpe_ratio=None,
    )
    zero_result.trades = []

    report = ResearchLearner.generate_report(zero_result, sample_spec)

    assert report.evidence_level == EvidenceLevel.SYNTHETIC_INSUFFICIENT_DATA
    assert "0 executed trades" in report.summary
    assert any("Zero simulated trades were generated" in obs for obs in report.performance_observations)
    assert any("entry condition" in step.lower() for step in report.next_research_steps)


def test_fewer_than_3_trades_flagged(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    3. Low sample size (< 3 trades) is flagged as insufficient data.
    """
    low_result = sample_backtest_result.model_copy(deep=True)
    low_result.metrics = BacktestMetrics(
        total_trades=2, winning_trades=2, losing_trades=0, win_rate_pct=100.0,
        net_return_pct=4.0, gross_return_pct=4.2, friction_drag_pct=0.2,
        profit_factor=99.99, max_drawdown_pct=0.5, avg_trade_return_pct=2.0,
        avg_holding_bars=2.5, sharpe_ratio=None,
    )

    report = ResearchLearner.generate_report(low_result, sample_spec)
    assert report.evidence_level == EvidenceLevel.SYNTHETIC_INSUFFICIENT_DATA
    assert any("Small sample size alert" in obs for obs in report.performance_observations)


def test_friction_dominated_detected(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    4. Friction wipeout detected when gross > 0 and net <= 0.
    """
    fric_result = sample_backtest_result.model_copy(deep=True)
    fric_result.metrics = BacktestMetrics(
        total_trades=8, winning_trades=5, losing_trades=3, win_rate_pct=62.5,
        net_return_pct=-0.8, gross_return_pct=1.4, friction_drag_pct=2.2,
        profit_factor=0.95, max_drawdown_pct=2.1, avg_trade_return_pct=-0.1,
        avg_holding_bars=3.2, sharpe_ratio=-0.2,
    )

    report = ResearchLearner.generate_report(fric_result, sample_spec)
    assert report.evidence_level == EvidenceLevel.SYNTHETIC_FRICTION_DOMINATED
    assert "Friction wipeout" in report.friction_observation
    assert any("Stress-test transaction costs" in step for step in report.next_research_steps)


def test_candidate_for_real_data_validation(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    5. Positive net expectancy classified as candidate for real-data testing.
    """
    report = ResearchLearner.generate_report(sample_backtest_result, sample_spec)
    assert report.evidence_level == EvidenceLevel.SYNTHETIC_CANDIDATE_FOR_REAL_DATA
    assert any("actual historical tick" in step for step in report.next_research_steps)


def test_severe_drawdown_flagged(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    6. Flags when maximum drawdown exceeds final net return.
    """
    dd_result = sample_backtest_result.model_copy(deep=True)
    dd_result.metrics = dd_result.metrics.model_copy(update={"net_return_pct": 1.2, "max_drawdown_pct": 8.5})

    report = ResearchLearner.generate_report(dd_result, sample_spec)
    assert any("exceeded the final net return" in obs for obs in report.risk_observations)


def test_mandatory_synthetic_disclaimer(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    7. Verifies mandatory synthetic disclaimer is present in the report and limitations.
    """
    report = ResearchLearner.generate_report(sample_backtest_result, sample_spec)
    assert "Deterministic synthetic reference data" in report.disclaimer
    assert "Results are illustrative and do not represent real market performance" in report.disclaimer
    assert any("Deterministic synthetic reference data" in lim for lim in report.limitations)


def test_no_trading_advice_in_next_steps(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    8. Confirms that next research steps are research questions and NOT trading advice.
    """
    report = ResearchLearner.generate_report(sample_backtest_result, sample_spec)

    forbidden_advice = [
        "widen stop loss",
        "tighten stop loss",
        "increase position",
        "decrease position",
        "increase trade frequency",
        "decrease trade frequency",
        "buy more",
        "sell more",
    ]

    for step in report.next_research_steps:
        lower_step = step.lower()
        for forbidden in forbidden_advice:
            assert forbidden not in lower_step, f"Found forbidden trading advice: '{forbidden}' in '{step}'"


def test_sharpe_ratio_is_descriptive_only(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    9. Sharpe ratio is treated as descriptive only and warns against statistical significance claims.
    """
    report = ResearchLearner.generate_report(sample_backtest_result, sample_spec)
    assert any("Sharpe ratio is descriptive in this prototype and should not be treated as evidence of statistical significance" in obs for obs in report.risk_observations)


def test_deterministic_output(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    10. Two evaluations on identical inputs produce bit-for-bit identical reports.
    """
    report1 = ResearchLearner.generate_report(sample_backtest_result, sample_spec)
    report2 = ResearchLearner.generate_report(sample_backtest_result, sample_spec)

    assert report1.model_dump() == report2.model_dump()


def test_api_learn_endpoint(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    11. POST /api/research/learn accepts ResearchLearnRequest and returns LearnReport.
    """
    resp = client.post(
        "/api/research/learn",
        json={
            "result": sample_backtest_result.model_dump(),
            "spec": sample_spec.model_dump(),
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["experiment_id"] == "EXP-TEST1234"
    assert data["evidence_level"] == "SYNTHETIC_CANDIDATE_FOR_REAL_DATA"
    assert "summary" in data
    assert "performance_observations" in data
    assert "friction_observation" in data
    assert "limitations" in data
    assert "next_research_steps" in data


def test_no_external_calls_during_learn(sample_spec: DefinedExperimentSpec, sample_backtest_result: BacktestResult):
    """
    12. Verifies that LEARN is completely offline, with zero LLM or external calls.
    """
    with patch("google.genai.Client") as mock_genai:
        resp = client.post(
            "/api/research/learn",
            json={
                "result": sample_backtest_result.model_dump(),
                "spec": sample_spec.model_dump(),
            },
        )
        assert resp.status_code == 200
        mock_genai.assert_not_called()
