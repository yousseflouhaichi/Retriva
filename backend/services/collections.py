"""
Qdrant collection helpers for multi-tenant workspace isolation.

Collection names match the normalized workspace id. Legacy collections named
company_{id} are still listed for backward compatibility.
"""

from __future__ import annotations

import re

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
