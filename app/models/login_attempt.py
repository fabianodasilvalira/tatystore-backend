from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, String, Boolean
from datetime import datetime, timezone
from app.core.database import Base
import uuid

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
