from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.core.config import Settings, get_settings
from backend.models.schemas import QueryRequest

router = APIRouter()


@router.post("/stream")
async def query_stream(request: QueryRequest, settings: Settings = Depends(get_settings)) -> EventSourceResponse:
    """
    Stream a response via SSE.

    This is a minimal scaffold that proves streaming works end-to-end.
    The full RAG pipeline (transform -> retrieve -> rerank -> generate) is wired later.
    """

    try:
        if not request.company_id.strip():
            raise ValueError("company_id is required")
        if not request.question.strip():
            raise ValueError("question is required")

        async def gen():
            yield {"event": "meta", "data": f"env={settings.environment}"}
            text = f"Echo: {request.question}"
            for token in text.split(" "):
                await asyncio.sleep(0.05)
                yield {"event": "token", "data": token + " "}
            yield {"event": "done", "data": ""}

        return EventSourceResponse(gen())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Query failed") from exc
