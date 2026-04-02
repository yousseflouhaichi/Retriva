"""
Delete indexed chunks for one document name inside a tenant Qdrant collection.
"""

from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import FieldCondition, Filter, FilterSelector, MatchValue

from backend.core.config import Settings
from backend.services.bm25_index import replace_bm25_corpus_from_qdrant
from backend.services.collections import company_collection_name, company_safe_id


async def delete_document_by_name(
    settings: Settings,
    company_id: str,
    document_name: str,
    qdrant: AsyncQdrantClient,
) -> None:
    """
    Remove all points whose payload document_name matches exactly (stripped).

    Rebuilds the tenant BM25 Redis list from remaining Qdrant points.

    Args:
        settings: Redis and scroll batch settings.
        company_id: Tenant id from the API.
        document_name: Indexed filename to remove (exact match after strip).
        qdrant: Async Qdrant client.

    Raises:
        ValueError: When ids or document_name are invalid.
    """

    stripped_doc = document_name.strip()
    if not stripped_doc:
        raise ValueError("document_name is required")
    collection = company_collection_name(company_id)
    exists = await qdrant.collection_exists(collection_name=collection)
    if not exists:
        raise ValueError("workspace collection not found")
    safe = company_safe_id(company_id)
    point_filter = Filter(
        must=[
            FieldCondition(
                key="document_name",
                match=MatchValue(value=stripped_doc),
            ),
        ],
    )
    await qdrant.delete(
        collection_name=collection,
        points_selector=FilterSelector(filter=point_filter),
        wait=True,
    )
    await replace_bm25_corpus_from_qdrant(settings, safe, qdrant, collection)
