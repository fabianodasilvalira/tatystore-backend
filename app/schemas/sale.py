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

class ProductInSaleItem(BaseModel):
    """Dados do produto no item de venda"""
    id: int
    name: str
    brand: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    is_on_sale: bool = False
    promotional_price: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)

class SaleItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    product: Optional[ProductInSaleItem] = None  # Dados completos do produto
    
    model_config = ConfigDict(from_attributes=True)

class InstallmentItemOut(BaseModel):
    id: int
    amount: float
    due_date: date
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class CustomerInSale(BaseModel):
    """Dados do cliente na venda"""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    
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
    customer: Optional[CustomerInSale] = None  # Dados completos do cliente
    
    model_config = ConfigDict(from_attributes=True)

SaleResponse = SaleOut
