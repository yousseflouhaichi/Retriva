"""
Qdrant collection helpers for multi-tenant workspace isolation.

Collection names match the normalized workspace id. Legacy collections named
company_{id} are still listed for backward compatibility.
"""

from __future__ import annotations

import re

import redis.asyncio as redis_lib
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from backend.core.config import Settings

LEGACY_COMPANY_COLLECTION_PREFIX = "company_"
_WORKSPACE_COLLECTION_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def company_safe_id(company_id: str) -> str:
    """
    Normalize company_id for storage keys and collection suffixes.

    Args:
        company_id: Raw tenant identifier from the API.

    Returns:
        str: Alphanumeric, hyphen, and underscore only.

    Raises:
        ValueError: If company_id cannot be normalized to a non-empty safe id.
    """

    stripped = company_id.strip()
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", stripped).strip("_")
    if not safe:
        raise ValueError("company_id must contain at least one letter, digit, hyphen, or underscore")
    return safe


def company_collection_name(company_id: str) -> str:
    """
    Build the Qdrant collection name for a workspace.

    Args:
        company_id: Tenant identifier from the API.

    Returns:
        str: Collection name equal to the normalized workspace id (no prefix).

    Raises:
        ValueError: If company_id cannot be normalized to a non-empty safe id.
    """

    return company_safe_id(company_id)


def _workspace_id_from_collection_name(collection_name: str) -> str | None:
    """
    Map a Qdrant collection name to a workspace id for GET /workspaces.

    Accepts current naming (plain safe id) and legacy company_{safe_id}.
    """

    raw = str(collection_name).strip()
    if not raw:
        return None
    if raw.startswith(LEGACY_COMPANY_COLLECTION_PREFIX):
        suffix = raw[len(LEGACY_COMPANY_COLLECTION_PREFIX) :]
        if suffix and _WORKSPACE_COLLECTION_RE.fullmatch(suffix):
            return suffix
        return None
    if _WORKSPACE_COLLECTION_RE.fullmatch(raw):
        return raw
    return None


async def list_tenant_workspace_ids(client: AsyncQdrantClient) -> list[str]:
    """
    List workspace ids for every Qdrant collection that matches app naming rules.

    Args:
        client: Async Qdrant HTTP client.

    Returns:
        Sorted unique workspace ids (plain safe names or legacy company_ suffixes).

    Raises:
        Exception: Propagates Qdrant client errors for the router to map to HTTP.
    """

    response = await client.get_collections()
    seen: set[str] = set()
    for coll in response.collections:
        wid = _workspace_id_from_collection_name(str(coll.name))
        if wid:
            seen.add(wid)
    return sorted(seen)


async def ensure_company_collection(
    client: AsyncQdrantClient,
    settings: Settings,
    company_id: str,
) -> str:
    """
    Create the company collection when missing, using embedding dimension from settings.

    Args:
        client: Async Qdrant client for the deployment.
        settings: Application settings (vector size and distance).
        company_id: Tenant identifier from the API.

    Returns:
        str: The collection name that exists and is ready for upserts.
    """

    name = company_collection_name(company_id)
    exists = await client.collection_exists(collection_name=name)
    if exists:
        return name
    await client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=settings.embeddings_dim, distance=Distance.COSINE),
    )
    return name


async def ensure_workspace_collection(
    client: AsyncQdrantClient,
    settings: Settings,
    raw_workspace_id: str,
) -> tuple[str, bool]:
    """
    Ensure a Qdrant collection exists for the workspace; create it when missing.

    Args:
        client: Qdrant async client.
        settings: App settings for embedding vector size.
        raw_workspace_id: Workspace id from the client (trimmed and validated).

    Returns:
        Normalized collection name and whether this call created the collection.

    Raises:
        ValueError: If workspace id is empty or invalid for collection naming.
    """

    stripped = raw_workspace_id.strip()
    if not stripped:
        raise ValueError("workspace_id is required")
    name = company_collection_name(stripped)
    existed_before = await client.collection_exists(collection_name=name)
    await ensure_company_collection(client, settings, stripped)
    return name, not existed_before


_WORKSPACE_PREFS_KEY_PREFIX = "workspace:prefs:"


async def delete_workspace_and_sidecars(
    settings: Settings,
    raw_workspace_id: str,
    client: AsyncQdrantClient,
) -> None:
    """
    Drop the Qdrant collection for a workspace and remove Redis BM25 and preferences keys.

    Args:
        settings: Redis URL from configuration.
        raw_workspace_id: Workspace id from the API path or body.
        client: Async Qdrant client.

    Raises:
        ValueError: If workspace id is invalid for collection naming.
    """

    name = company_collection_name(raw_workspace_id)
    safe = company_safe_id(raw_workspace_id)
    if await client.collection_exists(collection_name=name):
        await client.delete_collection(collection_name=name)
    redis_client = redis_lib.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis_client.delete(f"bm25:corpus:{safe}")
        await redis_client.delete(f"{_WORKSPACE_PREFS_KEY_PREFIX}{safe}")
    finally:
        await redis_client.aclose()
