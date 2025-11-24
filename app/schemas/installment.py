"""
Schemas Pydantic para Installment
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional, List
from app.models.installment import InstallmentStatus


class PaymentInInstallment(BaseModel):
    """Schema simplificado de pagamento para incluir nas parcelas"""
    id: int
    amount_paid: float
    paid_at: datetime
    status: str
    
    model_config = ConfigDict(from_attributes=True)


class InstallmentOut(BaseModel):
    id: int
    sale_id: int
    customer_id: int
    company_id: int
    installment_number: int
    amount: float
    due_date: date
    paid_at: Optional[datetime] = None
    status: InstallmentStatus
    created_at: datetime
    total_paid: float = 0.0
    remaining_amount: float = 0.0
    payments: List[PaymentInInstallment] = []
    payments_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)

class InstallmentPayIn(BaseModel):
    """Schema para registrar pagamento de parcela"""
    pass  # No additional fields needed - ID comes from URL
