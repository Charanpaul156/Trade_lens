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

