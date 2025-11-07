from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text
from app.core.db import Base
from app.models.common import pk_uuid, created_at_col, updated_at_col

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = pk_uuid()
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # novos
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active|suspended|archived
    admin_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cobranca_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at = created_at_col()
    updated_at = updated_at_col()

