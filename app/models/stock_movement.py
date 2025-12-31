"""
Modelo StockMovement - Auditoria de Movimentações de Estoque
Registra todas as alterações de estoque para rastreabilidade completa
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, func
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class MovementType(str, enum.Enum):
    SALE = "sale"
    CANCEL = "cancel"
    ADJUSTMENT = "adjustment"
    RETURN = "return"


class StockMovement(Base):
    __tablename__ = "stock_movements"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    
    movement_type = Column(SQLEnum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)  # Positivo = entrada, Negativo = saída
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    
    reference_type = Column(String(50))  # "sale", "sale_cancel", "manual", etc
    reference_id = Column(Integer)  # ID da venda, por exemplo
    notes = Column(String(500))
    
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    # Relacionamentos
    product = relationship("Product")
    user = relationship("User")
    company = relationship("Company")
