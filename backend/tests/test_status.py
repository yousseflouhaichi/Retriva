"""
Tests for GET /status and system_status service.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.core.config import Settings
from backend.models.schemas import DependencyCheckResult, PublicAppInfo, SystemStatusResponse
from backend.services import system_status as system_status_module


def _minimal_settings() -> Settings:
    """
    Settings instance without loading .env (construct only).
    """

    return Settings.model_construct(
        environment="test",
        qdrant_url="http://qdrant.test",
        redis_url="redis://redis.test/0",
        unstructured_api_url="http://unstructured.test",
        embeddings_model="text-embedding-test",
        query_answer_model="answer-model",
        query_transform_model="transform-model",
        status_dependency_timeout_seconds=2.0,
    )


@pytest.mark.asyncio
async def test_build_system_status_merges_probe_results() -> None:
    """
    All probes are awaited and ordered in the response with app metadata.
    """

    settings = _minimal_settings()
    with (
        patch.object(
            system_status_module,
            "_check_qdrant",
            AsyncMock(return_value=DependencyCheckResult(name="qdrant", ok=True)),
        ),
        patch.object(
            system_status_module,
            "_check_redis",
            AsyncMock(return_value=DependencyCheckResult(name="redis", ok=False, detail="timeout")),
        ),
        patch.object(
            system_status_module,
            "_check_unstructured",
            AsyncMock(return_value=DependencyCheckResult(name="unstructured", ok=True)),
        ),
    ):
        result = await system_status_module.build_system_status(settings)

    assert result.status == "ok"
    assert [d.name for d in result.dependencies] == ["qdrant", "redis", "unstructured"]
    assert result.dependencies[1].ok is False
    assert result.dependencies[1].detail == "timeout"
    assert result.app.environment == "test"
    assert result.app.embeddings_model == "text-embedding-test"


@pytest.mark.asyncio
async def test_status_http_endpoint(async_client: AsyncClient) -> None:
    """
    Router returns JSON matching SystemStatusResponse when service is patched.
    """

    canned = SystemStatusResponse(
        dependencies=[
            DependencyCheckResult(name="qdrant", ok=True),
            DependencyCheckResult(name="redis", ok=True),
            DependencyCheckResult(name="unstructured", ok=True),
        ],
        app=PublicAppInfo(
            environment="test",
            embeddings_model="e",
            query_answer_model="a",
            query_transform_model="t",
        ),
    )
    with patch(
        "backend.routers.status.build_system_status",
        AsyncMock(return_value=canned),
    ):
        response = await async_client.get("/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert len(body["dependencies"]) == 3
    assert body["app"]["query_answer_model"] == "a"
