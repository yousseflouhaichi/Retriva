"""
Turn Unstructured elements into text chunks sized for embedding.

Uses tiktoken windows so chunk boundaries align with the embedding tokenizer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import tiktoken

from backend.core.config import Settings


@dataclass(frozen=True)
class ChunkRecord:
    """One embeddable slice of document text with citation-oriented metadata."""

    text: str
    page_number: int
    chunk_type: str
    parent_chunk_id: str | None


def _split_text_to_token_windows(
    text: str,
    encoding: tiktoken.Encoding,
    max_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """
    Split text into overlapping token windows without breaking on naive character cuts.
    """

    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return [text]

    windows: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        window_tokens = tokens[start:end]
        windows.append(encoding.decode(window_tokens))
        if end >= len(tokens):
            break
        next_start = end - overlap_tokens
        start = max(next_start, start + 1)
    return windows


def chunks_from_elements(
    settings: Settings,
    elements: list[dict[str, Any]],
) -> list[ChunkRecord]:
    """
    Build chunk records from Unstructured element dicts.

    Args:
        settings: Chunk sizing and tiktoken encoding name.
        elements: Raw elements from Unstructured.

    Returns:
        list[ChunkRecord]: Chunks ready for embedding; may be empty if no text was found.
    """

    encoding = tiktoken.get_encoding(settings.tiktoken_encoding)
    max_tokens = settings.chunk_max_tokens
    overlap = min(settings.chunk_overlap_tokens, max_tokens - 1) if max_tokens > 1 else 0

    records: list[ChunkRecord] = []
    for element in elements:
        text = (element.get("text") or "").strip()
        if not text:
            continue

        metadata = element.get("metadata") if isinstance(element.get("metadata"), dict) else {}
        page_raw = metadata.get("page_number", 0)
        try:
            page_number = int(page_raw)
        except (TypeError, ValueError):
            page_number = 0

        chunk_type = str(element.get("type") or "unknown")
        parent = element.get("element_id")
        parent_chunk_id = str(parent) if parent is not None else None

        for window in _split_text_to_token_windows(text, encoding, max_tokens, overlap):
            trimmed = window.strip()
            if trimmed:
                records.append(
                    ChunkRecord(
                        text=trimmed,
                        page_number=page_number,
                        chunk_type=chunk_type,
                        parent_chunk_id=parent_chunk_id,
                    )
                )

    return records
