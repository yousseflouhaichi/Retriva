from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_query_stream_rejects_invalid_company_id(async_client: AsyncClient) -> None:
    """
    Invalid company_id returns 400 before streaming.
    """

    response = await async_client.post(
        "/query/stream",
        json={"company_id": "###", "question": "hello"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
@patch("backend.routers.query.stream_answer_tokens")
@patch("backend.routers.query.run_query_pipeline", new_callable=AsyncMock)
async def test_query_stream_sse_contains_sources_and_tokens(
    mock_pipeline: AsyncMock,
    mock_stream,
    async_client: AsyncClient,
) -> None:
    """
    Successful pipeline yields SSE sources then token events (external calls mocked).
    """

    async def fake_tokens(*args, **kwargs):
        yield "Answer"
        yield " "

    mock_pipeline.return_value = {
        "error": None,
        "contexts": [
            {
                "point_id": "p1",
                "text": "Chunk about RAG.",
                "document_name": "doc.md",
                "page_number": 1,
            },
        ],
    }
    mock_stream.side_effect = fake_tokens

    async with async_client.stream(
        "POST",
        "/query/stream",
        json={"company_id": "demo", "question": "What is RAG?"},
    ) as response:
        assert response.status_code == 200
        raw = b""
        async for chunk in response.aiter_bytes():
            raw += chunk

    text = raw.decode()
    assert "event: sources" in text
    assert "point_id" in text
    assert "event: token" in text
    assert "Answer" in text
    assert "event: done" in text


@pytest.mark.asyncio
@patch("backend.routers.query.run_query_pipeline", new_callable=AsyncMock)
async def test_query_stream_pipeline_error_emits_error_event(
    mock_pipeline: AsyncMock,
    async_client: AsyncClient,
) -> None:
    """
    Graph or retrieval errors surface as SSE error then done.
    """

    mock_pipeline.return_value = {"error": "upstream failed", "contexts": []}

    async with async_client.stream(
        "POST",
        "/query/stream",
        json={"company_id": "demo", "question": "q"},
    ) as response:
        assert response.status_code == 200
        raw = b""
        async for chunk in response.aiter_bytes():
            raw += chunk

    text = raw.decode()
    assert "event: error" in text
    assert "upstream failed" in text
    assert "event: done" in text
