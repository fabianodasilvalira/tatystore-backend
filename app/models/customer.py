from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text
from app.core.db import Base
from app.models.common import pk_uuid, created_at_col, updated_at_col

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = pk_uuid()
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text())
    cpf: Mapped[str | None] = mapped_column(String(14), unique=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    created_at = created_at_col()
    updated_at = updated_at_col()

    sales = relationship("Sale", back_populates="customer")
