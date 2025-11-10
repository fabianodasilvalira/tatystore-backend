from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date

class SaleItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)

class SaleCreate(BaseModel):
    customer_id: int
    items: List[SaleItemIn]
    payment_type: str = Field(pattern="^(cash|credit|pix)$")
    discount_amount: Optional[float] = Field(default=0, ge=0)
    installments_count: Optional[int] = Field(default=None, ge=1, le=60)
    notes: Optional[str] = None

class SaleItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    
    model_config = ConfigDict(from_attributes=True)

class InstallmentItemOut(BaseModel):
    id: int
    amount: float
    due_date: date
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class SaleOut(BaseModel):
    id: int
    customer_id: int
    company_id: int
    user_id: int
    subtotal: float
    total_amount: float
    discount_amount: Optional[float] = 0
    payment_type: str
    installments_count: Optional[int] = None
    created_at: datetime
    status: str
    items: List[SaleItemOut]
    installments: List[InstallmentItemOut] = []
    
    model_config = ConfigDict(from_attributes=True)

SaleResponse = SaleOut
