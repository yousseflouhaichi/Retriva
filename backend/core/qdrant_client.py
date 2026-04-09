"""
Qdrant client dependency.

Keeps Qdrant wiring in one place so routers/services can depend-inject a client.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings, get_settings


async def get_qdrant_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncIterator[AsyncQdrantClient]:
    """
    Provide an AsyncQdrantClient configured from Settings.
    """

    cfg = settings
    client = AsyncQdrantClient(url=cfg.qdrant_url, timeout=cfg.qdrant_api_timeout_seconds)
    try:
        yield client
    finally:
        await client.close()
