from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str
    VERSION: str
    DEBUG: bool = False

    API_BASE_URL: str
    UPLOAD_DIR: str = "/app/uploads"

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # ✅ Agora essa variável vem do .env corretamente
    BACKEND_CORS_ORIGINS: str | List[str]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if not v:
            return []
        if isinstance(v, list):
            return v
        return [origin.strip() for origin in v.split(",")]

    CRON_SECRET: str
    OVERDUE_JOB_HOUR: int
    SCHEDULER_TIMEZONE: str

    MAX_UPLOAD_SIZE: int

    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str


def get_settings():
    return Settings()


settings = get_settings()
