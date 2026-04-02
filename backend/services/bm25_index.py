"""
Per-tenant BM25 corpus in Redis for hybrid retrieval.

Each chunk id matches the Qdrant point id so RRF can fuse lexical and dense ranks.
"""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings


def _bm25_redis_key(company_safe_id: str) -> str:
    return f"bm25:corpus:{company_safe_id}"


async def append_bm25_documents(
    redis_client: redis.Redis,
    company_safe_id: str,
    documents: list[tuple[str, str]],
) -> None:
    """
    Append chunk id and text pairs to the tenant BM25 list in Redis.

    Args:
        redis_client: Async Redis client (decode_responses=True recommended).
        company_safe_id: Normalized tenant id from company_safe_id().
        documents: (point_id, chunk_text) for each upserted vector.
    """

    if not documents:
        return
    key = _bm25_redis_key(company_safe_id)
    payload_strings = [json.dumps({"id": point_id, "text": text}) for point_id, text in documents]
    await redis_client.rpush(key, *payload_strings)


async def load_bm25_corpus(
    settings: Settings,
    company_safe_id: str,
) -> tuple[list[str], list[str]]:
    """
    Load up to bm25_max_corpus_documents texts and ids for BM25 scoring.

    Args:
        settings: Redis URL and corpus size cap.
        company_safe_id: Normalized tenant id.

    Returns:
        tuple[list[str], list[str]]: Parallel lists of point ids and chunk texts.
    """

    client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        key = _bm25_redis_key(company_safe_id)
        end = max(0, settings.bm25_max_corpus_documents - 1)
        raw_rows = await client.lrange(key, 0, end)
    finally:
        await client.aclose()

    ids: list[str] = []
    texts: list[str] = []
    for row in raw_rows:
        try:
            obj: dict[str, Any] = json.loads(row)
            point_id = str(obj.get("id", ""))
            text = str(obj.get("text", ""))
            if point_id and text:
                ids.append(point_id)
                texts.append(text)
        except (json.JSONDecodeError, TypeError):
            continue
    return ids, texts


async def replace_bm25_corpus_from_qdrant(
    settings: Settings,
    company_safe_id: str,
    qdrant: AsyncQdrantClient,
    collection_name: str,
) -> None:
    """
    Rebuild the Redis BM25 list from Qdrant payloads, capped at bm25_max_corpus_documents.

    Used after point deletes so lexical retrieval matches dense vectors.
    """

    cap = max(1, settings.bm25_max_corpus_documents)
    batch = max(1, settings.document_list_scroll_batch_size)
    pairs: list[tuple[str, str]] = []
    scroll_offset: str | int | None = None
    while len(pairs) < cap:
        page_limit = min(batch, cap - len(pairs))
        if page_limit <= 0:
            break
        records, next_offset = await qdrant.scroll(
            collection_name=collection_name,
            limit=page_limit,
            offset=scroll_offset,
            with_payload=True,
            with_vectors=False,
        )
        if not records:
            break
        for record in records:
            if len(pairs) >= cap:
                break
            payload = record.payload or {}
            pid = str(record.id)
            text = str(payload.get("text", ""))
            if pid and text.strip():
                pairs.append((pid, text))
        scroll_offset = next_offset
        if scroll_offset is None:
            break

    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    try:
        key = _bm25_redis_key(company_safe_id)
        await redis_client.delete(key)
        if pairs:
            redis_batch = max(1, min(512, len(pairs)))
            for start in range(0, len(pairs), redis_batch):
                await append_bm25_documents(redis_client, company_safe_id, pairs[start : start + redis_batch])
    finally:
        await redis_client.aclose()
