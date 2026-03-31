from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from backend.core.config import Settings, get_settings
from backend.models.schemas import IngestStatusResponse, IngestUploadResponse

router = APIRouter()


def _job_key(job_id: str) -> str:
    return f"ingest:job:{job_id}"


@router.post("/upload", response_model=IngestUploadResponse, status_code=202)
async def ingest_upload(
    company_id: str,
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> IngestUploadResponse:
    """
    Accept a file upload and enqueue an ARQ ingestion job.
    """

    try:
        if not company_id.strip():
            raise ValueError("company_id is required")

        job_id = uuid4().hex
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(file.filename or "upload").name
        dest = upload_dir / f"{job_id}__{safe_name}"

        content = await file.read()
        dest.write_bytes(content)

        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            await redis.enqueue_job(
                "ingest_document",
                job_id=job_id,
                company_id=company_id,
                file_path=str(dest),
                original_filename=safe_name,
            )
        finally:
            await redis.aclose()

        return IngestUploadResponse(job_id=job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to enqueue ingestion job") from exc


@router.get("/status/{job_id}", response_model=IngestStatusResponse)
async def ingest_status(job_id: str, settings: Settings = Depends(get_settings)) -> IngestStatusResponse:
    """
    Get ingestion job status written by the ARQ worker.
    """

    try:
        redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
        try:
            raw = await redis.get(_job_key(job_id))
        finally:
            await redis.aclose()

        if raw is None:
            return IngestStatusResponse(job_id=job_id, status="queued", detail="Job not yet started")

        data = raw.decode() if isinstance(raw, bytes) else str(raw)

        # Stored as a simple string for the minimal scaffold.
        if data == "processing":
            return IngestStatusResponse(job_id=job_id, status="processing")
        if data == "ready":
            return IngestStatusResponse(job_id=job_id, status="ready")
        if data.startswith("failed:"):
            return IngestStatusResponse(job_id=job_id, status="failed", detail=data.removeprefix("failed:").strip())

        return IngestStatusResponse(job_id=job_id, status="processing", detail=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to read job status") from exc
