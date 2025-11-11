from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CategoryOut(CategoryBase):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryWithProductCount(CategoryOut):
    """Category with product count"""
    product_count: int

    model_config = ConfigDict(from_attributes=True)


class CategoryPublic(BaseModel):
    """Category schema for public API"""
    id: int
    name: str
    description: Optional[str] = None
    product_count: int = 0

    model_config = ConfigDict(from_attributes=True)


CategoryResponse = CategoryOut
CategoryPublicResponse = CategoryPublic
