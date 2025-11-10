"""
Modelo Product - Produtos
Cada produto pertence a uma empresa
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    sku = Column(String(100), index=True)
    barcode = Column(String(100), index=True)
    brand = Column(String(100))
    image_url = Column(String(500))
    
    cost_price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    
    stock_quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)
    
    # Multi-tenant
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    company = relationship("Company", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
