import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.research import (
    ResearchExperiment,
    FieldClarification,
    ResearchClarifyRequest,
    ParameterSource,
    ExperimentStatus,
)
from app.services.experiment_clarifier import ExperimentClarifier
from app.services.research_analyzer import DeterministicMockAnalyzer

client = TestClient(app)


@pytest.fixture
async def sample_experiment() -> ResearchExperiment:
    analyzer = DeterministicMockAnalyzer()
    question = "Does buying NIFTY after a 1% fall work better during high-volatility periods?"
    return await analyzer.analyze(question)


@pytest.mark.anyio
async def test_one_missing_field_clarified(sample_experiment: ResearchExperiment):
    """
    1. One missing field clarified:
    Holding period is clarified -> holding_period updated, remains NEEDS_CLARIFICATION
    because exit condition and other gaps are still pending.
    """
    clarification = FieldClarification(field="holding_period", value="5 trading sessions")
    updated = ExperimentClarifier.clarify(sample_experiment, [clarification])

    assert updated.holding_period.value == "5 trading sessions"
    assert updated.holding_period.source == ParameterSource.USER_EXPLICIT
    assert updated.holding_period.requires_confirmation is False
    assert updated.holding_period.confidence == 1.0

    # Still needs clarification because other gaps are still pending
    assert updated.status == ExperimentStatus.NEEDS_CLARIFICATION
    missing_fields = [m.field for m in updated.missing_information]
    assert "holding_period" not in missing_fields
    assert "test_period" in missing_fields


@pytest.mark.anyio
async def test_multiple_fields_clarified(sample_experiment: ResearchExperiment):
    """
    2. Multiple fields clarified in a single call.
    """
    clarifications = [
        FieldClarification(field="holding_period", value="5 days"),
        FieldClarification(field="exit_condition", value="Exit on 2% target or 1% stop loss"),
    ]
    updated = ExperimentClarifier.clarify(sample_experiment, clarifications)

    assert updated.holding_period.value == "5 days"
    assert updated.exit_condition.value == "Exit on 2% target or 1% stop loss"
    assert updated.holding_period.source == ParameterSource.USER_EXPLICIT
    assert updated.exit_condition.source == ParameterSource.USER_EXPLICIT
    assert not updated.holding_period.requires_confirmation
    assert not updated.exit_condition.requires_confirmation

    missing_fields = [m.field for m in updated.missing_information]
    assert "holding_period" not in missing_fields
    assert "exit_condition" not in missing_fields


@pytest.mark.anyio
async def test_clarified_fields_provenance_and_confirmation(sample_experiment: ResearchExperiment):
    """
    3. Clarified fields become USER_EXPLICIT.
    4. Clarified fields no longer require confirmation.
    """
    clarifications = [
        FieldClarification(field="filters", value=["India VIX > 20"]),
    ]
    updated = ExperimentClarifier.clarify(sample_experiment, clarifications)

    assert updated.filters.value == ["India VIX > 20"]
    assert updated.filters.source == ParameterSource.USER_EXPLICIT
    assert updated.filters.requires_confirmation is False
    assert updated.filters.confidence == 1.0


@pytest.mark.anyio
async def test_remaining_missing_fields_stay_missing(sample_experiment: ResearchExperiment):
    """
    5. Remaining missing fields stay missing and are not accidentally populated.
    """
    clarifications = [
        FieldClarification(field="holding_period", value="3 days"),
    ]
    updated = ExperimentClarifier.clarify(sample_experiment, clarifications)

    assert updated.test_period.value is None
    assert updated.test_period.source == ParameterSource.MISSING
    assert updated.cost_assumptions.value is None
    assert updated.cost_assumptions.source == ParameterSource.MISSING


@pytest.mark.anyio
async def test_experiment_becomes_ready_when_all_gaps_resolved(sample_experiment: ResearchExperiment):
    """
    6. Experiment becomes READY when all critical and warning gaps are resolved according to existing validator.
    """
    clarifications = [
        FieldClarification(field="timeframe", value="1D (Daily)"),
        FieldClarification(field="exit_condition", value="Exit on 2% target"),
        FieldClarification(field="holding_period", value="5 days"),
        FieldClarification(field="filters", value=["India VIX > 20"]),
        FieldClarification(field="test_period", value="2020 to 2024"),
        FieldClarification(field="cost_assumptions", value="0.05% slippage per side"),
    ]
    updated = ExperimentClarifier.clarify(sample_experiment, clarifications)

    assert len(updated.missing_information) == 0
    assert updated.status == ExperimentStatus.READY


def test_unsupported_field_names_rejected():
    """
    7. Unsupported field names are rejected with validation error.
    """
    with pytest.raises(ValidationError):
        FieldClarification(field="unsupported_arbitrary_field", value="foo")

    with pytest.raises(ValidationError):
        FieldClarification(field="malicious_payload", value="bar")


def test_clarification_values_validation():
    """
    8. Clarification values cannot inject malformed/empty data.
    """
    with pytest.raises(ValidationError):
        FieldClarification(field="holding_period", value="")

    with pytest.raises(ValidationError):
        FieldClarification(field="holding_period", value="   ")

    with pytest.raises(ValidationError):
        FieldClarification(field="filters", value=[])


def test_api_clarify_endpoint():
    """
    9. The clarify endpoint POST /api/research/clarify returns the updated experiment.
    """
    # 1. Initial analyze
    analyze_resp = client.post(
        "/api/research/analyze",
        json={"question": "Does buying NIFTY after a 1% fall work better during high-volatility periods?"},
    )
    assert analyze_resp.status_code == 200
    initial_exp = analyze_resp.json()["experiment"]
    assert initial_exp["holding_period"]["value"] is None

    # 2. Clarify holding period
    clarify_resp = client.post(
        "/api/research/clarify",
        json={
            "experiment": initial_exp,
            "clarifications": [
                {"field": "holding_period", "value": "5 trading sessions"},
            ],
        },
    )
    assert clarify_resp.status_code == 200
    data = clarify_resp.json()
    assert data["experiment"]["holding_period"]["value"] == "5 trading sessions"
    assert data["experiment"]["holding_period"]["source"] == "USER_EXPLICIT"
    assert data["experiment"]["holding_period"]["requires_confirmation"] is False
    assert data["status"] == "NEEDS_CLARIFICATION"


def test_no_gemini_call_during_clarify():
    """
    10. No Gemini LLM call is made during clarification.
    """
    analyze_resp = client.post(
        "/api/research/analyze",
        json={"question": "Does buying NIFTY after a 1% fall work?"},
    )
    initial_exp = analyze_resp.json()["experiment"]

    # Patch google.genai.Client to ensure it is never invoked
    with patch("google.genai.Client") as mock_genai_client:
        clarify_resp = client.post(
            "/api/research/clarify",
            json={
                "experiment": initial_exp,
                "clarifications": [
                    {"field": "holding_period", "value": "5 days"},
                    {"field": "exit_condition", "value": "2% profit target"},
                ],
            },
        )
        assert clarify_resp.status_code == 200
        mock_genai_client.assert_not_called()
