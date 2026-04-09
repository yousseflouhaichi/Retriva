"""
Centralized application configuration.

All runtime configuration must be sourced from this module (pydantic-settings).
Other modules should import `get_settings()` and never read `os.environ` directly.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    cors_extra_allow_origins: str = Field(
        default="",
        alias="CORS_EXTRA_ALLOW_ORIGINS",
        description="Comma-separated browser origins allowed by CORS (in addition to defaults), e.g. http://192.168.1.2:5173",
    )

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")

    qdrant_url: str = Field(
        default="http://127.0.0.1:6333",
        alias="QDRANT_URL",
        description="Use 127.0.0.1 on Windows+Docker Desktop to avoid localhost->IPv6 (::1) hangs.",
    )
    unstructured_api_url: str = Field(default="http://127.0.0.1:8000", alias="UNSTRUCTURED_API_URL")
    redis_url: str = Field(default="redis://127.0.0.1:6379", alias="REDIS_URL")

    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    embeddings_model: str = Field(default="text-embedding-3-large", alias="EMBEDDINGS_MODEL")
    embeddings_dim: int = Field(default=3072, alias="EMBEDDINGS_DIM")
    embedding_batch_size: int = Field(default=16, alias="EMBEDDING_BATCH_SIZE")

    chunk_max_tokens: int = Field(default=512, alias="CHUNK_MAX_TOKENS")
    chunk_overlap_tokens: int = Field(default=64, alias="CHUNK_OVERLAP_TOKENS")
    tiktoken_encoding: str = Field(default="cl100k_base", alias="TIKTOKEN_ENCODING")

    unstructured_timeout_seconds: float = Field(
        default=120.0,
        alias="UNSTRUCTURED_TIMEOUT_SECONDS",
        description="Max seconds for the Unstructured HTTP parse (httpx read timeout).",
    )
    ingestion_job_timeout_seconds: float | None = Field(
        default=None,
        alias="INGESTION_JOB_TIMEOUT_SECONDS",
        description=(
            "ARQ max runtime for one ingest job. When unset, uses UNSTRUCTURED_TIMEOUT_SECONDS plus "
            "INGESTION_JOB_TIMEOUT_BUFFER_SECONDS."
        ),
    )
    ingestion_job_timeout_buffer_seconds: float = Field(
        default=180.0,
        alias="INGESTION_JOB_TIMEOUT_BUFFER_SECONDS",
        description="Added to UNSTRUCTURED_TIMEOUT_SECONDS for the default ARQ job timeout when override is unset.",
    )

    status_dependency_timeout_seconds: float = Field(default=3.0, alias="STATUS_DEPENDENCY_TIMEOUT_SECONDS")

    qdrant_api_timeout_seconds: int = Field(
        default=30,
        alias="QDRANT_API_TIMEOUT_SECONDS",
        description="REST timeout (seconds) for AsyncQdrantClient; avoids indefinite hangs when Qdrant is unreachable.",
    )

    qdrant_upsert_batch_size: int = Field(default=64, alias="QDRANT_UPSERT_BATCH_SIZE")
    document_list_scroll_batch_size: int = Field(default=256, alias="DOCUMENT_LIST_SCROLL_BATCH_SIZE")
    document_index_max_points_scanned: int = Field(default=50_000, alias="DOCUMENT_INDEX_MAX_POINTS_SCANNED")
    document_list_default_limit: int = Field(default=100, alias="DOCUMENT_LIST_DEFAULT_LIMIT")
    document_list_max_limit: int = Field(default=500, alias="DOCUMENT_LIST_MAX_LIMIT")

    bm25_max_corpus_documents: int = Field(default=50_000, alias="BM25_MAX_CORPUS_DOCUMENTS")

    query_transform_model: str = Field(default="gpt-4o-mini", alias="QUERY_TRANSFORM_MODEL")
    multi_query_count: int = Field(default=3, alias="MULTI_QUERY_COUNT")

    dense_top_k_per_subquery: int = Field(default=20, alias="DENSE_TOP_K_PER_SUBQUERY")
    bm25_top_k: int = Field(default=30, alias="BM25_TOP_K")
    rrf_k: int = Field(default=60, alias="RRF_K")
    rerank_candidate_pool: int = Field(default=48, alias="RERANK_CANDIDATE_POOL")

    cohere_rerank_model: str = Field(default="rerank-v3.5", alias="COHERE_RERANK_MODEL")
    rerank_top_n: int = Field(default=8, alias="RERANK_TOP_N")

    query_answer_model: str = Field(default="gpt-4o-mini", alias="QUERY_ANSWER_MODEL")
    query_answer_max_tokens: int = Field(default=1024, alias="QUERY_ANSWER_MAX_TOKENS")

    @model_validator(mode="after")
    def validate_batch_and_chunk_fields(self) -> Self:
        """
        Keep numeric tuning parameters in a sane range so workers do not mis-chunk or starve APIs.
        """

        if self.embedding_batch_size < 1:
            raise ValueError("EMBEDDING_BATCH_SIZE must be at least 1")
        if self.qdrant_upsert_batch_size < 1:
            raise ValueError("QDRANT_UPSERT_BATCH_SIZE must be at least 1")
        if self.chunk_max_tokens < 1:
            raise ValueError("CHUNK_MAX_TOKENS must be at least 1")
        if self.chunk_overlap_tokens < 0:
            raise ValueError("CHUNK_OVERLAP_TOKENS must be non-negative")
        if self.chunk_overlap_tokens >= self.chunk_max_tokens:
            raise ValueError("CHUNK_OVERLAP_TOKENS must be less than CHUNK_MAX_TOKENS")
        if self.bm25_max_corpus_documents < 1:
            raise ValueError("BM25_MAX_CORPUS_DOCUMENTS must be at least 1")
        if self.multi_query_count < 1:
            raise ValueError("MULTI_QUERY_COUNT must be at least 1")
        if self.dense_top_k_per_subquery < 1:
            raise ValueError("DENSE_TOP_K_PER_SUBQUERY must be at least 1")
        if self.bm25_top_k < 1:
            raise ValueError("BM25_TOP_K must be at least 1")
        if self.rrf_k < 1:
            raise ValueError("RRF_K must be at least 1")
        if self.rerank_candidate_pool < 1:
            raise ValueError("RERANK_CANDIDATE_POOL must be at least 1")
        if self.rerank_top_n < 1:
            raise ValueError("RERANK_TOP_N must be at least 1")
        if self.rerank_top_n > self.rerank_candidate_pool:
            raise ValueError("RERANK_TOP_N must not exceed RERANK_CANDIDATE_POOL")
        if self.query_answer_max_tokens < 1:
            raise ValueError("QUERY_ANSWER_MAX_TOKENS must be at least 1")
        if self.status_dependency_timeout_seconds <= 0:
            raise ValueError("STATUS_DEPENDENCY_TIMEOUT_SECONDS must be positive")
        if self.qdrant_api_timeout_seconds < 1:
            raise ValueError("QDRANT_API_TIMEOUT_SECONDS must be at least 1")
        if self.document_list_scroll_batch_size < 1:
            raise ValueError("DOCUMENT_LIST_SCROLL_BATCH_SIZE must be at least 1")
        if self.document_index_max_points_scanned < 1:
            raise ValueError("DOCUMENT_INDEX_MAX_POINTS_SCANNED must be at least 1")
        if self.document_list_default_limit < 1:
            raise ValueError("DOCUMENT_LIST_DEFAULT_LIMIT must be at least 1")
        if self.document_list_max_limit < 1:
            raise ValueError("DOCUMENT_LIST_MAX_LIMIT must be at least 1")
        if self.document_list_default_limit > self.document_list_max_limit:
            raise ValueError("DOCUMENT_LIST_DEFAULT_LIMIT must not exceed DOCUMENT_LIST_MAX_LIMIT")
        if self.unstructured_timeout_seconds <= 0:
            raise ValueError("UNSTRUCTURED_TIMEOUT_SECONDS must be positive")
        if self.ingestion_job_timeout_buffer_seconds < 0:
            raise ValueError("INGESTION_JOB_TIMEOUT_BUFFER_SECONDS must be non-negative")
        if self.ingestion_job_timeout_seconds is not None and self.ingestion_job_timeout_seconds <= 0:
            raise ValueError("INGESTION_JOB_TIMEOUT_SECONDS must be positive when set")
        parse_wait = float(self.unstructured_timeout_seconds)
        effective_job = (
            float(self.ingestion_job_timeout_seconds)
            if self.ingestion_job_timeout_seconds is not None
            else parse_wait + float(self.ingestion_job_timeout_buffer_seconds)
        )
        if effective_job <= parse_wait:
            raise ValueError(
                "Effective ingestion job timeout must exceed UNSTRUCTURED_TIMEOUT_SECONDS; "
                "raise INGESTION_JOB_TIMEOUT_SECONDS or INGESTION_JOB_TIMEOUT_BUFFER_SECONDS.",
            )
        return self

    def effective_ingestion_job_timeout_seconds(self) -> float:
        """
        ARQ job_timeout for ingest_document: explicit override or parse timeout plus buffer.
        """

        parse_wait = float(self.unstructured_timeout_seconds)
        if self.ingestion_job_timeout_seconds is not None:
            return float(self.ingestion_job_timeout_seconds)
        return parse_wait + float(self.ingestion_job_timeout_buffer_seconds)

    def cors_extra_allow_origins_list(self) -> list[str]:
        """
        Parse CORS_EXTRA_ALLOW_ORIGINS into non-empty trimmed origin strings.
        """

        raw = self.cors_extra_allow_origins.strip()
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """

    return Settings()
