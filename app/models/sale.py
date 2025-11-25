"""
Modelo Sale e SaleItem - Vendas
Suporta vendas à vista (cash), crediário (credit) e PIX
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, text
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class PaymentType(str, enum.Enum):
    CASH = "cash"
    CREDIT = "credit"
    PIX = "pix"


class SaleStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relacionamentos
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Tipo de pagamento
    payment_type = Column(Enum(PaymentType), nullable=False)
    status = Column(Enum(SaleStatus), default=SaleStatus.PENDING)
    
    # Valores
    subtotal = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    
    # Crediário
    installments_count = Column(Integer, default=1)
    
    # Observações
    notes = Column(String(1000))
    
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"), onupdate=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="sales")
    company = relationship("Company", back_populates="sales")
    user = relationship("User", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    installments = relationship("Installment", back_populates="sale", cascade="all, delete-orphan")

    @property
    def profit(self) -> float:
        """
        Calcula o lucro real da venda
        Fórmula: Soma(preço_vendido - preço_custo) por cada item
        """
        total_profit = 0.0
        for item in self.items:
            # unit_price é o preço pelo qual foi vendido (normal ou promocional)
            # cost_price é o preço de custo do produto
            item_profit = (item.unit_price - item.product.cost_price) * item.quantity
            total_profit += item_profit
        return total_profit

    @property
    def profit_margin_percentage(self) -> float:
        """
        Calcula a margem de lucro percentual da venda
        Fórmula: (Lucro / Total da Venda) × 100
        """
        if self.total_amount <= 0:
            return 0.0
        return (self.profit / self.total_amount) * 100


class SaleItem(Base):
    __tablename__ = "sale_items"
    
    id = Column(Integer, primary_key=True, index=True)
    
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    
    # Relacionamentos
    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
