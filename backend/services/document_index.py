"""
List distinct indexed documents per tenant by scanning Qdrant payloads.

Used for document library UIs; never mixes data across company collections.
"""

from __future__ import annotations

from collections import defaultdict

from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings
from backend.models.schemas import DocumentIndexItem
from backend.services.collections import company_collection_name


async def list_indexed_documents_for_company(
    settings: Settings,
    company_id: str,
    client: AsyncQdrantClient,
) -> tuple[list[DocumentIndexItem], bool]:
    """
    Aggregate chunk counts by document_name for one tenant collection.

    Args:
        settings: Batch sizes and scan cap.
        company_id: Raw tenant id from the API.
        client: Shared async Qdrant client.

    Returns:
        Sorted document rows and whether scanning stopped early due to the cap.

    Raises:
        ValueError: When company_id is invalid for collection naming.
        Exception: Propagates Qdrant client errors for the router to map to HTTP.
    """

    collection = company_collection_name(company_id)
    exists = await client.collection_exists(collection_name=collection)
    if not exists:
        return [], False

    batch = max(1, settings.document_list_scroll_batch_size)
    max_points = max(1, settings.document_index_max_points_scanned)

    counts: dict[str, int] = defaultdict(int)
    scanned = 0
    offset: str | int | None = None
    truncated = False

    while scanned < max_points:
        limit = min(batch, max_points - scanned)
        if limit <= 0:
            break
        records, next_offset = await client.scroll(
            collection_name=collection,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not records:
            break
        for record in records:
            payload = record.payload or {}
            name = payload.get("document_name")
            if isinstance(name, str) and name.strip():
                counts[name.strip()] += 1
        scanned += len(records)
        offset = next_offset
        if offset is None:
            break
        if scanned >= max_points:
            truncated = True
            break

    items = [
        DocumentIndexItem(document_name=name, chunk_count=count)
        for name, count in sorted(counts.items(), key=lambda pair: pair[0].lower())
    ]
    return items, truncated
