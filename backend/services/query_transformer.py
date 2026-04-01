"""
Multi-query rewriting and HyDE-style hypothetical document for retrieval.

Runs before any vector or lexical search against Qdrant or BM25.
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from backend.core.config import Settings


async def transform_query_for_retrieval(
    settings: Settings,
    question: str,
) -> tuple[list[str], str]:
    """
    Produce sub-queries and a short hypothetical answer paragraph for dense lookup.

    Args:
        settings: Models and how many paraphrases to emit.
        question: Raw user question.

    Returns:
        tuple[list[str], str]: Sub-queries and HyDE document text.

    Raises:
        ValueError: When API key is missing or the model output is unusable.
        RuntimeError: When JSON parsing or schema validation fails.
    """

    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is required for query transformation")

    count = settings.multi_query_count
    system = (
        "You rewrite user questions for document retrieval. "
        f"Return strict JSON with keys: sub_queries (array of exactly {count} strings, "
        "each a concise search query), hyde_document (one short hypothetical passage that "
        "would answer the question if it were true, for embedding). "
        "Do not include markdown or commentary outside JSON."
    )
    user = f"User question:\n{question.strip()}"

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.chat.completions.create(
            model=settings.query_transform_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        raw = response.choices[0].message.content or ""
        payload: dict[str, Any] = json.loads(raw)
        sub_queries_raw = payload.get("sub_queries")
        hyde = str(payload.get("hyde_document", "")).strip()
        if not isinstance(sub_queries_raw, list) or not hyde:
            raise RuntimeError("Transform model returned an invalid JSON shape")
        sub_queries = [str(item).strip() for item in sub_queries_raw if str(item).strip()]
        if len(sub_queries) < 1:
            raise RuntimeError("Transform model returned no sub_queries")
        while len(sub_queries) < count:
            sub_queries.append(sub_queries[-1])
        sub_queries = sub_queries[:count]
        return sub_queries, hyde
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Transform model returned non-JSON: {exc}") from exc
    finally:
        await client.close()
