"""
Tests for GET /documents and document_index service.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings
from backend.core.qdrant_client import get_qdrant_client
from backend.main import app
from backend.services.document_index import list_indexed_documents_for_company


@pytest.mark.asyncio
async def test_list_indexed_documents_aggregates_and_sorts() -> None:
    """
    Chunk counts group by document_name; results are sorted case-insensitively by name.
    """

    settings = Settings.model_construct(
        document_list_scroll_batch_size=10,
        document_index_max_points_scanned=500,
    )
    client = AsyncMock(spec=AsyncQdrantClient)
    client.collection_exists = AsyncMock(return_value=True)
    client.scroll = AsyncMock(
        side_effect=[
            (
                [
                    SimpleNamespace(payload={"document_name": "Beta.pdf"}),
                    SimpleNamespace(payload={"document_name": "Alpha.pdf"}),
                ],
                "page2",
            ),
            (
                [
                    SimpleNamespace(payload={"document_name": "Alpha.pdf"}),
                    SimpleNamespace(payload={"document_name": ""}),
                ],
                None,
            ),
        ],
    )

    items, truncated = await list_indexed_documents_for_company(settings, "demo", client)

    assert truncated is False
    assert [(row.document_name, row.chunk_count) for row in items] == [
        ("Alpha.pdf", 2),
        ("Beta.pdf", 1),
    ]


@pytest.mark.asyncio
async def test_list_indexed_documents_missing_collection() -> None:
    """
    Unknown collection yields an empty list without calling scroll.
    """

    settings = Settings.model_construct(
        document_list_scroll_batch_size=64,
        document_index_max_points_scanned=1000,
    )
    client = AsyncMock(spec=AsyncQdrantClient)
    client.collection_exists = AsyncMock(return_value=False)

    items, truncated = await list_indexed_documents_for_company(settings, "newco", client)

    assert items == []
    assert truncated is False
    client.scroll.assert_not_called()


@pytest.mark.asyncio
async def test_list_indexed_documents_invalid_company_id() -> None:
    """
    Invalid tenant id raises before Qdrant calls.
    """

    settings = Settings.model_construct(
        document_list_scroll_batch_size=64,
        document_index_max_points_scanned=1000,
    )
    client = AsyncMock(spec=AsyncQdrantClient)

    with pytest.raises(ValueError):
        await list_indexed_documents_for_company(settings, "###", client)

    client.collection_exists.assert_not_called()


@pytest.mark.asyncio
async def test_get_documents_http_rejects_invalid_company(async_client: AsyncClient) -> None:
    """
    Router returns 400 for invalid company_id.
    """

    response = await async_client.get("/documents", params={"company_id": "###"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_documents_http_rejects_blank_company(async_client: AsyncClient) -> None:
    """
    Whitespace-only company_id is rejected.
    """

    response = await async_client.get("/documents", params={"company_id": "   "})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_documents_http_503_when_scroll_fails(async_client: AsyncClient) -> None:
    """
    Qdrant errors map to a safe 503.
    """

    mock_client = AsyncMock(spec=AsyncQdrantClient)
    mock_client.collection_exists = AsyncMock(return_value=True)
    mock_client.scroll = AsyncMock(side_effect=RuntimeError("boom"))

    async def _override_qdrant():
        yield mock_client

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.get("/documents", params={"company_id": "demo"})
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 503
