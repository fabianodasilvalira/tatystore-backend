"""
Modelo Product - Produtos
Cada produto pertence a uma empresa
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, func, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"
    
    __table_args__ = (
        CheckConstraint('stock_quantity >= 0', name='check_stock_non_negative'),
        CheckConstraint('min_stock >= 0', name='check_min_stock_non_negative'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    sku = Column(String(100), index=True)
    barcode = Column(String(100), index=True)
    brand = Column(String(100))
    image_url = Column(String(500))
    
    cost_price = Column(Float, nullable=True, default=0.0)
    sale_price = Column(Float, nullable=False)
    
    is_on_sale = Column(Boolean, default=False)
    promotional_price = Column(Float, nullable=True)
    
    stock_quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)
    
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    
    # Multi-tenant
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    company = relationship("Company", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product")
    category = relationship("Category", back_populates="products")
