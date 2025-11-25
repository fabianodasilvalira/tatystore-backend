"""
Modelo Category - Categorias de Produtos
Cada categoria pertence a uma empresa (multi-tenant)
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # Multi-tenant
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"), onupdate=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
    
    # Relacionamentos
    company = relationship("Company", back_populates="categories")
    products = relationship("Product", back_populates="category")
