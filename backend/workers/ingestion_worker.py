"""
ARQ ingestion worker.

Runs as a separate process from FastAPI and updates job status in Redis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from arq.connections import RedisSettings

from backend.core.config import get_settings
from backend.services.ingestion_pipeline import run_document_ingestion


def _job_key(job_id: str) -> str:
    return f"ingest:job:{job_id}"


async def ingest_document(
    ctx: dict[str, Any],
    job_id: str,
    company_id: str,
    file_path: str,
    original_filename: str,
) -> None:
    """
    Ingestion task: parse with Unstructured, embed, upsert to Qdrant, update Redis status.
    """

    redis = ctx["redis"]
    settings = get_settings()
    await redis.set(_job_key(job_id), json.dumps({"status": "processing"}), ex=60 * 60)
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Uploaded file not found: {file_path}")
        if not company_id.strip():
            raise ValueError("company_id is required")
        if not original_filename.strip():
            raise ValueError("original_filename is required")

        count, collection = await run_document_ingestion(
            settings=settings,
            company_id=company_id,
            job_id=job_id,
            file_path=path,
            original_filename=original_filename,
        )
        await redis.set(
            _job_key(job_id),
            json.dumps(
                {
                    "status": "ready",
                    "chunks_indexed": count,
                    "collection": collection,
                }
            ),
            ex=60 * 60,
        )
    except Exception as exc:
        await redis.set(
            _job_key(job_id),
            json.dumps({"status": "failed", "detail": str(exc)}),
            ex=60 * 60,
        )
        raise


class WorkerSettings:
    functions = [ingest_document]

    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
