from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings, get_settings
from backend.core.qdrant_client import get_qdrant_client
from backend.models.schemas import IngestStatusResponse, IngestUploadResponse
from backend.services.collections import company_collection_name
from backend.services.document_index import indexed_document_name_exists

router = APIRouter()


def _job_key(job_id: str) -> str:
    return f"ingest:job:{job_id}"


def _ingest_status_from_redis_value(job_id: str, data: str) -> IngestStatusResponse:
    """
    Map a Redis job value (JSON or legacy string) to an API response model.
    """

    text = data.strip()
    if text.startswith("{"):
        try:
            obj: dict[str, object] = json.loads(text)
            status_val = obj.get("status")
            if status_val == "processing":
                meta = {key: value for key, value in obj.items() if key != "status"}
                return IngestStatusResponse(
                    job_id=job_id,
                    status="processing",
                    meta=meta or None,
                )
            if status_val == "ready":
                raw_chunks = obj.get("chunks_indexed")
                chunks_indexed = int(raw_chunks) if raw_chunks is not None else None
                meta = {
                    key: value
                    for key, value in obj.items()
                    if key not in ("status", "chunks_indexed")
                }
                return IngestStatusResponse(
                    job_id=job_id,
                    status="ready",
                    chunks_indexed=chunks_indexed,
                    meta=meta or None,
                )
            if status_val == "failed":
                detail = str(obj.get("detail") or "Ingestion failed")
                meta = {key: value for key, value in obj.items() if key not in ("status", "detail")}
                return IngestStatusResponse(
                    job_id=job_id,
                    status="failed",
                    detail=detail,
                    meta=meta or None,
                )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    if text == "processing":
        return IngestStatusResponse(job_id=job_id, status="processing")
    if text == "ready":
        return IngestStatusResponse(job_id=job_id, status="ready")
    if text.startswith("failed:"):
        return IngestStatusResponse(
            job_id=job_id,
            status="failed",
            detail=text.removeprefix("failed:").strip(),
        )

    return IngestStatusResponse(job_id=job_id, status="processing", detail=text)


@router.post("/upload", response_model=IngestUploadResponse, status_code=202)
async def ingest_upload(
    company_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
    qdrant: Annotated[AsyncQdrantClient, Depends(get_qdrant_client)],
    file: Annotated[UploadFile, File(...)],
) -> IngestUploadResponse:
    """
    Accept a file upload and enqueue an ARQ ingestion job.
    """

    try:
        if not company_id.strip():
            raise ValueError("company_id is required")
        try:
            company_collection_name(company_id)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

        raw_name = Path(file.filename or "upload").name
        stripped_base = raw_name.strip()
        safe_name = stripped_base if stripped_base else "upload"

        try:
            if await indexed_document_name_exists(company_id, qdrant, safe_name):
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"A document named {safe_name!r} already exists in this workspace. "
                        "Delete it in the Documents panel or rename the file before uploading."
                    ),
                )
        except HTTPException:
            raise
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=503,
                detail="Could not verify whether this document already exists. Try again shortly.",
            ) from exc

        job_id = uuid4().hex
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

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
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to enqueue ingestion job") from exc


@router.get("/status/{job_id}", response_model=IngestStatusResponse)
async def ingest_status(
    job_id: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> IngestStatusResponse:
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
        return _ingest_status_from_redis_value(job_id, data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to read job status") from exc
