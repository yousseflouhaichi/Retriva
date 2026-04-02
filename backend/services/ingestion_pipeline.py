"""
End-to-end ingestion: Unstructured parse, chunk, embed, Qdrant upsert.

Runs inside the ARQ worker, not the FastAPI process.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import redis.asyncio as redis
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from backend.core.config import Settings
from backend.services.bm25_index import append_bm25_documents
from backend.services.chunker import chunks_from_elements
from backend.services.collections import company_safe_id, ensure_company_collection
from backend.services.document_index import indexed_document_name_exists
from backend.services.embedder import embed_texts
from backend.services.parser import parse_document_to_elements


async def run_document_ingestion(
    settings: Settings,
    company_id: str,
    job_id: str,
    file_path: Path,
    original_filename: str,
    redis_client: redis.Redis | None = None,
) -> tuple[int, str]:
    """
    Parse a file, embed chunks, and persist vectors to the tenant collection.

    Args:
        settings: Shared application configuration.
        company_id: Tenant id from the upload request.
        job_id: Ingestion job id for traceability in payloads.
        file_path: Absolute or project-relative path to the stored upload.
        original_filename: Display name of the uploaded document.

    Returns:
        tuple[int, str]: Number of points upserted and the Qdrant collection name.

    Raises:
        ValueError: For missing prerequisites such as API keys.
        RuntimeError: For unexpected API or persistence behavior.
    """

    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        doc_label = original_filename.strip()
        collection = await ensure_company_collection(client, settings, company_id)
        if await indexed_document_name_exists(company_id, client, doc_label):
            raise ValueError(
                f"A document named {doc_label!r} already exists in this workspace. "
                "Delete it or rename the file before uploading again."
            )
        elements = await parse_document_to_elements(settings, file_path)
        chunks = chunks_from_elements(settings, elements)
        if not chunks:
            return 0, collection

        vectors = await embed_texts(settings, [chunk.text for chunk in chunks])
        if len(vectors) != len(chunks):
            raise RuntimeError("Embedding count does not match chunk count")

        indexed_at = datetime.now(timezone.utc).isoformat()
        batch_size = max(1, settings.qdrant_upsert_batch_size)
        points: list[PointStruct] = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            payload: dict[str, Any] = {
                "workspace_id": company_id.strip(),
                "document_name": doc_label,
                "page_number": chunk.page_number,
                "chunk_type": chunk.chunk_type,
                "parent_chunk_id": chunk.parent_chunk_id or "",
                "job_id": job_id,
                "indexed_at": indexed_at,
                "text": chunk.text,
            }
            points.append(PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload))

        for start in range(0, len(points), batch_size):
            batch_points = points[start : start + batch_size]
            await client.upsert(collection_name=collection, points=batch_points, wait=True)

        if redis_client is not None and points:
            safe = company_safe_id(company_id)
            pairs = [
                (str(point.id), str(point.payload.get("text", "")))
                for point in points
                if point.payload.get("text")
            ]
            await append_bm25_documents(redis_client, safe, pairs)

        return len(points), collection
    finally:
        await client.close()
