from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
async def health_check() -> HealthResponse:
    """
    Returns the health status and identifier of the TradeLens AI backend service.
    """
    return HealthResponse(status="ok", service="trade-lens-ai")
