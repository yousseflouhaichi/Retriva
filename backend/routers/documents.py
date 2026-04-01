from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from qdrant_client import AsyncQdrantClient

from backend.core.config import Settings, get_settings
from backend.core.qdrant_client import get_qdrant_client
from backend.models.schemas import DocumentIndexResponse
from backend.services.collections import company_collection_name
from backend.services.document_index import list_indexed_documents_for_company

router = APIRouter()


@router.get("/documents", response_model=DocumentIndexResponse)
async def list_company_documents(
    company_id: str,
    qdrant: AsyncQdrantClient = Depends(get_qdrant_client),
    settings: Settings = Depends(get_settings),
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Page size after aggregation (defaults from config, capped by max)",
    ),
    offset: int = Query(default=0, ge=0, description="Skip this many documents in the sorted list"),
) -> DocumentIndexResponse:
    """
    List distinct document_name values in the tenant Qdrant collection with chunk counts.
    """

    stripped = company_id.strip()
    if not stripped:
        raise HTTPException(status_code=400, detail="company_id is required") from None
    try:
        company_collection_name(stripped)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    max_limit = settings.document_list_max_limit
    default_limit = settings.document_list_default_limit
    requested = limit if limit is not None else default_limit
    eff_limit = max(1, min(max_limit, requested))
    eff_offset = offset

    try:
        documents, truncated, total, used_limit, used_offset = await list_indexed_documents_for_company(
            settings,
            stripped,
            qdrant,
            limit=eff_limit,
            offset=eff_offset,
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not list documents from the vector store",
        ) from None

    return DocumentIndexResponse(
        company_id=stripped,
        documents=documents,
        truncated=truncated,
        total_documents=total,
        limit=used_limit,
        offset=used_offset,
    )
