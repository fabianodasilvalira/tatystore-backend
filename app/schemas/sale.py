from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List
from datetime import datetime, date
from app.core.datetime_utils import localize_to_fortaleza


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)


class SaleCreate(BaseModel):
    customer_id: int
    items: List[SaleItemIn]
    payment_type: str = Field(pattern="^(cash|credit|pix)$")
    discount_amount: Optional[float] = Field(default=0, ge=0)
    first_due_date: Optional[date] = None
    installments_count: Optional[int] = Field(default=None, ge=1, le=60)
    notes: Optional[str] = None
    
    model_config = ConfigDict(extra='forbid')


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
    total_paid: float = 0.0  # Tornar campos obrigatórios com default 0.0 para consistência
    remaining_amount: float = 0.0  # Tornar campos obrigatórios com default 0.0 para consistência

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
    profit: Optional[float] = None
    profit_margin_percentage: Optional[float] = None
    items: List[SaleItemOut]
    installments: List[InstallmentItemOut] = []
    customer: Optional[CustomerInSale] = None  # Dados completos do cliente

    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> datetime:
        if value is None:
            return None
        return localize_to_fortaleza(value)

    model_config = ConfigDict(from_attributes=True)


SaleResponse = SaleOut
