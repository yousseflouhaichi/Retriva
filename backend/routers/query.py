from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.core.config import Settings, get_settings
from backend.graphs.query_pipeline import run_query_pipeline
from backend.models.schemas import QueryRequest
from backend.services.collections import company_collection_name
from backend.services.generator import stream_answer_tokens

router = APIRouter()


@router.post("/stream")
async def query_stream(
    request: QueryRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> EventSourceResponse:
    """
    Run LangGraph transform and hybrid retrieval, then stream a grounded answer over SSE.
    """

    try:
        company_collection_name(request.company_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    async def event_gen():
        try:
            state = await run_query_pipeline(settings, request.company_id, request.question)
            if state.get("error"):
                yield {"event": "error", "data": str(state["error"])}
                yield {"event": "done", "data": ""}
                return

            contexts = state.get("contexts") or []
            sources: list[dict[str, str | int]] = []
            for ctx in contexts:
                text = str(ctx.get("text", ""))
                preview = text[:280] + ("…" if len(text) > 280 else "")
                sources.append(
                    {
                        "point_id": str(ctx.get("point_id", "")),
                        "document_name": str(ctx.get("document_name", "")),
                        "page_number": int(ctx.get("page_number", 0) or 0),
                        "preview": preview,
                    }
                )
            yield {"event": "sources", "data": json.dumps(sources)}
            async for token in stream_answer_tokens(settings, request.question, contexts):
                yield {"event": "token", "data": token}
            yield {"event": "done", "data": ""}
        except ValueError as exc:
            yield {"event": "error", "data": str(exc)}
            yield {"event": "done", "data": ""}
        except Exception:
            yield {"event": "error", "data": "Query pipeline failed"}
            yield {"event": "done", "data": ""}

    return EventSourceResponse(event_gen())
