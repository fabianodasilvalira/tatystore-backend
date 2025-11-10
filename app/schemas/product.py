from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    sale_price: float
    cost_price: float
    stock_quantity: int = Field(ge=0, default=0)
    min_stock: int = Field(ge=0, default=0)
    is_active: bool = True

class ProductCreate(ProductBase): 
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    sale_price: Optional[float] = None
    cost_price: Optional[float] = None
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    min_stock: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    sale_price: float
    cost_price: float
    stock_quantity: int
    min_stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    company_id: int
    
    model_config = ConfigDict(from_attributes=True)

class ProductPublic(BaseModel):
    """Product schema for public API - excludes cost_price"""
    id: int
    name: str
    description: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    sale_price: float
    stock_quantity: int
    min_stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

ProductResponse = ProductOut
ProductPublicResponse = ProductPublic
