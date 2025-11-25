"""
Modelo Installment - Parcelas de Crediário
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum, Date
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base
from app.core.datetime_utils import default_datetime_fortaleza


class InstallmentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Installment(Base):
    __tablename__ = "installments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    installment_number = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    
    due_date = Column(Date, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    
    status = Column(Enum(InstallmentStatus), default=InstallmentStatus.PENDING)
    
    created_at = Column(DateTime, default=default_datetime_fortaleza)
    updated_at = Column(DateTime, default=default_datetime_fortaleza, onupdate=default_datetime_fortaleza)
    
    # Relacionamentos
    sale = relationship("Sale", back_populates="installments")
    customer = relationship("Customer", back_populates="installments")
    company = relationship("Company")
    payments = relationship("InstallmentPayment", back_populates="installment", cascade="all, delete-orphan")
