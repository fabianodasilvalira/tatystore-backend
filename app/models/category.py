"""
Modelo Category - Categorias de Produtos
Cada categoria pertence a uma empresa (multi-tenant)
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.datetime_utils import default_datetime_fortaleza


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Multi-tenant
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=default_datetime_fortaleza)
    updated_at = Column(DateTime, default=default_datetime_fortaleza, onupdate=default_datetime_fortaleza)
    
    # Relacionamentos
    company = relationship("Company", back_populates="categories")
    products = relationship("Product", back_populates="category")
