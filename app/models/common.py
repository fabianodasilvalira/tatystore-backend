import uuid
from sqlalchemy.orm import mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import TIMESTAMP, func
def pk_uuid(): return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
def created_at_col(): return mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
def updated_at_col(): return mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

