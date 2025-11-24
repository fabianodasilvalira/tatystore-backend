from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date

class SaleItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class SaleCreate(BaseModel):
    customer_id: int
    items: List[SaleItemIn]
    payment_method: str = Field(pattern="^(cash|credit)$")
    discount_amount: Optional[float] = Field(default=0, ge=0)
    num_installments: Optional[int] = Field(default=None, ge=1, le=36)
    first_due_date: Optional[date] = None

class SaleItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    unit_cost_price: Optional[float] = 0
    
    model_config = ConfigDict(from_attributes=True)

class InstallmentOut(BaseModel):
    id: int
    amount: float
    due_date: date
    status: str
    total_paid: Optional[float] = None
    remaining_amount: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class SaleOut(BaseModel):
    id: int
    customer_id: int
    total_amount: float
    total_cost: Optional[float] = 0
    discount_amount: Optional[float] = 0
    payment_method: str
    sale_date: datetime
    first_due_date: Optional[date]
    status: str
    items: List[SaleItemOut]
    installments: List[InstallmentOut] = []
    
    model_config = ConfigDict(from_attributes=True)
