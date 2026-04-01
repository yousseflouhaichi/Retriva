from __future__ import annotations

from fastapi import APIRouter

from backend.routers.collections import router as collections_router
from backend.routers.documents import router as documents_router
from backend.routers.ingest import router as ingest_router
from backend.routers.query import router as query_router
from backend.routers.status import router as status_router


api_router = APIRouter()
api_router.include_router(collections_router, tags=["health"])
api_router.include_router(status_router, tags=["status"])
api_router.include_router(documents_router, tags=["documents"])
api_router.include_router(ingest_router, prefix="/ingest", tags=["ingest"])
api_router.include_router(query_router, prefix="/query", tags=["query"])

