"""
Document parsing via self-hosted Unstructured API (Docker).

Returns raw element dicts for downstream chunking and embedding.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import httpx

from backend.core.config import Settings


async def parse_document_to_elements(settings: Settings, file_path: Path) -> list[dict[str, Any]]:
    """
    Send a local file to Unstructured and return parsed elements.

    Args:
        settings: Application settings (base URL and timeouts).
        file_path: Path to the uploaded file on disk.

    Returns:
        list[dict[str, Any]]: Unstructured element objects.

    Raises:
        RuntimeError: When the response shape is unexpected.
        httpx.HTTPError: When the HTTP request fails.
    """

    base = settings.unstructured_api_url.rstrip("/")
    url = f"{base}/general/v0/general"
    timeout = httpx.Timeout(settings.unstructured_timeout_seconds)

    file_bytes = await asyncio.to_thread(file_path.read_bytes)
    filename = file_path.name
    files = {"files": (filename, file_bytes, "application/octet-stream")}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, files=files)
        response.raise_for_status()
        body = response.json()

    if isinstance(body, list):
        return body
    if isinstance(body, dict) and isinstance(body.get("elements"), list):
        return body["elements"]
    raise RuntimeError("Unstructured API returned an unexpected JSON shape")
