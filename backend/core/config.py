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

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")

    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    unstructured_api_url: str = Field(default="http://localhost:8000", alias="UNSTRUCTURED_API_URL")
    redis_url: str = Field(default="redis://localhost:6379", alias="REDIS_URL")

    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")

    embeddings_model: str = Field(default="text-embedding-3-large", alias="EMBEDDINGS_MODEL")
    embeddings_dim: int = Field(default=3072, alias="EMBEDDINGS_DIM")
    embedding_batch_size: int = Field(default=16, alias="EMBEDDING_BATCH_SIZE")

    chunk_max_tokens: int = Field(default=512, alias="CHUNK_MAX_TOKENS")
    chunk_overlap_tokens: int = Field(default=64, alias="CHUNK_OVERLAP_TOKENS")
    tiktoken_encoding: str = Field(default="cl100k_base", alias="TIKTOKEN_ENCODING")

    unstructured_timeout_seconds: float = Field(default=120.0, alias="UNSTRUCTURED_TIMEOUT_SECONDS")

    qdrant_upsert_batch_size: int = Field(default=64, alias="QDRANT_UPSERT_BATCH_SIZE")

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
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """

    return Settings()
