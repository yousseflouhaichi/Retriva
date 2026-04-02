from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings, get_settings
from backend.core.qdrant_client import get_qdrant_client
from backend.models.schemas import HealthResponse, WorkspacesListResponse
from backend.services.collections import list_tenant_workspace_ids

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Lightweight health check for the API process.
    """

    return HealthResponse(environment=settings.environment)


@router.get("/workspaces", response_model=WorkspacesListResponse)
async def list_workspaces(
    qdrant: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> WorkspacesListResponse:
    """
    Return workspace ids backed by existing Qdrant collections (plain id or legacy company_*).
    """

    try:
        workspaces = await list_tenant_workspace_ids(qdrant)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not list workspaces from the vector store",
        ) from None
    return WorkspacesListResponse(workspaces=workspaces)
