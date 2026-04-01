"""
Per-tenant UI preferences stored in Redis (JSON).

No authentication yet; company_id must match other tenant-scoped APIs.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis_lib

from backend.core.config import Settings
from backend.models.schemas import WorkspacePreferences, WorkspacePreferencesPatch
from backend.services.collections import company_safe_id

_PREFS_KEY_PREFIX = "workspace:prefs:"


def _redis_key(company_safe_id: str) -> str:
    return f"{_PREFS_KEY_PREFIX}{company_safe_id}"


def _default_preferences() -> WorkspacePreferences:
    return WorkspacePreferences()


async def load_workspace_preferences(settings: Settings, company_id: str) -> WorkspacePreferences:
    """
    Load merged preferences for a tenant, falling back to defaults when missing or invalid.
    """

    safe = company_safe_id(company_id)
    client = redis_lib.from_url(settings.redis_url, decode_responses=True)
    try:
        raw = await client.get(_redis_key(safe))
    finally:
        await client.aclose()

    if not raw:
        return _default_preferences()
    try:
        data: Any = json.loads(raw)
        if not isinstance(data, dict):
            return _default_preferences()
        return WorkspacePreferences.model_validate(data)
    except (json.JSONDecodeError, ValueError):
        return _default_preferences()


async def patch_workspace_preferences(
    settings: Settings,
    company_id: str,
    patch: WorkspacePreferencesPatch,
) -> WorkspacePreferences:
    """
    Merge a partial update into stored preferences and return the full document.
    """

    current = await load_workspace_preferences(settings, company_id)
    merged = current.model_copy(update=patch.model_dump(exclude_unset=True))
    safe = company_safe_id(company_id)
    payload = merged.model_dump(mode="json")
    client = redis_lib.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.set(_redis_key(safe), json.dumps(payload))
    finally:
        await client.aclose()
    return merged
