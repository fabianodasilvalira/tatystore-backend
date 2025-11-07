from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, ForeignKey
from datetime import datetime, timezone, timedelta
from app.core.db import Base
import uuid
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    token: Mapped[str] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    @staticmethod
    def new(user_id: str):
        return PasswordResetToken(user_id=user_id, token=uuid.uuid4(),
                                  expires_at=datetime.now(timezone.utc)+timedelta(minutes=30))

