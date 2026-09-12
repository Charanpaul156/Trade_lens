from typing import List
from app.schemas.research import (
    ResearchExperiment,
    FieldClarification,
    ParameterSource,
    SUPPORTED_EXPERIMENT_FIELDS,
)
from app.services.experiment_validator import ExperimentValidator


class ExperimentClarifier:
    """
    Stateless service responsible for applying structured user clarifications
    to an existing ResearchExperiment and re-validating the updated specification.
    Follows the core principle:
    - Sets clarified fields to USER_EXPLICIT
    - Clears requires_confirmation
    - Sets confidence to 1.0
    - Re-validates using ExperimentValidator without fabricating unmentioned parameters
    - Never calls Gemini for user-supplied explicit answers
    """

    @classmethod
    def clarify(
        cls,
        experiment: ResearchExperiment,
        clarifications: List[FieldClarification],
    ) -> ResearchExperiment:
        # Create a deep copy or work on a cloned model to avoid unexpected mutations
        updated_experiment = experiment.model_copy(deep=True)

        for item in clarifications:
            field_name = item.field.strip().lower()
            if field_name not in SUPPORTED_EXPERIMENT_FIELDS:
                raise ValueError(
                    f"Unsupported experiment field '{item.field}'. Supported fields are: {sorted(list(SUPPORTED_EXPERIMENT_FIELDS))}"
                )

            current_field = getattr(updated_experiment, field_name)

            if field_name == "filters":
                # filters is ExtractedField[List[str]]
                if isinstance(item.value, list):
                    val = [str(x).strip() for x in item.value if str(x).strip()]
                else:
                    val = [item.value.strip()] if item.value.strip() else []
                current_field.value = val
                current_field.raw_text = ", ".join(val)
            else:
                # String fields: instrument, timeframe, entry_condition, exit_condition,
                # holding_period, test_period, cost_assumptions
                val_str = ", ".join(item.value) if isinstance(item.value, list) else str(item.value).strip()
                current_field.value = val_str
                current_field.raw_text = val_str

            current_field.source = ParameterSource.USER_EXPLICIT
            current_field.requires_confirmation = False
            current_field.confidence = 1.0
            current_field.notes = None

        # Re-run quantitative validator to compile remaining missing items and update status
        return ExperimentValidator.validate(updated_experiment)
