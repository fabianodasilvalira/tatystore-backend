from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, ForeignKey, Date
from app.core.db import Base
from app.models.common import pk_uuid, created_at_col, updated_at_col

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[str] = pk_uuid()
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)  # novo
    address: Mapped[str | None] = mapped_column(Text())
    cpf: Mapped[str | None] = mapped_column(String(14))
    birth_date: Mapped[object | None] = mapped_column(Date, nullable=True)  # novo
    obs: Mapped[str | None] = mapped_column(Text, nullable=True)  # novo
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    created_at = created_at_col()
    updated_at = updated_at_col()

