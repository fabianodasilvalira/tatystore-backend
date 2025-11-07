from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Date, Numeric, Integer
from app.core.db import Base
from app.models.common import pk_uuid, created_at_col, updated_at_col

class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[str] = pk_uuid()
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    total_amount: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(10), nullable=False)
    sale_date: Mapped = mapped_column(DateTime(timezone=True), nullable=False)
    first_due_date: Mapped = mapped_column(Date(), nullable=True)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default="completed")
    created_at = created_at_col()
    updated_at = updated_at_col()

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    installments = relationship("Installment", back_populates="sale", cascade="all, delete-orphan")
    customer = relationship("Customer", back_populates="sales")

class SaleItem(Base):
    __tablename__ = "sale_items"
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id"), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

class Installment(Base):
    __tablename__ = "installments"
    id: Mapped[str] = pk_uuid()
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id"))
    amount: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    due_date: Mapped = mapped_column(Date(), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    created_at = created_at_col()
    updated_at = updated_at_col()

    sale = relationship("Sale", back_populates="installments")
