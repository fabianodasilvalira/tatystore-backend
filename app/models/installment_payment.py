"""
Modelo InstallmentPayment - Registro de Pagamentos Parciais de Parcelas
Permite que um cliente pague uma parcela em múltiplas vezes (parcialmente)
"""
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum, String, text
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


class InstallmentPaymentStatus(str, enum.Enum):
    """Status do pagamento da parcela"""
    PENDING = "pending"  # Pagamento registrado mas não processado
    COMPLETED = "completed"  # Pagamento processado
    FAILED = "failed"  # Falha no processamento


class InstallmentPayment(Base):
    """
    Registro de pagamento parcial de uma parcela
    Uma parcela pode ter múltiplos registros de pagamento
    Exemplo: Parcela de R$ 200,00 pode ter 2 pagamentos de R$ 100,00
    """
    __tablename__ = "installment_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Relacionamentos
    installment_id = Column(Integer, ForeignKey("installments.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Dados do pagamento
    amount_paid = Column(Float, nullable=False)  # Valor pago nesta transação
    
    # payment_method = Column(String(50), default="cash")
    
    status = Column(Enum(InstallmentPaymentStatus), default=InstallmentPaymentStatus.PENDING)
    
    # Rastreamento
    paid_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"), onupdate=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"))
    
    # Relacionamentos
    installment = relationship("Installment", back_populates="payments")
    company = relationship("Company")
