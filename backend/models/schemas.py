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
    meta: dict[str, Any] | None = None


class QueryRequest(BaseModel):
    company_id: str = Field(min_length=1)
    question: str = Field(min_length=1)


class SSEEvent(BaseModel):
    event: str
    data: str

