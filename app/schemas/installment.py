"""
Schemas Pydantic para Installment
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import Optional
from app.models.installment import InstallmentStatus


class InstallmentResponse(BaseModel):
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
    
    model_config = ConfigDict(from_attributes=True)

class InstallmentPayIn(BaseModel):
    """Schema para registrar pagamento de parcela"""
    pass  # No additional fields needed - ID comes from URL
