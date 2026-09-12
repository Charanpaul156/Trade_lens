from typing import List
from app.schemas.research import (
    ResearchExperiment,
    ExperimentStatus,
    MissingInfoItem,
    MissingSeverity,
    ParameterSource,
)


class ExperimentValidator:
    """
    Validates whether a ResearchExperiment contains the quantitative minimum
    information required for rigorous backtesting and execution.
    Enforces the principle that TradeLens AI does NOT blindly invent parameters.
    """

    @classmethod
    def validate(cls, experiment: ResearchExperiment) -> ResearchExperiment:
        missing_items: List[MissingInfoItem] = []

        # 1. Instrument Validation
        if not experiment.instrument.value or experiment.instrument.source == ParameterSource.MISSING:
            missing_items.append(
                MissingInfoItem(
                    field="instrument",
                    description="No target trading instrument or asset was specified.",
                    severity=MissingSeverity.CRITICAL,
                    clarification_prompt="Which index, stock, or instrument would you like to test (e.g. NIFTY, BANKNIFTY, SPY)?",
                    suggested_defaults=["NIFTY 50", "BANKNIFTY", "SPY"],
                )
            )
        elif experiment.instrument.requires_confirmation:
            missing_items.append(
                MissingInfoItem(
                    field="instrument",
                    description=f"Instrument '{experiment.instrument.value}' was inferred from context and requires user confirmation.",
                    severity=MissingSeverity.WARNING,
                    clarification_prompt=f"Please confirm whether you want to test on '{experiment.instrument.value}'.",
                    suggested_defaults=[experiment.instrument.value],
                )
            )

        # 2. Entry Condition Validation
        if not experiment.entry_condition.value or experiment.entry_condition.source == ParameterSource.MISSING:
            missing_items.append(
                MissingInfoItem(
                    field="entry_condition",
                    description="No entry trigger or rule was specified.",
                    severity=MissingSeverity.CRITICAL,
                    clarification_prompt="What specific event or price movement triggers entry (e.g., a 1% decline from previous close)?",
                    suggested_defaults=["Close drops >= 1.0% from previous day", "RSI(14) drops below 30"],
                )
            )
        elif experiment.entry_condition.requires_confirmation:
            missing_items.append(
                MissingInfoItem(
                    field="entry_condition",
                    description=experiment.entry_condition.notes or "The entry condition contains subjective terminology that needs quantification.",
                    severity=MissingSeverity.CRITICAL,
                    clarification_prompt="How would you quantify the entry threshold (e.g., 1%, 2%, or 2 standard deviations)?",
                    suggested_defaults=["1.0% drawdown", "2.0% drawdown", "2 standard deviations drop"],
                )
            )

        # 3. Exit Condition & Holding Period Validation
        has_exit = (
            experiment.exit_condition.value is not None
            and experiment.exit_condition.source != ParameterSource.MISSING
        )
        has_holding_period = (
            experiment.holding_period.value is not None
            and experiment.holding_period.source != ParameterSource.MISSING
        )

        if not has_exit and not has_holding_period:
            missing_items.append(
                MissingInfoItem(
                    field="exit_condition",
                    description="No exit rule (e.g., profit target or stop-loss) was specified.",
                    severity=MissingSeverity.CRITICAL,
                    clarification_prompt="What is your planned exit rule (e.g., fixed target/stop or dynamic indicator exit)?",
                    suggested_defaults=["Exit on 2% profit target or 1% stop loss", "Exit at next bar open"],
                )
            )
            missing_items.append(
                MissingInfoItem(
                    field="holding_period",
                    description="No fixed trade holding period or time exit was specified.",
                    severity=MissingSeverity.CRITICAL,
                    clarification_prompt="How many days or sessions should each trade be held (e.g., hold for 1 day, 5 days, or 10 days)?",
                    suggested_defaults=["Hold for 1 trading session", "Hold for 5 trading sessions", "Hold for 10 trading sessions"],
                )
            )

        # 4. Timeframe Validation
        if not experiment.timeframe.value or experiment.timeframe.source == ParameterSource.MISSING:
            missing_items.append(
                MissingInfoItem(
                    field="timeframe",
                    description="No bar timeframe was specified.",
                    severity=MissingSeverity.CRITICAL,
                    clarification_prompt="What candle timeframe should be used for the calculation (e.g., 1D / Daily, 1H / Hourly, 15m)?",
                    suggested_defaults=["1D (Daily)", "1H (Hourly)", "15m"],
                )
            )
        elif experiment.timeframe.requires_confirmation:
            missing_items.append(
                MissingInfoItem(
                    field="timeframe",
                    description=f"Timeframe '{experiment.timeframe.value}' was inferred from context and requires user confirmation.",
                    severity=MissingSeverity.INFO,
                    clarification_prompt=f"Is the inferred timeframe of '{experiment.timeframe.value}' correct for your research?",
                    suggested_defaults=["1D (Daily)", "1H (Hourly)"],
                )
            )

        # 5. Test Period Validation
        if not experiment.test_period.value or experiment.test_period.source == ParameterSource.MISSING:
            missing_items.append(
                MissingInfoItem(
                    field="test_period",
                    description="Historical backtest date range is not defined.",
                    severity=MissingSeverity.WARNING,
                    clarification_prompt="What historical date range should be tested (e.g., 2018-01-01 to 2024-12-31)?",
                    suggested_defaults=["Last 5 years (2020 - present)", "Last 10 years (2015 - present)"],
                )
            )

        # 6. Cost Assumptions Validation
        if not experiment.cost_assumptions.value or experiment.cost_assumptions.source == ParameterSource.MISSING:
            missing_items.append(
                MissingInfoItem(
                    field="cost_assumptions",
                    description="Transaction costs, brokerage fees, and slippage assumptions are not specified.",
                    severity=MissingSeverity.WARNING,
                    clarification_prompt="What slippage and transaction cost model should be applied (e.g. 0.05% slippage per side)?",
                    suggested_defaults=["Zero fees (idealized)", "Standard equity/index friction: 0.05% per side"],
                )
            )

        # 7. Filters Validation
        if experiment.filters.value and experiment.filters.requires_confirmation:
            missing_items.append(
                MissingInfoItem(
                    field="filters",
                    description=experiment.filters.notes or "Qualitative regime filter requires an explicit quantitative definition.",
                    severity=MissingSeverity.WARNING,
                    clarification_prompt="How would you define and quantify the volatility filter (e.g., India VIX > 20, or VIX above historical 75th percentile)?",
                    suggested_defaults=["India VIX > 20", "VIX above 75th percentile", "Historical volatility > 1.5 std dev"],
                )
            )

        # Assign updated missing information
        experiment.missing_information = missing_items

        # Determine overall experiment status
        has_critical = any(item.severity == MissingSeverity.CRITICAL for item in missing_items)
        has_warning = any(item.severity == MissingSeverity.WARNING for item in missing_items)

        # If both instrument and entry are missing entirely, it's an initial DRAFT
        if (
            (not experiment.instrument.value or experiment.instrument.source == ParameterSource.MISSING)
            and (not experiment.entry_condition.value or experiment.entry_condition.source == ParameterSource.MISSING)
        ):
            experiment.status = ExperimentStatus.DRAFT
        elif has_critical or has_warning:
            experiment.status = ExperimentStatus.NEEDS_CLARIFICATION
        else:
            experiment.status = ExperimentStatus.READY

        return experiment
