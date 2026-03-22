"""Centralised application settings (production-ready)."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ENUMS
class StorageBackend(str, Enum):
    LOCAL = "local"
    S3 = "s3"


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # APP
    app_name: str = "LuminaLib"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True

    # SERVER
    host: str = "0.0.0.0"
    port: int = 8000

    # DATABASE (raw components)
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    @property
    def database_url(self) -> str:
        """Build async DB URL dynamically."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    # STORAGE
    storage_backend: StorageBackend = StorageBackend.LOCAL
    local_storage_path: Path = Path("./storage/books")

    # S3 / MINIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_name: str = "luminalib-books"
    s3_region: str = "us-east-1"

    # LLM
    llm_provider: LLMProvider = LLMProvider.OLLAMA

    ollama_base_url: str = "http://localhost:11434/"
    # ollama_model: str = "llama3"
    ollama_model: str = "phi3"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # CELERY
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # RECOMMENDATION
    recommendation_min_borrows: int = Field(default=1, ge=1)
    recommendation_top_n: int = Field(default=10, ge=1)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (singleton)."""
    return Settings()
