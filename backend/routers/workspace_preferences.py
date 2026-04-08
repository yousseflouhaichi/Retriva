from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from backend.core.config import Settings, get_settings
from backend.models.schemas import WorkspacePreferences, WorkspacePreferencesPatch
from backend.services.collections import company_collection_name
from backend.services.workspace_settings import load_workspace_preferences, patch_workspace_preferences

router = APIRouter()


@router.get("/workspace/preferences", response_model=WorkspacePreferences)
async def get_workspace_preferences(
    company_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkspacePreferences:
    """
    Return persisted UI preferences for a workspace, merged with defaults when unset.
    """

    stripped = company_id.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="company_id is required") from None
    try:
        company_collection_name(stripped)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return await load_workspace_preferences(settings, stripped)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not load workspace preferences",
        ) from None


@router.patch("/workspace/preferences", response_model=WorkspacePreferences)
async def update_workspace_preferences(
    body: WorkspacePreferencesPatch,
    company_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkspacePreferences:
    """
    Patch UI preferences for a workspace (theme, density, streaming indicator).
    """

    stripped = company_id.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="company_id is required") from None
    try:
        company_collection_name(stripped)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return await patch_workspace_preferences(settings, stripped, body)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not save workspace preferences",
        ) from None
