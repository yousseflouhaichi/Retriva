"""
Tests for Qdrant-backed workspace listing.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from qdrant_client import AsyncQdrantClient

from backend.core.qdrant_client import get_qdrant_client
from backend.main import app
from backend.services.collections import list_tenant_workspace_ids


@pytest.mark.asyncio
async def test_list_tenant_workspace_ids_filters_company_prefix() -> None:
    """
    Only company_* collections become workspace ids; names are sorted and unique.
    """

    client = AsyncMock(spec=AsyncQdrantClient)
    client.get_collections = AsyncMock(
        return_value=SimpleNamespace(
            collections=[
                SimpleNamespace(name="company_zebra"),
                SimpleNamespace(name="other"),
                SimpleNamespace(name="company_acme"),
                SimpleNamespace(name="company_acme"),
            ],
        ),
    )

    ids = await list_tenant_workspace_ids(client)
    assert ids == ["acme", "zebra"]


@pytest.mark.asyncio
async def test_get_workspaces_endpoint(async_client: AsyncClient) -> None:
    """
    GET /workspaces returns sorted ids from mocked Qdrant.
    """

    mock_qdrant = AsyncMock(spec=AsyncQdrantClient)
    mock_qdrant.get_collections = AsyncMock(
        return_value=SimpleNamespace(
            collections=[SimpleNamespace(name="company_demo"), SimpleNamespace(name="company_x")],
        ),
    )

    async def _override_qdrant():
        yield mock_qdrant

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.get("/workspaces")
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspaces"] == ["demo", "x"]


@pytest.mark.asyncio
async def test_get_workspaces_endpoint_503_when_qdrant_fails(async_client: AsyncClient) -> None:
    """
    Qdrant errors map to a safe 503 without leaking internals.
    """

    mock_qdrant = AsyncMock(spec=AsyncQdrantClient)
    mock_qdrant.get_collections = AsyncMock(side_effect=OSError("refused"))

    async def _override_qdrant():
        yield mock_qdrant

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.get("/workspaces")
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 503
    assert "vector store" in response.json()["detail"].lower()
