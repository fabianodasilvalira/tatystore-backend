import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
from app.core.db import Base
from app.models.common import created_at_col, updated_at_col

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    role_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)

    # novos
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at = created_at_col()
    updated_at = updated_at_col()

