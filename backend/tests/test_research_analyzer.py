import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.research import (
    ExperimentStatus,
    ParameterSource,
    MissingSeverity,
)
from app.services.research_analyzer import DeterministicMockAnalyzer

client = TestClient(app)


class TestResearchAnalyzer:
    """
    Unit test suite for the DeterministicMockAnalyzer service.
    """

    @pytest.mark.anyio
    async def test_complete_ish_question_with_explicit_instrument_and_entry(self):
        """
        Case 1: 'Does buying NIFTY after a 1% fall work better during high-volatility periods?'
        Should extract:
        - Instrument: NIFTY (USER_EXPLICIT, requires_confirmation=False)
        - Entry: falls by at least 1% (USER_EXPLICIT)
        - Filter: High volatility regime (USER_EXPLICIT)
        - Timeframe: Daily (AI_INFERRED, requires_confirmation=True)
        - Missing: exit_condition, holding_period, test_period, cost_assumptions
        - Status: NEEDS_CLARIFICATION
        """
        analyzer = DeterministicMockAnalyzer()
        question = "Does buying NIFTY after a 1% fall work better during high-volatility periods?"
        experiment = await analyzer.analyze(question)

        # Instrument assertion
        assert experiment.instrument.value == "NIFTY"
        assert experiment.instrument.source == ParameterSource.USER_EXPLICIT
        assert not experiment.instrument.requires_confirmation

        # Entry condition assertion
        assert "falls by at least 1" in experiment.entry_condition.value
        assert experiment.entry_condition.source == ParameterSource.USER_EXPLICIT
        assert not experiment.entry_condition.requires_confirmation

        # Filter assertion
        assert len(experiment.filters.value) >= 1
        assert "volatility" in experiment.filters.value[0].lower()
        assert experiment.filters.source == ParameterSource.USER_EXPLICIT

        # Timeframe provenance: must be AI_INFERRED, not USER_EXPLICIT!
        assert experiment.timeframe.source == ParameterSource.AI_INFERRED
        assert experiment.timeframe.requires_confirmation is True

        # Exit and holding period must NOT be invented
        assert experiment.exit_condition.value is None
        assert experiment.exit_condition.source == ParameterSource.MISSING
        assert experiment.holding_period.value is None
        assert experiment.holding_period.source == ParameterSource.MISSING

        # Missing information check
        missing_fields = [item.field for item in experiment.missing_information]
        assert "exit_condition" in missing_fields
        assert "holding_period" in missing_fields

        # Status check
        assert experiment.status == ExperimentStatus.NEEDS_CLARIFICATION

    @pytest.mark.anyio
    async def test_ambiguous_question_sharp_fall(self):
        """
        Case 2: 'Does buying NIFTY after a sharp fall work?'
        'sharp fall' is subjective and not quantified.
        System must flag entry_condition with requires_confirmation=True and lower confidence.
        """
        analyzer = DeterministicMockAnalyzer()
        question = "Does buying NIFTY after a sharp fall work?"
        experiment = await analyzer.analyze(question)

        assert experiment.instrument.value == "NIFTY"
        assert experiment.entry_condition.value is not None
        assert "sharp fall" in experiment.entry_condition.value.lower()
        # Must require confirmation because it's not a concrete numerical rule
        assert experiment.entry_condition.requires_confirmation is True
        assert experiment.entry_condition.confidence < 0.8

        # Missing information must contain prompt for entry condition quantification
        entry_missing = next((item for item in experiment.missing_information if item.field == "entry_condition"), None)
        assert entry_missing is not None
        assert entry_missing.severity == MissingSeverity.CRITICAL

        assert experiment.status == ExperimentStatus.NEEDS_CLARIFICATION

    @pytest.mark.anyio
    async def test_question_missing_holding_period(self):
        """
        Case 3: 'Does buying AAPL on 2% dip work?'
        No holding period or exit rule specified.
        System must NOT hallucinate a holding period and must identify both as missing.
        """
        analyzer = DeterministicMockAnalyzer()
        question = "Does buying AAPL on 2% dip work?"
        experiment = await analyzer.analyze(question)

        assert experiment.instrument.value == "AAPL"
        assert "2%" in experiment.entry_condition.value
        assert experiment.holding_period.value is None
        assert experiment.holding_period.source == ParameterSource.MISSING
        assert experiment.exit_condition.value is None
        assert experiment.exit_condition.source == ParameterSource.MISSING

        missing_fields = {item.field: item for item in experiment.missing_information}
        assert "holding_period" in missing_fields
        assert "exit_condition" in missing_fields
        assert missing_fields["holding_period"].severity == MissingSeverity.CRITICAL

        assert experiment.status == ExperimentStatus.NEEDS_CLARIFICATION


class TestResearchApiEndpoints:
    """
    API Integration tests for POST /api/research/analyze.
    """

    def test_api_analyze_success(self):
        payload = {
            "question": "Does buying NIFTY after a 1% fall work better during high-volatility periods?"
        }
        response = client.post("/api/research/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "NEEDS_CLARIFICATION"
        assert "experiment" in data
        assert data["experiment"]["instrument"]["value"] == "NIFTY"
        assert data["experiment"]["instrument"]["source"] == "USER_EXPLICIT"
        assert data["experiment"]["timeframe"]["source"] == "AI_INFERRED"
        assert data["experiment"]["timeframe"]["requires_confirmation"] is True
        assert len(data["missing_information"]) > 0

    def test_api_analyze_ambiguous(self):
        payload = {
            "question": "Does buying NIFTY after a sharp fall work?"
        }
        response = client.post("/api/research/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "NEEDS_CLARIFICATION"
        assert data["experiment"]["entry_condition"]["requires_confirmation"] is True
        missing_fields = [item["field"] for item in data["missing_information"]]
        assert "entry_condition" in missing_fields

    def test_api_analyze_empty_question(self):
        """
        Case 4: Empty / whitespace / short question.
        Should return HTTP 422 Unprocessable Entity.
        """
        # Completely empty
        resp1 = client.post("/api/research/analyze", json={"question": ""})
        assert resp1.status_code == 422

        # Pure whitespace
        resp2 = client.post("/api/research/analyze", json={"question": "   "})
        assert resp2.status_code == 422

        # Too short (< 3 characters)
        resp3 = client.post("/api/research/analyze", json={"question": "hi"})
        assert resp3.status_code == 422
