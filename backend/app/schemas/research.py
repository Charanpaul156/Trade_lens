from enum import Enum
from typing import Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field, field_validator


class ExperimentStatus(str, Enum):
    DRAFT = "DRAFT"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    READY = "READY"


class ParameterSource(str, Enum):
    USER_EXPLICIT = "USER_EXPLICIT"
    AI_INFERRED = "AI_INFERRED"
    SYSTEM_DEFAULT = "SYSTEM_DEFAULT"
    MISSING = "MISSING"


class MissingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


T = TypeVar("T")


class ExtractedField(BaseModel, Generic[T]):
    """
    Wraps an experiment parameter with full provenance tracking.
    Ensures that AI inferences are never silently converted into confirmed user parameters.
    """
    value: Optional[T] = Field(default=None, description="Extracted or inferred parameter value")
    source: ParameterSource = Field(default=ParameterSource.MISSING, description="Provenance origin of this parameter")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    requires_confirmation: bool = Field(default=False, description="Whether explicit user confirmation is needed before execution")
    raw_text: Optional[str] = Field(default=None, description="Exact substring or trigger phrase from the user prompt")
    notes: Optional[str] = Field(default=None, description="Reasoning, ambiguity note, or clarification prompt")


class MissingInfoItem(BaseModel):
    """
    Identifies a missing or ambiguous parameter required for backtesting and quantitative rigor.
    """
    field: str = Field(..., description="Target parameter name")
    description: str = Field(..., description="Explanation of what is missing or ambiguous")
    severity: MissingSeverity = Field(default=MissingSeverity.CRITICAL, description="Severity level of the missing information")
    clarification_prompt: str = Field(..., description="Direct question to ask the user to resolve this gap")
    suggested_defaults: Optional[List[str]] = Field(default=None, description="Actionable options or standard conventions")


class ResearchExperiment(BaseModel):
    """
    Structured research experiment model for quantitative hypothesis testing.
    """
    research_question: str = Field(..., description="The user's original research question")
    hypothesis: Optional[str] = Field(default=None, description="Formal academic/quantitative hypothesis formulated from the question")
    status: ExperimentStatus = Field(default=ExperimentStatus.NEEDS_CLARIFICATION, description="Validation readiness status")
    
    # Core Strategy Parameters
    instrument: ExtractedField[str] = Field(default_factory=ExtractedField, description="Target financial asset or ticker (e.g. NIFTY, SPY)")
    timeframe: ExtractedField[str] = Field(default_factory=ExtractedField, description="Bar aggregation timeframe (e.g. 1D, 1H, 15m)")
    entry_condition: ExtractedField[str] = Field(default_factory=ExtractedField, description="Quantified rule for entering a position")
    exit_condition: ExtractedField[str] = Field(default_factory=ExtractedField, description="Rule for exiting the position (stop loss / take profit)")
    holding_period: ExtractedField[str] = Field(default_factory=ExtractedField, description="Explicit duration or time limit for holding the trade")
    filters: ExtractedField[List[str]] = Field(default_factory=lambda: ExtractedField(value=[]), description="Regime, volatility, or contextual market filters")
    test_period: ExtractedField[str] = Field(default_factory=ExtractedField, description="Historical sample date range for backtest")
    cost_assumptions: ExtractedField[str] = Field(default_factory=ExtractedField, description="Slippage, commissions, and transaction cost model")
    
    # Gap Analysis
    missing_information: List[MissingInfoItem] = Field(default_factory=list, description="List of missing parameters requiring clarification")


class ResearchAnalyzeRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        description="Natural language trading idea or research question",
        examples=["Does buying NIFTY after a 1% fall work better during high-volatility periods?"]
    )


class ResearchAnalyzeResponse(BaseModel):
    status: ExperimentStatus = Field(..., description="Overall experiment validation status")
    experiment: ResearchExperiment = Field(..., description="Structured experiment specification")
    missing_information: List[MissingInfoItem] = Field(default_factory=list, description="All identified missing parameters")


SUPPORTED_EXPERIMENT_FIELDS = {
    "instrument",
    "timeframe",
    "entry_condition",
    "exit_condition",
    "holding_period",
    "filters",
    "test_period",
    "cost_assumptions",
}


class FieldClarification(BaseModel):
    """
    Structured user response to a parameter clarification prompt.
    """
    field: str = Field(..., description="Target parameter name to update")
    value: Union[str, List[str]] = Field(..., description="User's clarified value or selected default")

    @field_validator("field")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in SUPPORTED_EXPERIMENT_FIELDS:
            raise ValueError(
                f"Unsupported experiment field '{v}'. Supported fields are: {sorted(list(SUPPORTED_EXPERIMENT_FIELDS))}"
            )
        return clean

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: Union[str, List[str]]) -> Union[str, List[str]]:
        if isinstance(v, str):
            if not v.strip():
                raise ValueError("Clarification value cannot be empty or whitespace.")
            return v.strip()
        elif isinstance(v, list):
            cleaned = [item.strip() for item in v if isinstance(item, str) and item.strip()]
            if not cleaned:
                raise ValueError("Clarification list value cannot be empty.")
            return cleaned
        raise ValueError("Clarification value must be a string or a list of strings.")


class ResearchClarifyRequest(BaseModel):
    """
    Request model for applying structured user clarifications to an existing ResearchExperiment.
    """
    experiment: ResearchExperiment = Field(..., description="The existing structured experiment to refine")
    clarifications: List[FieldClarification] = Field(
        ...,
        min_length=1,
        description="One or more field clarifications provided by the user",
    )


class ParameterProvenanceRecord(BaseModel):
    """
    Audit record capturing the origin and confirmation status of an execution parameter.
    """
    field: str
    source: ParameterSource
    confidence: float
    requires_confirmation: bool = False


class DefinedMarketContext(BaseModel):
    """
    Target trading asset and candle bar aggregation interval.
    """
    instrument: str
    timeframe: str


class DefinedSignalRules(BaseModel):
    """
    Explicit entry rules and contextual market regime filters.
    """
    entry_condition: str
    filters: List[str] = Field(default_factory=list)


class DefinedPositionRules(BaseModel):
    """
    Risk parameters, exit triggers, and maximum trade holding duration.
    """
    exit_condition: Optional[str] = None
    holding_period: Optional[str] = None


class DefinedBacktestBounds(BaseModel):
    """
    Historical sample date range and transaction friction / slippage assumptions.
    """
    test_period: str
    cost_assumptions: str


class DefinedExperimentSpec(BaseModel):
    """
    Derived execution-contract projection representing a finalized research experiment
    ready for quantitative simulation (TEST milestone).
    Does NOT replace ResearchExperiment; acts as a locked, canonical contract view.
    """
    research_question: str
    hypothesis: Optional[str] = None
    market_context: DefinedMarketContext
    signal_rules: DefinedSignalRules
    position_rules: DefinedPositionRules
    backtest_bounds: DefinedBacktestBounds
    provenance_audit: List[ParameterProvenanceRecord]

    @classmethod
    def from_experiment(cls, experiment: ResearchExperiment) -> "DefinedExperimentSpec":
        """
        Validates the experiment against the strict DEFINE safety gate:
        - Must have status == READY
        - Zero unresolved missing information
        - Execution-critical parameters must not be empty, missing, or require confirmation
        - No unconfirmed AI-inferred assumptions
        """
        # 1. Status check
        if experiment.status != ExperimentStatus.READY:
            raise ValueError(
                f"Experiment status must be READY to define, but is '{experiment.status.value}'."
            )

        # 2. Unresolved missing information check
        if experiment.missing_information and len(experiment.missing_information) > 0:
            unresolved = [item.field for item in experiment.missing_information]
            raise ValueError(
                f"Cannot define experiment with unresolved missing parameters: {unresolved}"
            )

        # 3. Execution-critical fields check
        critical_fields = [
            ("instrument", experiment.instrument),
            ("timeframe", experiment.timeframe),
            ("entry_condition", experiment.entry_condition),
            ("test_period", experiment.test_period),
            ("cost_assumptions", experiment.cost_assumptions),
        ]

        for name, field in critical_fields:
            if not field.value or (isinstance(field.value, str) and not field.value.strip()):
                raise ValueError(f"Execution-critical field '{name}' has a missing or empty value.")
            if field.requires_confirmation:
                raise ValueError(f"Execution-critical field '{name}' requires explicit user confirmation.")
            if field.source == ParameterSource.MISSING:
                raise ValueError(f"Execution-critical field '{name}' has invalid provenance 'MISSING'.")
            if field.source == ParameterSource.AI_INFERRED and field.requires_confirmation:
                raise ValueError(f"Execution-critical field '{name}' has unconfirmed AI-inferred assumptions.")

        # Position rules check: at least one of exit_condition or holding_period must be present and confirmed
        has_exit = bool(experiment.exit_condition.value and str(experiment.exit_condition.value).strip() and experiment.exit_condition.source != ParameterSource.MISSING)
        has_holding = bool(experiment.holding_period.value and str(experiment.holding_period.value).strip() and experiment.holding_period.source != ParameterSource.MISSING)

        if not has_exit and not has_holding:
            raise ValueError("At least one position exit rule (exit_condition or holding_period) must be defined.")

        if has_exit and experiment.exit_condition.requires_confirmation:
            raise ValueError("Field 'exit_condition' requires explicit user confirmation.")
        if has_holding and experiment.holding_period.requires_confirmation:
            raise ValueError("Field 'holding_period' requires explicit user confirmation.")

        # Filters check: if regime filters are provided, they must not require confirmation
        if experiment.filters.value and experiment.filters.requires_confirmation:
            raise ValueError("Regime filters require explicit user confirmation.")

        # Construct audit records
        provenance_records = [
            ParameterProvenanceRecord(
                field="instrument",
                source=experiment.instrument.source,
                confidence=experiment.instrument.confidence,
                requires_confirmation=experiment.instrument.requires_confirmation,
            ),
            ParameterProvenanceRecord(
                field="timeframe",
                source=experiment.timeframe.source,
                confidence=experiment.timeframe.confidence,
                requires_confirmation=experiment.timeframe.requires_confirmation,
            ),
            ParameterProvenanceRecord(
                field="entry_condition",
                source=experiment.entry_condition.source,
                confidence=experiment.entry_condition.confidence,
                requires_confirmation=experiment.entry_condition.requires_confirmation,
            ),
            ParameterProvenanceRecord(
                field="exit_condition",
                source=experiment.exit_condition.source,
                confidence=experiment.exit_condition.confidence,
                requires_confirmation=experiment.exit_condition.requires_confirmation,
            ),
            ParameterProvenanceRecord(
                field="holding_period",
                source=experiment.holding_period.source,
                confidence=experiment.holding_period.confidence,
                requires_confirmation=experiment.holding_period.requires_confirmation,
            ),
            ParameterProvenanceRecord(
                field="filters",
                source=experiment.filters.source,
                confidence=experiment.filters.confidence,
                requires_confirmation=experiment.filters.requires_confirmation,
            ),
            ParameterProvenanceRecord(
                field="test_period",
                source=experiment.test_period.source,
                confidence=experiment.test_period.confidence,
                requires_confirmation=experiment.test_period.requires_confirmation,
            ),
            ParameterProvenanceRecord(
                field="cost_assumptions",
                source=experiment.cost_assumptions.source,
                confidence=experiment.cost_assumptions.confidence,
                requires_confirmation=experiment.cost_assumptions.requires_confirmation,
            ),
        ]

        return cls(
            research_question=experiment.research_question,
            hypothesis=experiment.hypothesis,
            market_context=DefinedMarketContext(
                instrument=str(experiment.instrument.value).strip(),
                timeframe=str(experiment.timeframe.value).strip(),
            ),
            signal_rules=DefinedSignalRules(
                entry_condition=str(experiment.entry_condition.value).strip(),
                filters=experiment.filters.value or [],
            ),
            position_rules=DefinedPositionRules(
                exit_condition=str(experiment.exit_condition.value).strip() if experiment.exit_condition.value else None,
                holding_period=str(experiment.holding_period.value).strip() if experiment.holding_period.value else None,
            ),
            backtest_bounds=DefinedBacktestBounds(
                test_period=str(experiment.test_period.value).strip(),
                cost_assumptions=str(experiment.cost_assumptions.value).strip(),
            ),
            provenance_audit=provenance_records,
        )


class ResearchDefineRequest(BaseModel):
    """
    Request payload to project a validated READY ResearchExperiment into a DefinedExperimentSpec.
    """
    experiment: ResearchExperiment = Field(..., description="The finalized ResearchExperiment to define")


class SimulatedTrade(BaseModel):
    """
    Simulated trade execution record with explicit entry/exit timing and friction impact.
    """
    trade_id: int
    entry_bar_index: int
    entry_date: str
    entry_price: float
    exit_bar_index: int
    exit_date: str
    exit_price: float
    exit_reason: str  # "HOLDING_PERIOD_EXPIRY" | "PROFIT_TARGET" | "STOP_LOSS"
    gross_pnl_pct: float
    net_pnl_pct: float
    friction_paid_pct: float
    holding_bars: int
    is_win: bool


class EquityPoint(BaseModel):
    """
    Daily portfolio valuation point on the equity curve.
    """
    date: str
    equity: float
    drawdown_pct: float
    in_trade: bool


class BacktestMetrics(BaseModel):
    """
    Summary performance and risk analytics for a backtest run.
    Guaranteed never to return NaN or Infinity.
    """
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    net_return_pct: float
    gross_return_pct: float
    friction_drag_pct: float
    profit_factor: float
    max_drawdown_pct: float
    avg_trade_return_pct: float
    avg_holding_bars: float
    sharpe_ratio: Optional[float] = None


class BacktestResult(BaseModel):
    """
    Complete output of a deterministic backtest simulation.
    Explicitly distinguishes synthetic simulation from live market results.
    """
    experiment_id: str
    instrument: str
    timeframe: str
    test_period: str
    initial_capital: float
    final_equity: float
    metrics: BacktestMetrics
    equity_curve: List[EquityPoint]
    trades: List[SimulatedTrade]
    execution_timing_convention: str
    simulation_disclaimer: str
    reproducible_seed: int


class TestExecutionRequest(BaseModel):
    """
    Request model to execute a deterministic backtest on a DefinedExperimentSpec.
    Accepts ONLY a DefinedExperimentSpec to ensure DEFINE gating cannot be bypassed.
    """
    __test__ = False
    spec: DefinedExperimentSpec = Field(..., description="Locked, validated experiment execution contract")
    initial_capital: float = Field(default=100000.0, ge=1000.0, description="Starting portfolio cash in local currency")



