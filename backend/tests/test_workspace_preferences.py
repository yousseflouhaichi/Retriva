"""
Tests for workspace preferences stored in Redis.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_workspace_preferences_returns_defaults_when_redis_empty(async_client: AsyncClient) -> None:
    """
    Missing Redis key yields default preference model.
    """

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.aclose = AsyncMock()

    with patch("backend.services.workspace_settings.redis_lib.from_url", return_value=mock_redis):
        response = await async_client.get("/workspace/preferences", params={"company_id": "demo"})

    assert response.status_code == 200
    body = response.json()
    assert body["theme"] == "system"
    assert body["density"] == "comfortable"
    assert body["show_streaming_indicator"] is True


@pytest.mark.asyncio
async def test_patch_workspace_preferences_merges(async_client: AsyncClient) -> None:
    """
    PATCH updates stored JSON and returns merged preferences.
    """

    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    mock_redis.aclose = AsyncMock()

    with patch("backend.services.workspace_settings.redis_lib.from_url", return_value=mock_redis):
        response = await async_client.patch(
            "/workspace/preferences",
            params={"company_id": "demo"},
            json={"theme": "dark"},
        )

    assert response.status_code == 200
    assert response.json()["theme"] == "dark"
    assert response.json()["density"] == "comfortable"
    mock_redis.set.assert_awaited()


@pytest.mark.asyncio
async def test_workspace_preferences_rejects_invalid_company(async_client: AsyncClient) -> None:
    response = await async_client.get("/workspace/preferences", params={"company_id": "###"})
    assert response.status_code == 400
