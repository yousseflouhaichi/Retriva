"""
ARQ ingestion worker.

Runs as a separate process from FastAPI and updates job status in Redis.
"""

from __future__ import annotations

import asyncio
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
            redis_client=redis,
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
    except asyncio.CancelledError:
        await redis.set(
            _job_key(job_id),
            json.dumps(
                {
                    "status": "failed",
                    "detail": (
                        "Ingestion was cancelled or hit the worker time limit (ARQ job_timeout). "
                        "Increase INGESTION_JOB_TIMEOUT_SECONDS or UNSTRUCTURED_TIMEOUT_SECONDS plus buffer if parsing is slow."
                    ),
                }
            ),
            ex=60 * 60,
        )
        raise
    except Exception as exc:
        await redis.set(
            _job_key(job_id),
            json.dumps({"status": "failed", "detail": str(exc)}),
            ex=60 * 60,
        )
        raise


class WorkerSettings:
    functions = [ingest_document]

    _settings = get_settings()
    redis_settings = RedisSettings.from_dsn(_settings.redis_url)
    job_timeout = _settings.effective_ingestion_job_timeout_seconds()
