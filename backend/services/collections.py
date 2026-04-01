"""
Qdrant collection helpers for multi-tenant company namespacing.

Ensures each company has an isolated vector collection before upserts.
"""

from __future__ import annotations

import re

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from backend.core.config import Settings

COMPANY_COLLECTION_PREFIX = "company_"


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
    Build the Qdrant collection name for a company.

    Args:
        company_id: Tenant identifier from the API.

    Returns:
        str: Collection name in the form company_{safe_suffix}.

    Raises:
        ValueError: If company_id cannot be normalized to a non-empty safe id.
    """

    return f"{COMPANY_COLLECTION_PREFIX}{company_safe_id(company_id)}"


async def list_tenant_workspace_ids(client: AsyncQdrantClient) -> list[str]:
    """
    List company_id suffixes for every Qdrant collection owned by the app prefix.

    Args:
        client: Async Qdrant HTTP client.

    Returns:
        Sorted unique workspace ids (safe suffixes after company_).

    Raises:
        Exception: Propagates Qdrant client errors for the router to map to HTTP.
    """

    response = await client.get_collections()
    seen: set[str] = set()
    for coll in response.collections:
        name = str(coll.name)
        if not name.startswith(COMPANY_COLLECTION_PREFIX):
            continue
        suffix = name[len(COMPANY_COLLECTION_PREFIX) :].strip()
        if suffix:
            seen.add(suffix)
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
