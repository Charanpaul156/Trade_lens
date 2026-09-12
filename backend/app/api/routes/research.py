from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.research import (
    ResearchAnalyzeRequest,
    ResearchAnalyzeResponse,
    ResearchClarifyRequest,
)
from app.services.experiment_clarifier import ExperimentClarifier
from app.services.research_analyzer import (
    BaseResearchAnalyzer,
    get_research_analyzer,
)

router = APIRouter(prefix="/research", tags=["Research Analysis"])


@router.post(
    "/analyze",
    response_model=ResearchAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Trading Research Question",
    description="Transforms a natural language trading research idea into a validated quantitative ResearchExperiment with parameter provenance tracking.",
)
async def analyze_research_question(
    request: ResearchAnalyzeRequest,
    analyzer: BaseResearchAnalyzer = Depends(get_research_analyzer),
) -> ResearchAnalyzeResponse:
    """
    Receives a natural language research question and returns a structured, validated experiment.
    Enforces that missing or ambiguous information is highlighted and not silently invented.
    """
    cleaned_question = request.question.strip()
    if not cleaned_question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The research question cannot be empty or whitespace.",
        )

    # Delegate interpretation to the analyzer service
    experiment = await analyzer.analyze(cleaned_question)

    return ResearchAnalyzeResponse(
        status=experiment.status,
        experiment=experiment,
        missing_information=experiment.missing_information,
    )


@router.post(
    "/clarify",
    response_model=ResearchAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    summary="Clarify Experiment Parameters",
    description="Applies structured user clarifications to an existing ResearchExperiment, updates parameter provenance to USER_EXPLICIT, and re-validates backtest readiness.",
)
async def clarify_experiment(
    request: ResearchClarifyRequest,
) -> ResearchAnalyzeResponse:
    """
    Applies user-provided clarifications to specific experiment parameters.
    Re-runs ExperimentValidator to update missing information and readiness status.
    No LLM call is made; user clarifications are strictly USER_EXPLICIT.
    """
    try:
        updated_experiment = ExperimentClarifier.clarify(
            experiment=request.experiment,
            clarifications=request.clarifications,
        )
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(err),
        )

    return ResearchAnalyzeResponse(
        status=updated_experiment.status,
        experiment=updated_experiment,
        missing_information=updated_experiment.missing_information,
    )

