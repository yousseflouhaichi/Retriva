"""
Redis client dependency.

Used by both API endpoints and the ARQ worker for job status and queuing.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import redis.asyncio as redis

from backend.core.config import Settings, get_settings


async def get_redis(settings: Settings | None = None) -> AsyncIterator[redis.Redis]:
    """
    Provide an async Redis client configured from Settings.
    """

    cfg = settings or get_settings()
    client = redis.from_url(cfg.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()

