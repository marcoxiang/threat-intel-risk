from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ThreatIntelRisk API"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://threatintel:threatintel@postgres:5432/threatintel"
    redis_url: str = "redis://redis:6379/0"
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "threatintel"
    minio_secure: bool = False
    openai_api_key: str | None = None
    ingestion_sync: bool = True
    upload_dir: str = "uploads"
    allowed_roles: str = "Analyst,Reviewer,Admin"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
