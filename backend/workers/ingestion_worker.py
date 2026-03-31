"""
ARQ ingestion worker.

Runs as a separate process from FastAPI and updates job status in Redis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from arq.connections import RedisSettings

from backend.core.config import get_settings


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
    Minimal ingestion task:
    - Marks job as processing
    - Validates file exists
    - Marks job as ready
    """

    redis = ctx["redis"]
    await redis.set(_job_key(job_id), "processing", ex=60 * 60)
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Uploaded file not found: {file_path}")
        if not company_id.strip():
            raise ValueError("company_id is required")
        if not original_filename.strip():
            raise ValueError("original_filename is required")
        await redis.set(_job_key(job_id), "ready", ex=60 * 60)
    except Exception as exc:
        await redis.set(_job_key(job_id), f"failed: {exc}", ex=60 * 60)
        raise


class WorkerSettings:
    functions = [ingest_document]

    settings = get_settings()
    redis_settings = RedisSettings.from_dsn(settings.redis_url)

