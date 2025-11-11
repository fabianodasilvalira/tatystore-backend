"""
Configurações da aplicação
Carrega variáveis de ambiente e define constantes
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import Optional, List
import json


class Settings(BaseSettings):
    model_config = ConfigDict(
        case_sensitive=False,
        env_file=".env",
        extra="allow"
    )
    
    # Configurações do Projeto
    PROJECT_NAME: str = "TatyStore Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # Segurança JWT
    SECRET_KEY: str = "seu-secret-key-super-secreto-mude-em-producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 dias
    
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/tatystore"
    
    # CORS - Lista completa de origens permitidas
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:8080",
    ]

    # CORS - Lista completa de origens permitidas
    BACKEND_CORS_ORIGINS: str | List[str] = ""

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if not v:
            return []

        # Se já é lista => ok
        if isinstance(v, list):
            return v

        # Se veio como string => separar por vírgula
        v = v.strip().replace(" ", "").replace('"', "").replace("'", "")
        return v.split(",")


    # Cron Jobs
    CRON_SECRET: str = "cron-secret-key-change-in-production"
    OVERDUE_JOB_HOUR: int = 0
    SCHEDULER_TIMEZONE: str = "America/Sao_Paulo"
    
    # Uploads
    UPLOAD_DIR: str = "uploads"
    upload_root: str = "uploads"  # Usado pelo storage_local.py
    MAX_UPLOAD_SIZE: int = 5242880  # 5MB
    
    # Admin padrão
    ADMIN_EMAIL: str = "admin@tatystore.com"
    ADMIN_PASSWORD: str = "admin123"


def get_settings():
    return Settings()


settings = Settings()
