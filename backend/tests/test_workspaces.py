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
async def test_list_tenant_workspace_ids_plain_and_legacy_names() -> None:
    """
    Plain safe collection names and legacy company_* map to workspace ids; invalid names skipped.
    """

    client = AsyncMock(spec=AsyncQdrantClient)
    client.get_collections = AsyncMock(
        return_value=SimpleNamespace(
            collections=[
                SimpleNamespace(name="zebra"),
                SimpleNamespace(name="has.dot"),
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
            collections=[SimpleNamespace(name="demo"), SimpleNamespace(name="x")],
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


@pytest.mark.asyncio
async def test_post_workspaces_creates_collection_when_missing(async_client: AsyncClient) -> None:
    """
    POST /workspaces creates a Qdrant collection and returns created=true.
    """

    mock_qdrant = AsyncMock(spec=AsyncQdrantClient)
    mock_qdrant.collection_exists = AsyncMock(return_value=False)
    mock_qdrant.create_collection = AsyncMock()

    async def _override_qdrant():
        yield mock_qdrant

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.post("/workspaces", json={"workspace_id": "newspace"})
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace_id"] == "newspace"
    assert payload["created"] is True
    mock_qdrant.create_collection.assert_called_once()


@pytest.mark.asyncio
async def test_post_workspaces_idempotent_when_collection_exists(async_client: AsyncClient) -> None:
    """
    POST /workspaces returns created=false when the collection already exists.
    """

    mock_qdrant = AsyncMock(spec=AsyncQdrantClient)
    mock_qdrant.collection_exists = AsyncMock(return_value=True)
    mock_qdrant.create_collection = AsyncMock()

    async def _override_qdrant():
        yield mock_qdrant

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.post("/workspaces", json={"workspace_id": "existing"})
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["workspace_id"] == "existing"
    assert payload["created"] is False
    mock_qdrant.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_post_workspaces_rejects_invalid_workspace_id(async_client: AsyncClient) -> None:
    """
    Invalid workspace id returns 400 before touching create_collection.
    """

    mock_qdrant = AsyncMock(spec=AsyncQdrantClient)
    mock_qdrant.collection_exists = AsyncMock()
    mock_qdrant.create_collection = AsyncMock()

    async def _override_qdrant():
        yield mock_qdrant

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.post("/workspaces", json={"workspace_id": "###"})
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 400
    mock_qdrant.create_collection.assert_not_called()


@pytest.mark.asyncio
async def test_post_workspaces_503_when_qdrant_fails(async_client: AsyncClient) -> None:
    """
    Qdrant errors map to 503 on POST /workspaces.
    """

    mock_qdrant = AsyncMock(spec=AsyncQdrantClient)
    mock_qdrant.collection_exists = AsyncMock(side_effect=OSError("refused"))

    async def _override_qdrant():
        yield mock_qdrant

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.post("/workspaces", json={"workspace_id": "demo"})
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 503
    assert "vector store" in response.json()["detail"].lower()
