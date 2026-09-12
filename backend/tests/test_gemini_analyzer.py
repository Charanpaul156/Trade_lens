import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.research import (
    ResearchExperiment,
    ExtractedField,
    ParameterSource,
    ExperimentStatus,
)
from app.services.research_analyzer import (
    GeminiResearchAnalyzer,
    DeterministicMockAnalyzer,
    get_research_analyzer,
)
from app.core.config import settings


@pytest.mark.anyio
async def test_gemini_analyzer_fallback_when_no_api_key():
    """
    When no Gemini API key is provided, the analyzer should gracefully
    delegate to the DeterministicMockAnalyzer.
    """
    analyzer = GeminiResearchAnalyzer(api_key=None)
    assert analyzer._client is None

    question = "Does buying NIFTY after a 1% fall work better during high-volatility periods?"
    experiment = await analyzer.analyze(question)

    assert isinstance(experiment, ResearchExperiment)
    assert experiment.instrument.value == "NIFTY"
    assert experiment.instrument.source == ParameterSource.USER_EXPLICIT
    assert experiment.status == ExperimentStatus.NEEDS_CLARIFICATION


@pytest.mark.anyio
async def test_gemini_analyzer_fallback_on_api_error():
    """
    When Gemini API call encounters an error (e.g. quota, network),
    it should catch the exception and gracefully fall back to the mock analyzer.
    """
    analyzer = GeminiResearchAnalyzer(api_key="test-dummy-key")
    assert analyzer._client is not None

    # Mock the client's async generate_content to raise an error
    mock_aio_generate = AsyncMock(side_effect=RuntimeError("Google GenAI Rate Limit or Network Error"))
    analyzer._client.aio.models.generate_content = mock_aio_generate

    question = "Does buying AAPL on 2% dip work?"
    experiment = await analyzer.analyze(question)

    assert isinstance(experiment, ResearchExperiment)
    assert experiment.instrument.value == "AAPL"
    assert experiment.status == ExperimentStatus.NEEDS_CLARIFICATION


@pytest.mark.anyio
async def test_gemini_analyzer_success_with_mocked_gemini_response():
    """
    When Gemini API succeeds, it should parse the structured JSON response
    and run through ExperimentValidator.
    """
    analyzer = GeminiResearchAnalyzer(api_key="test-dummy-key")

    mock_experiment_data = {
        "research_question": "Does buying NIFTY after a 1% fall work?",
        "hypothesis": "Buying NIFTY after 1% fall yields positive excess returns over 5 days.",
        "status": "NEEDS_CLARIFICATION",
        "instrument": {
            "value": "NIFTY",
            "source": "USER_EXPLICIT",
            "confidence": 0.98,
            "requires_confirmation": False,
            "raw_text": "NIFTY",
            "notes": None,
        },
        "timeframe": {
            "value": "1D (Daily)",
            "source": "AI_INFERRED",
            "confidence": 0.8,
            "requires_confirmation": True,
            "raw_text": None,
            "notes": "Inferred standard daily timeframe",
        },
        "entry_condition": {
            "value": "NIFTY drops >= 1.0%",
            "source": "USER_EXPLICIT",
            "confidence": 0.95,
            "requires_confirmation": False,
            "raw_text": "1% fall",
            "notes": None,
        },
        "exit_condition": {
            "value": None,
            "source": "MISSING",
            "confidence": 0.0,
            "requires_confirmation": True,
            "raw_text": None,
            "notes": "No exit condition specified",
        },
        "holding_period": {
            "value": None,
            "source": "MISSING",
            "confidence": 0.0,
            "requires_confirmation": True,
            "raw_text": None,
            "notes": "No holding period specified",
        },
        "filters": {
            "value": [],
            "source": "MISSING",
            "confidence": 1.0,
            "requires_confirmation": False,
            "raw_text": None,
            "notes": None,
        },
        "test_period": {
            "value": None,
            "source": "MISSING",
            "confidence": 0.0,
            "requires_confirmation": True,
            "raw_text": None,
            "notes": None,
        },
        "cost_assumptions": {
            "value": None,
            "source": "MISSING",
            "confidence": 0.0,
            "requires_confirmation": True,
            "raw_text": None,
            "notes": None,
        },
        "missing_information": [],
    }

    mock_response = MagicMock()
    mock_response.text = json.dumps(mock_experiment_data)

    mock_aio_generate = AsyncMock(return_value=mock_response)
    analyzer._client.aio.models.generate_content = mock_aio_generate

    question = "Does buying NIFTY after a 1% fall work?"
    experiment = await analyzer.analyze(question)

    assert experiment.instrument.value == "NIFTY"
    assert experiment.entry_condition.value == "NIFTY drops >= 1.0%"
    assert experiment.timeframe.source == ParameterSource.AI_INFERRED
    # Check validator compiled missing information
    missing_fields = [m.field for m in experiment.missing_information]
    assert "exit_condition" in missing_fields
    assert "holding_period" in missing_fields
    assert experiment.status == ExperimentStatus.NEEDS_CLARIFICATION


def test_get_research_analyzer_factory():
    """
    Test dependency injection factory switching.
    """
    with patch.object(settings, "RESEARCH_ANALYZER_PROVIDER", "mock"):
        analyzer = get_research_analyzer()
        assert isinstance(analyzer, DeterministicMockAnalyzer)

    with patch.object(settings, "RESEARCH_ANALYZER_PROVIDER", "gemini"):
        with patch.object(settings, "GEMINI_API_KEY", "test-key"):
            analyzer = get_research_analyzer()
            assert isinstance(analyzer, GeminiResearchAnalyzer)
            assert analyzer.api_key == "test-key"
