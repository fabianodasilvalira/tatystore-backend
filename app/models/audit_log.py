from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, Text, ForeignKey
from datetime import datetime, timezone
from app.core.database import Base
import uuid

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False, default="HTTP")
    endpoint: Mapped[str] = mapped_column(String(255))
    method: Mapped[str] = mapped_column(String(10))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
