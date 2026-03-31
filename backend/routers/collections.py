from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.config import Settings, get_settings
from backend.models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Lightweight health check for the API process.
    """

    return HealthResponse(environment=settings.environment)
