"""
Centralized application configuration.

All runtime configuration must be sourced from this module (pydantic-settings).
Other modules should import `get_settings()` and never read `os.environ` directly.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    """

    return Settings()
