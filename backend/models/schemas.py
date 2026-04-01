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


class IngestionWorkerSnapshot(BaseModel):
    """
    ARQ ingestion queue depth and worker heartbeat visible in Redis.
    """

    queue_name: str = Field(description="Redis sorted-set key holding pending jobs")
    jobs_queued: int = Field(ge=0, description="Approximate count of jobs waiting in the queue")
    worker_health_ok: bool = Field(description="True when the worker health-check key is present")
    health_detail: str | None = Field(
        default=None,
        description="Truncated worker self-report when healthy, or a safe error hint when probe fails",
    )


class SystemStatusResponse(BaseModel):
    """
    API process is up; dependencies may individually fail.
    """

    status: Literal["ok"] = "ok"
    dependencies: list[DependencyCheckResult]
    app: PublicAppInfo
    ingestion_worker: IngestionWorkerSnapshot


class DocumentIndexItem(BaseModel):
    """
    One logical document aggregated from chunk payloads in Qdrant.
    """

    document_name: str
    chunk_count: int = Field(ge=0)
    last_indexed_at: datetime | None = Field(
        default=None,
        description="Latest chunk indexed_at for this document (new ingests only)",
    )


class DocumentIndexResponse(BaseModel):
    """
    Per-tenant document library derived from vector payloads.
    """

    company_id: str
    documents: list[DocumentIndexItem]
    truncated: bool = Field(
        default=False,
        description="True when the scan stopped early at the configured point cap",
    )
    total_documents: int = Field(
        description="Distinct documents matched before limit/offset pagination",
    )
    limit: int = Field(ge=0, description="Page size applied after aggregation")
    offset: int = Field(ge=0, description="Documents skipped from the sorted list")


class WorkspacePreferences(BaseModel):
    """
    Client-controlled UI preferences for a workspace (stored server-side per company_id).
    """

    theme: Literal["light", "dark", "system"] = "system"
    density: Literal["comfortable", "compact"] = "comfortable"
    show_streaming_indicator: bool = True


class WorkspacePreferencesPatch(BaseModel):
    """
    Partial update for workspace preferences; omitted fields stay unchanged.
    """

    theme: Literal["light", "dark", "system"] | None = None
    density: Literal["comfortable", "compact"] | None = None
    show_streaming_indicator: bool | None = None


class SSEEvent(BaseModel):
    event: str
    data: str

