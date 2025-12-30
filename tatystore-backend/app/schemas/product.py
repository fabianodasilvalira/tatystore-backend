from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class CategoryInProduct(BaseModel):
    """Schema simplificado de categoria para incluir nos produtos"""
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


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
    category_id: Optional[int] = None
    is_on_sale: bool = False
    promotional_price: Optional[float] = None


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
    category_id: Optional[int] = None
    is_on_sale: Optional[bool] = None
    promotional_price: Optional[float] = None


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
    category_id: Optional[int] = None
    category: Optional[CategoryInProduct] = None
    is_on_sale: bool = False
    promotional_price: Optional[float] = None

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
    category_id: Optional[int] = None
    category: Optional[CategoryInProduct] = None
    is_on_sale: bool = False
    promotional_price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ProductSearch(BaseModel):
    """Schema simplificado para busca rápida de produtos durante vendas"""
    id: int
    name: str
    price: float
    stock_quantity: int
    barcode: Optional[str] = None
    sku: Optional[str] = None
    brand: Optional[str] = None
    image_url: Optional[str] = None
    min_stock: int
    category_id: Optional[int] = None
    category: Optional[CategoryInProduct] = None
    is_on_sale: bool = False
    promotional_price: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


ProductResponse = ProductOut
ProductPublicResponse = ProductPublic
ProductSearchResponse = ProductSearch
