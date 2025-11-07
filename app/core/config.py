from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
def _parse_list(csv: str) -> list[str]:
    return [x.strip() for x in (csv or "").split(",") if x.strip()]
class Settings(BaseSettings):
    app_name: str = "Taty Store API"
    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/taty_store"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_secret: str = "change_me"
    jwt_algorithm: str = "HS256"
    jwt_access_minutes: int = 60
    jwt_issuer: str = "taty-store-api"
    jwt_audience: str = "taty-store-clients"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_tls: bool = True
    smtp_ssl: bool = False
    email_from: str = "no-reply@example.com"
    email_from_name: str = "Taty Store"
    scheduler_timezone: str = "America/Fortaleza"
    overdue_job_hour: int = 3
    upload_root: str = "uploads"
    admin_email: str = "admin@local"
    admin_password: str = "admin@2025"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    @property
    def cors_list(self) -> list[str]:
        return _parse_list(self.cors_origins)
@lru_cache
def get_settings() -> Settings:
    return Settings()

