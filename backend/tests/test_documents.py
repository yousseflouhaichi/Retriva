"""
Tests for GET /documents and document_index service.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

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
    t_old = "2025-01-01T12:00:00+00:00"
    t_new = "2026-01-02T12:00:00+00:00"
    client.scroll = AsyncMock(
        side_effect=[
            (
                [
                    SimpleNamespace(
                        payload={
                            "document_name": "Beta.pdf",
                            "indexed_at": t_old,
                        },
                    ),
                    SimpleNamespace(
                        payload={
                            "document_name": "Alpha.pdf",
                            "indexed_at": t_new,
                        },
                    ),
                ],
                "page2",
            ),
            (
                [
                    SimpleNamespace(
                        payload={
                            "document_name": "Alpha.pdf",
                            "indexed_at": t_old,
                        },
                    ),
                    SimpleNamespace(payload={"document_name": ""}),
                ],
                None,
            ),
        ],
    )

    items, truncated, total, lim, off = await list_indexed_documents_for_company(
        settings,
        "demo",
        client,
        limit=50,
        offset=0,
    )

    assert truncated is False
    assert total == 2
    assert lim == 50
    assert off == 0
    assert [(row.document_name, row.chunk_count) for row in items] == [
        ("Alpha.pdf", 2),
        ("Beta.pdf", 1),
    ]
    alpha = items[0]
    assert alpha.last_indexed_at == datetime.fromisoformat(t_new.replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_list_indexed_documents_pagination_slice() -> None:
    """
    Limit and offset apply to the sorted document list after aggregation.
    """

    settings = Settings.model_construct(
        document_list_scroll_batch_size=64,
        document_index_max_points_scanned=1000,
    )
    client = AsyncMock(spec=AsyncQdrantClient)
    client.collection_exists = AsyncMock(return_value=True)
    client.scroll = AsyncMock(
        return_value=(
            [
                SimpleNamespace(payload={"document_name": "a.pdf"}),
                SimpleNamespace(payload={"document_name": "b.pdf"}),
                SimpleNamespace(payload={"document_name": "c.pdf"}),
            ],
            None,
        ),
    )

    page1, truncated, total, _, _ = await list_indexed_documents_for_company(
        settings,
        "demo",
        client,
        limit=1,
        offset=0,
    )
    page2, _, total2, _, off2 = await list_indexed_documents_for_company(
        settings,
        "demo",
        client,
        limit=1,
        offset=1,
    )

    assert not truncated
    assert total == total2 == 3
    assert [row.document_name for row in page1] == ["a.pdf"]
    assert [row.document_name for row in page2] == ["b.pdf"]
    assert off2 == 1


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

    items, truncated, total, lim, off = await list_indexed_documents_for_company(
        settings,
        "newco",
        client,
        limit=20,
        offset=0,
    )

    assert items == []
    assert truncated is False
    assert total == 0
    assert lim == 20
    assert off == 0
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
        await list_indexed_documents_for_company(settings, "###", client, limit=10, offset=0)

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
async def test_get_documents_http_includes_pagination_fields(async_client: AsyncClient) -> None:
    """
    JSON includes total_documents, limit, and offset.
    """

    mock_client = AsyncMock(spec=AsyncQdrantClient)
    mock_client.collection_exists = AsyncMock(return_value=True)
    mock_client.scroll = AsyncMock(return_value=([], None))

    async def _override_qdrant():
        yield mock_client

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.get(
            "/documents",
            params={"company_id": "demo", "limit": 25, "offset": 0},
        )
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 200
    body = response.json()
    assert body["total_documents"] == 0
    assert body["limit"] == 25
    assert body["offset"] == 0


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


@pytest.mark.asyncio
async def test_delete_document_http_success(async_client: AsyncClient) -> None:
    """
    DELETE /documents calls Qdrant delete with a document_name filter and rebuilds BM25.
    """

    mock_client = AsyncMock(spec=AsyncQdrantClient)
    mock_client.collection_exists = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock()

    async def _override_qdrant():
        yield mock_client

    with patch(
        "backend.services.document_delete.replace_bm25_corpus_from_qdrant",
        new_callable=AsyncMock,
    ) as mock_rebuild:
        app.dependency_overrides[get_qdrant_client] = _override_qdrant
        try:
            response = await async_client.delete(
                "/documents",
                params={"company_id": "demo", "document_name": "a.pdf"},
            )
        finally:
            app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 200
    assert response.json()["document_name"] == "a.pdf"
    assert response.json()["deleted"] is True
    mock_client.delete.assert_called_once()
    mock_rebuild.assert_called_once()


@pytest.mark.asyncio
async def test_delete_document_http_404_when_collection_missing(async_client: AsyncClient) -> None:
    """
    Missing tenant collection returns 404.
    """

    mock_client = AsyncMock(spec=AsyncQdrantClient)
    mock_client.collection_exists = AsyncMock(return_value=False)

    async def _override_qdrant():
        yield mock_client

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.delete(
            "/documents",
            params={"company_id": "demo", "document_name": "a.pdf"},
        )
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_http_400_invalid_company(async_client: AsyncClient) -> None:
    """
    Invalid company_id returns 400.
    """

    mock_client = AsyncMock(spec=AsyncQdrantClient)

    async def _override_qdrant():
        yield mock_client

    app.dependency_overrides[get_qdrant_client] = _override_qdrant
    try:
        response = await async_client.delete(
            "/documents",
            params={"company_id": "###", "document_name": "a.pdf"},
        )
    finally:
        app.dependency_overrides.pop(get_qdrant_client, None)

    assert response.status_code == 400
