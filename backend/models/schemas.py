"""
Pydantic v2 request/response schemas for the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IngestUploadResponse(BaseModel):
    job_id: str


class IngestStatusResponse(BaseModel):
    job_id: str
    status: Literal["queued", "processing", "ready", "failed"]
    detail: str | None = None
    chunks_indexed: int | None = None
    meta: dict[str, Any] | None = None


class QueryRequest(BaseModel):
    company_id: str = Field(min_length=1)
    question: str = Field(min_length=1)


class WorkspacesListResponse(BaseModel):
    """
    Tenant workspace ids derived from Qdrant collection names (company_*).
    """

    workspaces: list[str] = Field(description="Sorted unique workspace ids with indexed data in Qdrant")


class DependencyCheckResult(BaseModel):
    """
    One infrastructure dependency probe result for status dashboards.
    """

    name: str = Field(description="Dependency id, e.g. qdrant, redis, unstructured")
    ok: bool
    detail: str | None = Field(default=None, description="Safe error category when ok is false")


class PublicAppInfo(BaseModel):
    """
    Non-secret model names and environment for a settings or about panel.
    """

    environment: str
    embeddings_model: str
    query_answer_model: str
    query_transform_model: str


class SystemStatusResponse(BaseModel):
    """
    API process is up; dependencies may individually fail.
    """

    status: Literal["ok"] = "ok"
    dependencies: list[DependencyCheckResult]
    app: PublicAppInfo


class SSEEvent(BaseModel):
    event: str
    data: str

