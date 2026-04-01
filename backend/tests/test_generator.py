"""
Tests for answer streaming (OpenAI client mocked; no network).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.config import Settings
from backend.services.generator import stream_answer_tokens


class _FakeOpenAIStream:
    """Minimal async iterator matching chat completion stream chunks."""

    def __init__(self, chunks: list[MagicMock]) -> None:
        self._chunks = chunks
        self._index = 0

    def __aiter__(self) -> _FakeOpenAIStream:
        return self

    async def __anext__(self) -> MagicMock:
        if self._index >= len(self._chunks):
            raise StopAsyncIteration
        chunk = self._chunks[self._index]
        self._index += 1
        return chunk


def _chunk_with_delta(content: str | None) -> MagicMock:
    delta = MagicMock()
    delta.content = content
    choice = MagicMock()
    choice.delta = delta
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


@pytest.mark.asyncio
async def test_stream_answer_tokens_requires_api_key() -> None:
    """
    Missing key fails fast with a clear error before any client call.
    """

    settings = Settings.model_validate({"OPENAI_API_KEY": ""})
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        async for _ in stream_answer_tokens(settings, "q", []):
            pass


@pytest.mark.asyncio
@patch("backend.services.generator.AsyncOpenAI")
async def test_stream_answer_tokens_yields_deltas(mock_client_class: MagicMock) -> None:
    """
    Token fragments from the OpenAI stream are yielded in order.
    """

    empty_choices = MagicMock()
    empty_choices.choices = []

    chunks = [
        _chunk_with_delta("Hello"),
        empty_choices,
        _chunk_with_delta(None),
        _chunk_with_delta(" world"),
    ]
    mock_stream = _FakeOpenAIStream(chunks)
    instance = mock_client_class.return_value
    instance.chat.completions.create = AsyncMock(return_value=mock_stream)
    instance.close = AsyncMock()

    settings = Settings.model_validate({"OPENAI_API_KEY": "sk-test"})
    contexts = [{"text": "body", "document_name": "a.pdf", "page_number": 1}]

    out: list[str] = []
    async for token in stream_answer_tokens(settings, "Question?", contexts):
        out.append(token)

    assert out == ["Hello", " world"]
    instance.chat.completions.create.assert_awaited_once()
    instance.close.assert_awaited()
