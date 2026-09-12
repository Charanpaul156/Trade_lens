from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Current service health status")
    service: str = Field(default="trade-lens-ai", description="Service identifier")
