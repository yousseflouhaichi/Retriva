from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings, get_settings
from backend.core.qdrant_client import get_qdrant_client
from backend.models.schemas import (
    HealthResponse,
    WorkspaceEnsureRequest,
    WorkspaceEnsureResponse,
    WorkspacesListResponse,
)
from backend.services.collections import ensure_workspace_collection, list_tenant_workspace_ids

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


@router.post("/workspaces", response_model=WorkspaceEnsureResponse)
async def ensure_workspace(
    ensure_request: WorkspaceEnsureRequest,
    qdrant: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
) -> WorkspaceEnsureResponse:
    """
    Create an empty Qdrant collection for a workspace so it exists before any document ingest.
    """

    settings = get_settings()
    try:
        name, created = await ensure_workspace_collection(qdrant, settings, ensure_request.workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not create workspace collection in the vector store",
        ) from None
    return WorkspaceEnsureResponse(workspace_id=name, created=created)
