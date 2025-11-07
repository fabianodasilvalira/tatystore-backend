from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base
from app.models.common import created_at_col, updated_at_col
import uuid
class Role(Base):
    __tablename__ = "roles"
    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    created_at = created_at_col()
    updated_at = updated_at_col()

