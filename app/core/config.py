from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

def _parse_origins(v: str) -> list[str]:
    if not v:
        return []
    return [s.strip() for s in v.split(",") if s.strip()]

class Settings(BaseSettings):
    app_name: str = "Taty Store API"
    app_env: str = "development"
    tz: str = "America/Fortaleza"

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/taty_store"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # JWT
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_access_minutes: int = 60
    jwt_issuer: str = "taty-store-api"
    jwt_audience: str = "taty-store-clients"

    # CORS
    cors_origins_raw: str = "http://localhost:5173,http://localhost:3000"

    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "user@example.com"
    smtp_password: str = "password"
    smtp_tls: bool = True
    smtp_ssl: bool = False
    email_from: str = "no-reply@example.com"
    email_from_name: str = "Taty Store"

    # S3
    s3_endpoint: str = "http://minio:9000"
    s3_region: str = "us-east-1"
    s3_access_key: str = "minio"
    s3_secret_key: str = "minio123"
    s3_bucket: str = "taty-store"

    # Scheduler
    scheduler_timezone: str = "America/Fortaleza"
    overdue_job_hour: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return _parse_origins(self.cors_origins_raw)

@lru_cache
def get_settings() -> Settings:
    return Settings()
