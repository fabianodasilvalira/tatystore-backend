"""
Modelo Customer - Clientes
Cada cliente pertence a uma empresa
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(20))
    cpf = Column(String(11), index=True)
    address = Column(String(500))
    
    # Multi-tenant
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    company = relationship("Company", back_populates="customers")
    sales = relationship("Sale", back_populates="customer")
    installments = relationship("Installment", back_populates="customer")
