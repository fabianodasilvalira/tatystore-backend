"""
Modelo Company - Empresas
Multi-tenant: cada empresa é isolada
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    cnpj = Column(String(14), unique=True, nullable=False)
    email = Column(String(200))
    phone = Column(String(20))
    address = Column(String(500))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    users = relationship("User", back_populates="company")
    products = relationship("Product", back_populates="company")
    customers = relationship("Customer", back_populates="company")
    sales = relationship("Sale", back_populates="company")
