from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.core.config import Settings, get_settings
from backend.models.schemas import SystemStatusResponse
from backend.services.system_status import build_system_status

router = APIRouter()


@router.get("/status", response_model=SystemStatusResponse)
async def system_status(settings: Annotated[Settings, Depends(get_settings)]) -> SystemStatusResponse:
    """
    Dependency health and safe app metadata for system status and settings UIs.
    """

    return await build_system_status(settings)
