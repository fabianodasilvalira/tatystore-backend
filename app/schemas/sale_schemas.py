from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class SaleItemIn(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)

class SaleCreate(BaseModel):
    customer_id: str
    items: List[SaleItemIn]
    payment_method: str = Field(pattern="^(cash|credit)$")
    num_installments: Optional[int] = Field(default=None, ge=1, le=36)
    first_due_date: Optional[date] = None

class SaleItemOut(BaseModel):
    product_id: str
    quantity: int
    unit_price: float
    class Config:
        from_attributes = True

class InstallmentOut(BaseModel):
    id: str
    amount: float
    due_date: date
    status: str
    class Config:
        from_attributes = True

class SaleOut(BaseModel):
    id: str
    customer_id: str
    total_amount: float
    payment_method: str
    sale_date: datetime
    first_due_date: Optional[date]
    status: str
    items: List[SaleItemOut]
    installments: List[InstallmentOut] = []
    class Config:
        from_attributes = True
