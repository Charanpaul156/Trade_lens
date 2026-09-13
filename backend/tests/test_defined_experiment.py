import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.research import (
    ResearchExperiment,
    ExperimentStatus,
    ParameterSource,
    ExtractedField,
    FieldClarification,
    DefinedExperimentSpec,
    MissingInfoItem,
    MissingSeverity,
)
from app.services.experiment_clarifier import ExperimentClarifier
from app.services.research_analyzer import DeterministicMockAnalyzer

client = TestClient(app)


import asyncio


@pytest.fixture
def fully_clarified_ready_experiment() -> ResearchExperiment:
    """
    Returns an experiment where all parameters have been explicitly clarified and resolved to READY.
    """
    analyzer = DeterministicMockAnalyzer()
    exp = asyncio.run(analyzer.analyze("Does buying NIFTY after a 1% fall work better during high-volatility periods?"))

    # Clarify all missing/ambiguous parameters to achieve full READY state
    clarifications = [
        FieldClarification(field="timeframe", value="1D (Daily)"),
        FieldClarification(field="exit_condition", value="Exit on 2% target or 1% stop loss"),
        FieldClarification(field="holding_period", value="5 trading sessions"),
        FieldClarification(field="filters", value=["India VIX > 20"]),
        FieldClarification(field="test_period", value="2020 to 2024"),
        FieldClarification(field="cost_assumptions", value="0.05% slippage per side"),
    ]
    ready_exp = ExperimentClarifier.clarify(exp, clarifications)
    assert ready_exp.status == ExperimentStatus.READY
    assert len(ready_exp.missing_information) == 0
    return ready_exp


def test_valid_fully_confirmed_ready_experiment_succeeds(fully_clarified_ready_experiment: ResearchExperiment):
    """
    1. Valid fully confirmed READY experiment successfully projects into DefinedExperimentSpec.
    """
    resp = client.post(
        "/api/research/define",
        json={"experiment": fully_clarified_ready_experiment.model_dump()},
    )
    assert resp.status_code == 200
    data = resp.json()

    # Verify root fields
    assert data["research_question"] == fully_clarified_ready_experiment.research_question
    assert data["hypothesis"] == fully_clarified_ready_experiment.hypothesis

    # Verify Market Context
    assert data["market_context"]["instrument"] == "NIFTY"
    assert data["market_context"]["timeframe"] == "1D (Daily)"

    # Verify Signal Rules
    assert data["signal_rules"]["entry_condition"] == fully_clarified_ready_experiment.entry_condition.value
    assert data["signal_rules"]["filters"] == ["India VIX > 20"]

    # Verify Position Rules
    assert data["position_rules"]["exit_condition"] == "Exit on 2% target or 1% stop loss"
    assert data["position_rules"]["holding_period"] == "5 trading sessions"

    # Verify Backtest Bounds
    assert data["backtest_bounds"]["test_period"] == "2020 to 2024"
    assert data["backtest_bounds"]["cost_assumptions"] == "0.05% slippage per side"

    # Verify Provenance Audit
    audit = {item["field"]: item for item in data["provenance_audit"]}
    assert audit["instrument"]["source"] == "USER_EXPLICIT"
    assert audit["instrument"]["confidence"] == 1.0
    assert audit["instrument"]["requires_confirmation"] is False
    assert audit["entry_condition"]["source"] == "USER_EXPLICIT"
    assert audit["cost_assumptions"]["source"] == "USER_EXPLICIT"


def test_needs_clarification_is_rejected():
    """
    2. Experiments with status NEEDS_CLARIFICATION are rejected by the safety gate with HTTP 422.
    """
    # Create an experiment that needs clarification
    analyzer = DeterministicMockAnalyzer()
    import asyncio
    exp = asyncio.run(analyzer.analyze("Does buying NIFTY after a 1% fall work?"))
    assert exp.status == ExperimentStatus.NEEDS_CLARIFICATION

    resp = client.post(
        "/api/research/define",
        json={"experiment": exp.model_dump()},
    )
    assert resp.status_code == 422
    assert "status must be READY" in resp.json()["detail"]


def test_draft_is_rejected():
    """
    3. Experiments with status DRAFT are rejected by the safety gate with HTTP 422.
    """
    draft_exp = ResearchExperiment(
        research_question="Is anything good?",
        status=ExperimentStatus.DRAFT,
    )

    resp = client.post(
        "/api/research/define",
        json={"experiment": draft_exp.model_dump()},
    )
    assert resp.status_code == 422
    assert "status must be READY" in resp.json()["detail"]


def test_ready_experiment_with_requires_confirmation_rejected(fully_clarified_ready_experiment: ResearchExperiment):
    """
    4. Even if an experiment claims status READY, if any execution-critical parameter
       still has requires_confirmation == True, the DEFINE safety gate strictly rejects it.
    """
    tampered_exp = fully_clarified_ready_experiment.model_copy(deep=True)
    tampered_exp.entry_condition.requires_confirmation = True

    resp = client.post(
        "/api/research/define",
        json={"experiment": tampered_exp.model_dump()},
    )
    assert resp.status_code == 422
    assert "requires explicit user confirmation" in resp.json()["detail"]


def test_missing_execution_critical_provenance_rejected(fully_clarified_ready_experiment: ResearchExperiment):
    """
    5. Rejects experiments if critical provenance is invalid (e.g. source == MISSING or empty value).
    """
    # Empty value
    tampered_exp = fully_clarified_ready_experiment.model_copy(deep=True)
    tampered_exp.cost_assumptions.value = "   "

    resp = client.post(
        "/api/research/define",
        json={"experiment": tampered_exp.model_dump()},
    )
    assert resp.status_code == 422
    assert "missing or empty value" in resp.json()["detail"]

    # Source == MISSING
    tampered_exp2 = fully_clarified_ready_experiment.model_copy(deep=True)
    tampered_exp2.test_period.source = ParameterSource.MISSING

    resp2 = client.post(
        "/api/research/define",
        json={"experiment": tampered_exp2.model_dump()},
    )
    assert resp2.status_code == 422
    assert "invalid provenance 'MISSING'" in resp2.json()["detail"]


def test_unresolved_missing_information_rejected(fully_clarified_ready_experiment: ResearchExperiment):
    """
    6. Rejects experiments if missing_information list is non-empty.
    """
    tampered_exp = fully_clarified_ready_experiment.model_copy(deep=True)
    tampered_exp.missing_information = [
        MissingInfoItem(
            field="cost_assumptions",
            description="Fee assumptions unresolved",
            severity=MissingSeverity.CRITICAL,
            clarification_prompt="What are your cost assumptions?",
        )
    ]

    resp = client.post(
        "/api/research/define",
        json={"experiment": tampered_exp.model_dump()},
    )
    assert resp.status_code == 422
    assert "unresolved missing parameters" in resp.json()["detail"]


def test_output_contract_structure_is_correct(fully_clarified_ready_experiment: ResearchExperiment):
    """
    7. Validates that the returned DefinedExperimentSpec matches the expected schema.
    """
    spec = DefinedExperimentSpec.from_experiment(fully_clarified_ready_experiment)

    assert isinstance(spec, DefinedExperimentSpec)
    assert spec.market_context.instrument == "NIFTY"
    assert spec.market_context.timeframe == "1D (Daily)"
    assert spec.signal_rules.entry_condition == fully_clarified_ready_experiment.entry_condition.value
    assert len(spec.signal_rules.filters) == 1
    assert spec.position_rules.exit_condition == "Exit on 2% target or 1% stop loss"
    assert spec.position_rules.holding_period == "5 trading sessions"
    assert spec.backtest_bounds.test_period == "2020 to 2024"
    assert spec.backtest_bounds.cost_assumptions == "0.05% slippage per side"
    assert len(spec.provenance_audit) == 8


def test_no_llm_or_backtest_calls_occur(fully_clarified_ready_experiment: ResearchExperiment):
    """
    8. Verifies that /define is completely stateless and never invokes Gemini or external services.
    """
    with patch("google.genai.Client") as mock_genai:
        resp = client.post(
            "/api/research/define",
            json={"experiment": fully_clarified_ready_experiment.model_dump()},
        )
        assert resp.status_code == 200
        mock_genai.assert_not_called()


def test_define_succeeds_with_only_holding_period(fully_clarified_ready_experiment: ResearchExperiment):
    """
    9. Consistent with ExperimentValidator: A time-based exit strategy (holding_period only,
       no exit_condition) is valid, reaches READY, and is accepted by DEFINE.
    """
    exp = fully_clarified_ready_experiment.model_copy(deep=True)
    exp.exit_condition = ExtractedField(value=None, source=ParameterSource.MISSING)

    resp = client.post(
        "/api/research/define",
        json={"experiment": exp.model_dump()},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["position_rules"]["exit_condition"] is None
    assert data["position_rules"]["holding_period"] == "5 trading sessions"


def test_define_succeeds_with_only_exit_condition(fully_clarified_ready_experiment: ResearchExperiment):
    """
    10. Consistent with ExperimentValidator: A target/stop exit strategy (exit_condition only,
        no holding_period) is valid, reaches READY, and is accepted by DEFINE.
    """
    exp = fully_clarified_ready_experiment.model_copy(deep=True)
    exp.holding_period = ExtractedField(value=None, source=ParameterSource.MISSING)

    resp = client.post(
        "/api/research/define",
        json={"experiment": exp.model_dump()},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["position_rules"]["exit_condition"] == "Exit on 2% target or 1% stop loss"
    assert data["position_rules"]["holding_period"] is None


def test_define_rejects_when_both_exit_rules_missing(fully_clarified_ready_experiment: ResearchExperiment):
    """
    11. Rejects if BOTH position exit rules (exit_condition AND holding_period) are missing.
    """
    exp = fully_clarified_ready_experiment.model_copy(deep=True)
    exp.exit_condition = ExtractedField(value=None, source=ParameterSource.MISSING)
    exp.holding_period = ExtractedField(value=None, source=ParameterSource.MISSING)

    resp = client.post(
        "/api/research/define",
        json={"experiment": exp.model_dump()},
    )
    assert resp.status_code == 422
    assert "At least one position exit rule" in resp.json()["detail"]


def test_define_rejects_when_exit_rule_requires_confirmation(fully_clarified_ready_experiment: ResearchExperiment):
    """
    12. Rejects if an existing exit rule requires confirmation.
    """
    exp1 = fully_clarified_ready_experiment.model_copy(deep=True)
    exp1.exit_condition.requires_confirmation = True

    resp1 = client.post(
        "/api/research/define",
        json={"experiment": exp1.model_dump()},
    )
    assert resp1.status_code == 422
    assert "exit_condition' requires explicit user confirmation" in resp1.json()["detail"]

    exp2 = fully_clarified_ready_experiment.model_copy(deep=True)
    exp2.holding_period.requires_confirmation = True

    resp2 = client.post(
        "/api/research/define",
        json={"experiment": exp2.model_dump()},
    )
    assert resp2.status_code == 422
    assert "holding_period' requires explicit user confirmation" in resp2.json()["detail"]

