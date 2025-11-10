from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, date

class InstallmentPayIn(BaseModel):
    pass

class InstallmentBase(BaseModel):
    installment_number: int
    amount: float
    due_date: date
    status: str = Field(pattern="^(pending|paid|overdue|cancelled)$")

class InstallmentCreate(InstallmentBase):
    sale_id: int
    customer_id: int
    company_id: int

class InstallmentOut(InstallmentBase):
    id: int
    sale_id: int
    customer_id: int
    company_id: int
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class InstallmentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|paid|overdue|cancelled)$")
    paid_at: Optional[datetime] = None
