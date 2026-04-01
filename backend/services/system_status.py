"""
Dependency probes for operations dashboards (Qdrant, Redis, Unstructured).

Returns safe summaries without leaking stack traces or secrets.
"""

from __future__ import annotations

import asyncio
import httpx
import redis.asyncio as redis_lib
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings
from backend.models.schemas import DependencyCheckResult, PublicAppInfo, SystemStatusResponse


def _safe_error_detail(exc: BaseException) -> str:
    """
    Map exceptions to a short client-safe category.
    """

    if isinstance(exc, httpx.TimeoutException | TimeoutError):
        return "timeout"
    if isinstance(exc, OSError):
        return "connection_error"
    return "unavailable"


async def _check_qdrant(url: str) -> DependencyCheckResult:
    """
    Verify Qdrant responds to list collections.
    """

    client = AsyncQdrantClient(url=url)
    try:
        await client.get_collections()
        return DependencyCheckResult(name="qdrant", ok=True, detail=None)
    except Exception as exc:
        return DependencyCheckResult(name="qdrant", ok=False, detail=_safe_error_detail(exc))
    finally:
        await client.close()


async def _check_redis(url: str) -> DependencyCheckResult:
    """
    Verify Redis accepts PING.
    """

    client = redis_lib.from_url(url, decode_responses=True)
    try:
        await client.ping()
        return DependencyCheckResult(name="redis", ok=True, detail=None)
    except Exception as exc:
        return DependencyCheckResult(name="redis", ok=False, detail=_safe_error_detail(exc))
    finally:
        await client.aclose()


async def _check_unstructured(base_url: str, timeout_seconds: float) -> DependencyCheckResult:
    """
    Verify Unstructured API base URL responds (any 2xx or 404 counts as reachable service).
    """

    root = base_url.rstrip("/") or base_url
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as http_client:
            response = await http_client.get(root)
        if response.status_code < 500:
            return DependencyCheckResult(name="unstructured", ok=True, detail=None)
        return DependencyCheckResult(name="unstructured", ok=False, detail="bad_response")
    except Exception as exc:
        return DependencyCheckResult(name="unstructured", ok=False, detail=_safe_error_detail(exc))


async def build_system_status(settings: Settings) -> SystemStatusResponse:
    """
    Run dependency checks in parallel and attach non-secret app metadata for settings UIs.
    """

    timeout = max(0.5, min(settings.status_dependency_timeout_seconds, 30.0))
    qdrant_task = asyncio.create_task(_check_qdrant(settings.qdrant_url))
    redis_task = asyncio.create_task(_check_redis(settings.redis_url))
    unstructured_task = asyncio.create_task(
        _check_unstructured(settings.unstructured_api_url, timeout),
    )
    qdrant_result, redis_result, unstructured_result = await asyncio.gather(
        qdrant_task,
        redis_task,
        unstructured_task,
    )

    app_info = PublicAppInfo(
        environment=settings.environment,
        embeddings_model=settings.embeddings_model,
        query_answer_model=settings.query_answer_model,
        query_transform_model=settings.query_transform_model,
    )

    return SystemStatusResponse(
        dependencies=[qdrant_result, redis_result, unstructured_result],
        app=app_info,
    )
