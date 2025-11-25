import uuid
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, DateTime, text

def pk_uuid() -> Mapped[str]:
    return mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

def created_at_col():
    return mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))

def updated_at_col():
    return mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"), onupdate=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
