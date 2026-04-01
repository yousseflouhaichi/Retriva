"""
Stream grounded answers using only retrieved chunk text (OpenAI chat).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI

from backend.core.config import Settings


async def stream_answer_tokens(
    settings: Settings,
    question: str,
    contexts: list[dict[str, Any]],
) -> AsyncIterator[str]:
    """
    Stream completion tokens; the model must rely exclusively on numbered context blocks.

    Args:
        settings: API key, model, and max tokens.
        question: Original user question.
        contexts: Reranked chunks with text, document_name, page_number.

    Yields:
        str: Token fragments from the model stream.

    Raises:
        ValueError: When OpenAI API key is missing.
    """

    if not settings.openai_api_key.strip():
        raise ValueError("OPENAI_API_KEY is required for answer generation")

    system = (
        "You are a careful assistant for internal company documents. "
        "Answer using only the numbered context passages. "
        "If the context does not contain enough information, say so clearly. "
        "When you use a fact, cite the passage number in brackets like [1]. "
        "Do not invent sources, filenames, or page numbers that are not in the context headers."
    )
    blocks: list[str] = []
    for idx, ctx in enumerate(contexts, start=1):
        doc = str(ctx.get("document_name", "unknown"))
        page = ctx.get("page_number", 0)
        body = str(ctx.get("text", ""))
        blocks.append(f"[{idx}] (document={doc!r} page={page})\n{body}")
    if blocks:
        user_content = f"Question:\n{question.strip()}\n\nContext:\n\n" + "\n\n---\n\n".join(blocks)
    else:
        user_content = (
            f"Question:\n{question.strip()}\n\n"
            "There is no retrieved context. Reply that no relevant documents were found."
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        stream = await client.chat.completions.create(
            model=settings.query_answer_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_content},
            ],
            max_tokens=settings.query_answer_max_tokens,
            stream=True,
            temperature=0.2,
        )
        async for chunk in stream:
            choices = chunk.choices
            if not choices:
                continue
            delta = choices[0].delta.content
            if delta:
                yield delta
    finally:
        await client.close()
