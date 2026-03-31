"""
OpenAI text embeddings for ingestion (async).

Batches requests according to settings to limit rate and payload size.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from backend.core.config import Settings


async def embed_texts(settings: Settings, texts: list[str]) -> list[list[float]]:
    """
    Embed a list of texts with the configured OpenAI embedding model.

    Args:
        settings: API key, model name, and batch size.
        texts: Non-empty strings to embed in original order.

    Returns:
        list[list[float]]: One embedding vector per input string.

    Raises:
        ValueError: When OpenAI API key is missing or texts is empty in an invalid way.
        RuntimeError: When the API response does not align with inputs.
    """

    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is required for embedding during ingestion")
    if not texts:
        return []

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        batch_size = max(1, settings.embedding_batch_size)
        all_vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = await client.embeddings.create(model=settings.embeddings_model, input=batch)
            ordered = sorted(response.data, key=lambda item: item.index)
            if len(ordered) != len(batch):
                raise RuntimeError("OpenAI embeddings response length mismatch for batch")
            all_vectors.extend(item.embedding for item in ordered)
        return all_vectors
    finally:
        await client.close()
