"""
List distinct indexed documents per tenant by scanning Qdrant payloads.

Used for document library UIs; never mixes data across company collections.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings
from backend.models.schemas import DocumentIndexItem
from backend.services.collections import company_collection_name


def _parse_indexed_at(raw: object) -> datetime | None:
    """
    Parse ISO-8601 indexed_at from chunk payload; return None when missing or invalid.
    """

    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


async def list_indexed_documents_for_company(
    settings: Settings,
    company_id: str,
    client: AsyncQdrantClient,
    *,
    limit: int,
    offset: int,
) -> tuple[list[DocumentIndexItem], bool, int, int, int]:
    """
    Aggregate chunk counts and latest indexed_at by document_name for one tenant.

    Args:
        settings: Batch sizes, scan cap, and pagination bounds.
        company_id: Raw tenant id from the API.
        client: Shared async Qdrant client.
        limit: Page size after aggregation (clamped to config).
        offset: Documents to skip in the sorted name list (non-negative).

    Returns:
        Page of rows, truncated scan flag, total distinct documents, effective limit, effective offset.

    Raises:
        ValueError: When company_id is invalid for collection naming.
        Exception: Propagates Qdrant client errors for the router to map to HTTP.
    """

    collection = company_collection_name(company_id)
    exists = await client.collection_exists(collection_name=collection)
    if not exists:
        return [], False, 0, limit, offset

    batch = max(1, settings.document_list_scroll_batch_size)
    max_points = max(1, settings.document_index_max_points_scanned)

    counts: dict[str, int] = defaultdict(int)
    latest: dict[str, datetime | None] = defaultdict(lambda: None)
    scanned = 0
    scroll_offset: str | int | None = None
    truncated = False

    while scanned < max_points:
        page_limit = min(batch, max_points - scanned)
        if page_limit <= 0:
            break
        records, next_offset = await client.scroll(
            collection_name=collection,
            limit=page_limit,
            offset=scroll_offset,
            with_payload=True,
            with_vectors=False,
        )
        if not records:
            break
        for record in records:
            payload = record.payload or {}
            name = payload.get("document_name")
            if not isinstance(name, str) or not name.strip():
                continue
            key = name.strip()
            counts[key] += 1
            ts = _parse_indexed_at(payload.get("indexed_at"))
            if ts is not None:
                prev = latest[key]
                if prev is None or ts > prev:
                    latest[key] = ts
        scanned += len(records)
        scroll_offset = next_offset
        if scroll_offset is None:
            break
        if scanned >= max_points:
            truncated = True
            break

    sorted_names = sorted(counts.keys(), key=lambda value: value.lower())
    total = len(sorted_names)
    eff_offset = max(0, offset)
    page_names = sorted_names[eff_offset : eff_offset + limit]

    items = [
        DocumentIndexItem(
            document_name=name,
            chunk_count=counts[name],
            last_indexed_at=latest[name],
        )
        for name in page_names
    ]
    return items, truncated, total, limit, eff_offset
