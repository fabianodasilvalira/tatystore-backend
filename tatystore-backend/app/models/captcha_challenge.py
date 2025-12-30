from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DateTime, String
from datetime import datetime, timezone, timedelta
from app.core.database import Base
import uuid, random

class CaptchaChallenge(Base):
    __tablename__ = "captcha_challenges"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    answer: Mapped[str] = mapped_column(String(10))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    @staticmethod
    def new():
        a, b = random.randint(1,9), random.randint(1,9)
        from uuid import uuid4
        return CaptchaChallenge(
            key=str(uuid4()),
            answer=str(a + b),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        ), f"{a} + {b} = ?"
