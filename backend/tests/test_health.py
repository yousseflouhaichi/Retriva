from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(async_client: AsyncClient) -> None:
    """
    Health endpoint responds with 200 and expected JSON shape.
    """

    response = await async_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "ok"
    assert "environment" in payload
    assert "timestamp" in payload
