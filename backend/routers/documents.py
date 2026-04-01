from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
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

    try:
        documents, truncated = await list_indexed_documents_for_company(settings, stripped, qdrant)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not list documents from the vector store",
        ) from None

    return DocumentIndexResponse(company_id=stripped, documents=documents, truncated=truncated)
