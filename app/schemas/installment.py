"""
Schemas Pydantic para Installment
"""
from pydantic import BaseModel, ConfigDict, field_serializer
from datetime import datetime, date
from typing import Optional, List
from app.models.installment import InstallmentStatus
from app.core.datetime_utils import localize_to_fortaleza


class PaymentInInstallment(BaseModel):
    """Schema simplificado de pagamento para incluir nas parcelas"""
    id: int
    amount_paid: float
    paid_at: datetime
    status: str
    
    @field_serializer('paid_at')
    def serialize_paid_at(self, value: datetime) -> datetime:
        if value is None:
            return None
        return localize_to_fortaleza(value)
    
    model_config = ConfigDict(from_attributes=True)


class CustomerInInstallment(BaseModel):
    """Schema simplificado de cliente para incluir nas parcelas"""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None

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
    customer: Optional[CustomerInInstallment] = None
    payments: List[PaymentInInstallment] = []
    payments_count: int = 0
    
    @field_serializer('paid_at', 'created_at')
    def serialize_datetime(self, value: datetime) -> datetime:
        if value is None:
            return None
        return localize_to_fortaleza(value)
    
    model_config = ConfigDict(from_attributes=True)


class InstallmentPayIn(BaseModel):
    """Schema para registrar pagamento de parcela"""
    pass  # No additional fields needed - ID comes from URL
