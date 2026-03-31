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
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """

    return Settings()
