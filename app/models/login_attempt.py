from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, Boolean
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base
import uuid

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
