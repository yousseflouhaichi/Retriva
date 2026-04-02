from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@patch("backend.routers.ingest.create_pool", new_callable=AsyncMock)
async def test_ingest_upload_returns_job_id(mock_create_pool: AsyncMock, async_client: AsyncClient) -> None:
    """
    Upload accepts a file, enqueues ARQ job, returns 202 with job_id when Redis pool works.
    """

    mock_redis = AsyncMock()
    mock_redis.enqueue_job = AsyncMock()
    mock_redis.aclose = AsyncMock()
    mock_create_pool.return_value = mock_redis

    files = {"file": ("note.txt", b"hello world", "text/plain")}
    response = await async_client.post("/ingest/upload?company_id=demo", files=files)

    assert response.status_code == 202
    body = response.json()
    assert "job_id" in body
    assert len(body["job_id"]) == 32
    mock_redis.enqueue_job.assert_awaited_once()
    mock_redis.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_upload_rejects_invalid_company_id(async_client: AsyncClient) -> None:
    """
    Invalid company_id fails validation before touching Redis.
    """

    files = {"file": ("note.txt", b"x", "text/plain")}
    response = await async_client.post("/ingest/upload?company_id=###", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
@patch("backend.routers.ingest.create_pool", new_callable=AsyncMock)
async def test_ingest_status_ready_json(mock_create_pool: AsyncMock, async_client: AsyncClient) -> None:
    """
    Status endpoint parses JSON job payloads from Redis.
    """

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(
        return_value=json.dumps({"status": "ready", "chunks_indexed": 5, "collection": "demo"}),
    )
    mock_redis.aclose = AsyncMock()
    mock_create_pool.return_value = mock_redis

    response = await async_client.get("/ingest/status/abc123")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "abc123"
    assert data["status"] == "ready"
    assert data["chunks_indexed"] == 5
    assert data["meta"] is not None
    assert data["meta"].get("collection") == "demo"


@pytest.mark.asyncio
@patch("backend.routers.ingest.create_pool", new_callable=AsyncMock)
async def test_ingest_status_queued_when_missing_key(mock_create_pool: AsyncMock, async_client: AsyncClient) -> None:
    """
    Missing Redis key is reported as queued.
    """

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.aclose = AsyncMock()
    mock_create_pool.return_value = mock_redis

    response = await async_client.get("/ingest/status/unknown")

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
