from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, Integer, Numeric, ForeignKey
from app.core.db import Base
from app.models.common import pk_uuid, created_at_col, updated_at_col

class Product(Base):
    __tablename__ = "products"
    id: Mapped[str] = pk_uuid()
    company_id: Mapped[str] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text())
    price: Mapped[float | None] = mapped_column(Numeric(10,2))
    cost_price: Mapped[float | None] = mapped_column(Numeric(10,2), default=0)  # novo
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    photo_url: Mapped[str | None] = mapped_column(Text())
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    created_at = created_at_col()
    updated_at = updated_at_col()

