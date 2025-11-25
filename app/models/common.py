import uuid
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, DateTime, func

def pk_uuid() -> Mapped[str]:
    return mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

def created_at_col():
    return mapped_column(DateTime(timezone=True), server_default=func.now())

def updated_at_col():
    return mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
