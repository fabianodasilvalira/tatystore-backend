"""
Schemas Pydantic para Customer
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer
from datetime import datetime
from typing import Optional
from app.core.datetime_utils import localize_to_fortaleza


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    address: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime
    
    @field_serializer('created_at')
    def serialize_created_at(self, value: datetime) -> datetime:
        if value is None:
            return None
        return localize_to_fortaleza(value)
    
    model_config = ConfigDict(from_attributes=True)
