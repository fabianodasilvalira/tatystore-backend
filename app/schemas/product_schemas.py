from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ProductBase(BaseModel):
    name: str
    brand: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: int = Field(ge=0)
    photo_url: Optional[str] = None
    status: str = Field(pattern="^(active|inactive)$")

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = Field(default=None, ge=0)
    photo_url: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")

class ProductOut(ProductBase):
    id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True
