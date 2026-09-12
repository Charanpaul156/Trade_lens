from abc import ABC, abstractmethod
import re
from typing import List, Optional

from app.schemas.research import (
    ResearchExperiment,
    ExtractedField,
    ParameterSource,
    ExperimentStatus,
)
from app.services.experiment_validator import ExperimentValidator


class BaseResearchAnalyzer(ABC):
    """
    Abstract interface for AI Research Analyzers.
    Decouples natural language interpretation from API routes and allows
    seamless swapping between deterministic mock analyzers and real LLMs (e.g. Gemini).
    """

    @abstractmethod
    async def analyze(self, question: str) -> ResearchExperiment:
        """
        Analyze a natural language trading question into a structured ResearchExperiment.
        """
        pass


class DeterministicMockAnalyzer(BaseResearchAnalyzer):
    """
    Rule-based deterministic analyzer for testing and offline environments.
    Strictly adheres to the product principle:
    - Distinguishes USER_EXPLICIT from AI_INFERRED
    - Flags ambiguous terms (e.g., 'sharp fall') with requires_confirmation=True
    - Does NOT blindly invent exit conditions, holding periods, or test periods
    """

    KNOWN_INSTRUMENTS = [
        "NIFTY 50", "NIFTY50", "NIFTY", "BANKNIFTY", "BANK NIFTY",
        "FINNIFTY", "SENSEX", "SPY", "QQQ", "AAPL", "MSFT", "TSLA",
        "BTC", "ETH", "CRUDE OIL", "GOLD"
    ]

    async def analyze(self, question: str) -> ResearchExperiment:
        cleaned_question = question.strip()

        # 1. Extract Instrument
        instrument_field = self._extract_instrument(cleaned_question)

        # 2. Extract Entry Condition
        entry_field = self._extract_entry_condition(cleaned_question, instrument_field.value)

        # 3. Extract Timeframe
        timeframe_field = self._extract_timeframe(cleaned_question)

        # 4. Extract Filters
        filters_field = self._extract_filters(cleaned_question)

        # 5. Extract Holding Period
        holding_field = self._extract_holding_period(cleaned_question)

        # 6. Extract Exit Condition
        exit_field = self._extract_exit_condition(cleaned_question)

        # 7. Extract Test Period
        test_period_field = self._extract_test_period(cleaned_question)

        # 8. Extract Cost Assumptions
        cost_field = self._extract_cost_assumptions(cleaned_question)

        # 9. Formulate Hypothesis
        hypothesis = self._formulate_hypothesis(
            instrument=instrument_field.value,
            entry=entry_field.value,
            filters=filters_field.value,
            question=cleaned_question,
        )

        experiment = ResearchExperiment(
            research_question=cleaned_question,
            hypothesis=hypothesis,
            status=ExperimentStatus.NEEDS_CLARIFICATION,
            instrument=instrument_field,
            timeframe=timeframe_field,
            entry_condition=entry_field,
            exit_condition=exit_field,
            holding_period=holding_field,
            filters=filters_field,
            test_period=test_period_field,
            cost_assumptions=cost_field,
            missing_information=[],
        )

        # Run validation engine to compile missing information and determine final status
        return ExperimentValidator.validate(experiment)

    def _extract_instrument(self, text: str) -> ExtractedField[str]:
        for inst in self.KNOWN_INSTRUMENTS:
            pattern = rf"\b{re.escape(inst)}\b"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                matched_text = match.group(0)
                normalized = "NIFTY" if "NIFTY" in matched_text.upper() and "BANK" not in matched_text.upper() and "FIN" not in matched_text.upper() else matched_text.upper()
                return ExtractedField(
                    value=normalized,
                    source=ParameterSource.USER_EXPLICIT,
                    confidence=1.0,
                    requires_confirmation=False,
                    raw_text=matched_text,
                )
        
        # Generic symbol detection (e.g. $TICKER or all-caps word)
        symbol_match = re.search(r"\$([A-Z]{2,6})\b", text)
        if symbol_match:
            return ExtractedField(
                value=symbol_match.group(1),
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.9,
                requires_confirmation=False,
                raw_text=symbol_match.group(0),
            )

        return ExtractedField(
            value=None,
            source=ParameterSource.MISSING,
            confidence=0.0,
            requires_confirmation=True,
            notes="No identifiable financial instrument or ticker found in the question.",
        )

    def _extract_entry_condition(self, text: str, instrument: Optional[str]) -> ExtractedField[str]:
        # Check for quantified percentage drop: e.g. "1% fall", "falls by 2%", "after a 1.5% drop", "2% dip"
        pct_match = re.search(r"(?:after\s+(?:a\s+)?)?(\d+(?:\.\d+)?)\s*%\s*(?:fall|drop|decline|dip|down|pullback)", text, re.IGNORECASE)
        if pct_match:
            pct = pct_match.group(1)
            inst_str = instrument or "Asset"
            return ExtractedField(
                value=f"{inst_str} falls by at least {pct}%",
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.95,
                requires_confirmation=False,
                raw_text=pct_match.group(0),
                notes=f"Extracted quantified entry threshold of {pct}%.",
            )

        # Check for unquantified / ambiguous drops: e.g. "sharp fall", "big crash", "severe drop", "plunge"
        ambiguous_match = re.search(r"\b(sharp\s+fall|sharp\s+drop|big\s+drop|market\s+crash|heavy\s+selling|plunge)\b", text, re.IGNORECASE)
        if ambiguous_match:
            matched_phrase = ambiguous_match.group(1)
            inst_str = instrument or "Asset"
            return ExtractedField(
                value=f"{inst_str} experiences a {matched_phrase.lower()}",
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.4,
                requires_confirmation=True,
                raw_text=matched_phrase,
                notes=f"Ambiguous entry trigger: '{matched_phrase}' is subjective. Quantitative backtesting requires an exact numerical threshold (e.g. 1%, 2%, or 2 standard deviations).",
            )

        # Check for general "buying" without specific entry
        if re.search(r"\b(buy|buying|long)\b", text, re.IGNORECASE):
            return ExtractedField(
                value=None,
                source=ParameterSource.MISSING,
                confidence=0.0,
                requires_confirmation=True,
                notes="The question mentions buying but does not define a measurable entry rule or trigger.",
            )

        return ExtractedField(
            value=None,
            source=ParameterSource.MISSING,
            confidence=0.0,
            requires_confirmation=True,
            notes="No entry condition specified in research question.",
        )

    def _extract_timeframe(self, text: str) -> ExtractedField[str]:
        # Explicit timeframe detection
        if re.search(r"\b(daily|1d|day\s+chart|end\s+of\s+day|eod)\b", text, re.IGNORECASE):
            return ExtractedField(
                value="1D (Daily)",
                source=ParameterSource.USER_EXPLICIT,
                confidence=1.0,
                requires_confirmation=False,
                raw_text="daily",
            )
        if re.search(r"\b(hourly|1h|60m|60\s*min)\b", text, re.IGNORECASE):
            return ExtractedField(
                value="1H (Hourly)",
                source=ParameterSource.USER_EXPLICIT,
                confidence=1.0,
                requires_confirmation=False,
                raw_text="hourly",
            )
        if re.search(r"\b(intraday|5m|15m)\b", text, re.IGNORECASE):
            return ExtractedField(
                value="Intraday",
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.9,
                requires_confirmation=False,
                raw_text="intraday",
            )

        # Inferred timeframe: Standard convention for percentage dips is Daily (1D), but mark as AI_INFERRED
        return ExtractedField(
            value="1D (Daily)",
            source=ParameterSource.AI_INFERRED,
            confidence=0.7,
            requires_confirmation=True,
            raw_text=None,
            notes="Timeframe was not explicitly stated; inferred Daily (1D) as default convention for percentage drop analysis.",
        )

    def _extract_filters(self, text: str) -> ExtractedField[List[str]]:
        filters: List[str] = []
        is_unquantified_regime = False
        notes = None

        if re.search(r"\b(high[- ]volatility|turbulent)\b", text, re.IGNORECASE):
            filters.append("High volatility regime")
            is_unquantified_regime = True
            notes = "User specified qualitative high volatility. Quantitative backtesting requires an explicit volatility definition (e.g., India VIX or historical volatility percentile), which requires user confirmation."
        elif re.search(r"\b(elevated\s+vix|high\s+vix)\b", text, re.IGNORECASE):
            filters.append("High VIX regime")
            is_unquantified_regime = True
            notes = "VIX regime specified without explicit numerical threshold. Numerical threshold requires user confirmation."

        if re.search(r"\b(low[- ]volatility|calm\s+market)\b", text, re.IGNORECASE):
            filters.append("Low volatility regime")
            is_unquantified_regime = True
            notes = "User specified qualitative low volatility. Quantitative threshold requires user confirmation."

        if re.search(r"\b(uptrend|above\s+200\s*dma|bull\s+market)\b", text, re.IGNORECASE):
            filters.append("Trend filter: Price above 200-day moving average")

        if filters:
            return ExtractedField(
                value=filters,
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.75 if is_unquantified_regime else 0.9,
                requires_confirmation=is_unquantified_regime,
                raw_text=", ".join(filters),
                notes=notes,
            )

        return ExtractedField(
            value=[],
            source=ParameterSource.MISSING,
            confidence=1.0,
            requires_confirmation=False,
            notes="No secondary market regime or indicator filters specified.",
        )

    def _extract_holding_period(self, text: str) -> ExtractedField[str]:
        # e.g. "hold for 5 days", "holding period of 10 days", "held for 1 week", "exit after 5 days"
        hold_match = re.search(r"\b(?:hold(?:ing)?(?:\s+period)?(?:\s+for)?|held\s+for|exit\s+(?:after|in)|exiting\s+(?:after|in))\s+(\d+)\s*(days?|sessions?|weeks?|months?)\b", text, re.IGNORECASE)
        if hold_match:
            num = hold_match.group(1)
            unit = hold_match.group(2).lower()
            return ExtractedField(
                value=f"{num} {unit}",
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.95,
                requires_confirmation=False,
                raw_text=hold_match.group(0),
            )

        # Do NOT invent holding period!
        return ExtractedField(
            value=None,
            source=ParameterSource.MISSING,
            confidence=0.0,
            requires_confirmation=True,
            notes="Holding period was not specified by the user.",
        )

    def _extract_exit_condition(self, text: str) -> ExtractedField[str]:
        # e.g. "target 2%", "stop loss 1%", "exit on 2% gain"
        exit_match = re.search(r"\b(target|stop[- ]loss|take[- ]profit|exit\s+(?:on|at))\s+(\d+(?:\.\d+)?%?)\b", text, re.IGNORECASE)
        if exit_match:
            return ExtractedField(
                value=exit_match.group(0),
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.9,
                requires_confirmation=False,
                raw_text=exit_match.group(0),
            )

        # Check for time-based exit condition (e.g. "exit after 5 days", "exit after 1 session")
        time_exit_match = re.search(r"\b(exit\s+(?:after|in)\s+\d+\s*(?:days?|sessions?|weeks?|months?))\b", text, re.IGNORECASE)
        if time_exit_match:
            return ExtractedField(
                value=time_exit_match.group(0),
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.95,
                requires_confirmation=False,
                raw_text=time_exit_match.group(0),
            )

        # Do NOT invent exit condition!
        return ExtractedField(
            value=None,
            source=ParameterSource.MISSING,
            confidence=0.0,
            requires_confirmation=True,
            notes="Exit condition (profit target, trailing stop, or stop loss) was not specified by the user.",
        )

    def _extract_test_period(self, text: str) -> ExtractedField[str]:
        # e.g. "from 2020 to 2024", "last 5 years"
        period_match = re.search(r"\b(?:between|from)\s+(\d{4})\s+(?:and|to)\s+(\d{4})\b", text, re.IGNORECASE)
        if period_match:
            return ExtractedField(
                value=f"{period_match.group(1)} - {period_match.group(2)}",
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.95,
                requires_confirmation=False,
                raw_text=period_match.group(0),
            )
        
        # Do NOT invent test period!
        return ExtractedField(
            value=None,
            source=ParameterSource.MISSING,
            confidence=0.0,
            requires_confirmation=True,
            notes="Historical test date range not specified by the user.",
        )

    def _extract_cost_assumptions(self, text: str) -> ExtractedField[str]:
        cost_match = re.search(r"\b(\d+(?:\.\d+)?%?\s*(?:slippage|brokerage|fees|costs?))\b", text, re.IGNORECASE)
        if cost_match:
            return ExtractedField(
                value=cost_match.group(1),
                source=ParameterSource.USER_EXPLICIT,
                confidence=0.9,
                requires_confirmation=False,
                raw_text=cost_match.group(0),
            )

        # Do NOT invent cost assumptions!
        return ExtractedField(
            value=None,
            source=ParameterSource.MISSING,
            confidence=0.0,
            requires_confirmation=True,
            notes="Transaction costs, friction, and slippage assumptions not specified by the user.",
        )

    def _formulate_hypothesis(
        self,
        instrument: Optional[str],
        entry: Optional[str],
        filters: Optional[List[str]],
        question: str,
    ) -> str:
        inst = instrument or "the underlying asset"
        entry_str = entry or "the specified entry condition"
        filter_str = f" during {filters[0].lower()}" if filters else ""

        return (
            f"Entering a long position in {inst} following {entry_str}{filter_str} "
            f"demonstrates a statistically significant positive forward excess return compared to the unconditional baseline."
        )


class GeminiResearchAnalyzer(BaseResearchAnalyzer):
    """
    Production-grade AI Research Analyzer powered by Google Gemini API (google-genai SDK).
    Extracts structured research experiment specifications with strict parameter provenance:
    - Distinguishes USER_EXPLICIT from AI_INFERRED parameters
    - Never hallucinates or blindly invents unmentioned exit conditions or holding periods
    - Identifies subjective/ambiguous conditions and flags them for confirmation
    - Resilient: gracefully falls back to DeterministicMockAnalyzer if API key is absent or on network/API failure
    """

    SYSTEM_INSTRUCTION = """You are an expert quantitative trading research assistant for TradeLens AI.
Your role is to translate natural language trading ideas and hypotheses into structured quantitative research experiments with rigorous parameter provenance tracking.

MANDATORY RULES:
1. Provenance Attribution:
   - Mark source as "USER_EXPLICIT" ONLY if the parameter was explicitly stated in the user question.
   - Mark source as "AI_INFERRED" if the parameter is deduced from market conventions (e.g., Daily/1D timeframe when not stated).
   - Mark source as "MISSING" with value=null if not mentioned and cannot be deduced.
2. DO NOT INVENT PARAMETERS:
   - Never hallucinate exit conditions (stop-loss / take-profit), holding periods, historical backtest dates, or cost assumptions if the user didn't specify them. Set their value to null, source to "MISSING", and requires_confirmation to true.
3. Ambiguity Quantification:
   - Identify unquantified or subjective phrases (e.g., 'sharp fall', 'market crash', 'heavy drop', 'dip'). Set requires_confirmation=true and confidence < 0.8, noting that quantitative backtesting requires an exact numerical threshold (e.g. 1%, 2%, or 2 standard deviations).
4. Market Regimes & Volatility Filters:
   - If the user mentions qualitative market regimes (e.g. 'high-volatility periods'), extract the qualitative filter ("High volatility regime") with source "USER_EXPLICIT", but set requires_confirmation=true and confidence <= 0.8.
   - Do NOT convert qualitative volatility into a specific threshold (e.g., "VIX above 75th percentile") and mark that threshold USER_EXPLICIT. Any suggested definition must be AI_INFERRED and require user confirmation. Do not silently invent a volatility threshold.
5. Academic Hypothesis Formulation:
   - Formulate a formal, testable null/alternative quantitative hypothesis.
"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        fallback_analyzer: Optional[BaseResearchAnalyzer] = None,
    ):
        import logging
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        self.fallback_analyzer = fallback_analyzer or DeterministicMockAnalyzer()
        self._client = None

        if self.api_key and self.api_key.strip():
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key.strip())
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini Client: {e}. Fallback analyzer will be used.")

    async def analyze(self, question: str) -> ResearchExperiment:
        cleaned_question = question.strip()

        # If no client or API key is configured, gracefully delegate to fallback mock analyzer
        if not self._client:
            self.logger.info("Gemini API key not configured or client uninitialized. Using deterministic analyzer fallback.")
            return await self.fallback_analyzer.analyze(cleaned_question)

        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                system_instruction=self.SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ResearchExperiment,
                temperature=0.1,
            )

            prompt = f"Analyze this trading research question and extract the experiment parameters:\n\n\"{cleaned_question}\""
            
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )

            if not response.text:
                raise ValueError("Gemini returned an empty response.")

            # Validate and parse into Pydantic model
            experiment = ResearchExperiment.model_validate_json(response.text)
            experiment.research_question = cleaned_question

            # Ensure filters list is populated
            if experiment.filters.value is None:
                experiment.filters.value = []

            # Post-validate with ExperimentValidator to ensure uniform gap analysis and status determination
            return ExperimentValidator.validate(experiment)

        except Exception as exc:
            self.logger.warning(
                f"Gemini API analysis failed with error: {exc}. Gracefully falling back to deterministic mock analyzer."
            )
            fallback_result = await self.fallback_analyzer.analyze(cleaned_question)
            return fallback_result


def get_research_analyzer() -> BaseResearchAnalyzer:
    """
    Dependency injection provider for Research Analyzer.
    Instantiates GeminiResearchAnalyzer if provider is 'gemini'.
    GeminiResearchAnalyzer handles missing API keys and errors by gracefully
    falling back to DeterministicMockAnalyzer.
    """
    from app.core.config import settings

    provider = (settings.RESEARCH_ANALYZER_PROVIDER or "gemini").lower()
    if provider == "gemini":
        return GeminiResearchAnalyzer(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
        )
    return DeterministicMockAnalyzer()

