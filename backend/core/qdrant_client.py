"""
Qdrant client dependency.

Keeps Qdrant wiring in one place so routers/services can depend-inject a client.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings, get_settings


async def get_qdrant_client(settings: Settings | None = None) -> AsyncIterator[AsyncQdrantClient]:
    """
    Provide an AsyncQdrantClient configured from Settings.
    """

    cfg = settings or get_settings()
    client = AsyncQdrantClient(url=cfg.qdrant_url)
    try:
        yield client
    finally:
        await client.close()
