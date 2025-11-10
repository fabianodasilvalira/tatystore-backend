"""
Schemas Pydantic para Company
"""
from pydantic import BaseModel, Field, EmailStr, field_validator
from datetime import datetime
from typing import Optional
import re


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    cnpj: str = Field(..., min_length=14, max_length=14)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    @field_validator('cnpj')
    @classmethod
    def validate_cnpj(cls, v):
        # Remove caracteres não numéricos
        cnpj = re.sub(r'\D', '', v)
        if len(cnpj) != 14:
            raise ValueError('CNPJ deve ter 14 dígitos')
        return cnpj


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    id: int
    slug: str
    is_active: bool
    created_at: datetime
    access_url: Optional[str] = None
    
    model_config = {"from_attributes": True}


class CompanyCreateResponse(CompanyResponse):
    """Resposta ao criar empresa, incluindo credenciais do admin"""
    admin_email: str
    admin_password: str
    message: str
