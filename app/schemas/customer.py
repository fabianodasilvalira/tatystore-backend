"""
Schemas Pydantic para Customer
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_serializer, field_validator
from datetime import datetime
from typing import Optional
from app.core.datetime_utils import localize_to_fortaleza


class CustomerBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    cpf: Optional[str] = None
    address: Optional[str] = None
    
    @field_validator('cpf')
    @classmethod
    def validate_cpf(cls, v: Optional[str]) -> Optional[str]:
        """
        Valida CPF segundo o algoritmo brasileiro.
        CPF é opcional, mas se fornecido deve ser válido.
        """
        if v is None or v.strip() == '':
            return None
        
        # Remove formatação (pontos, hífens, espaços)
        cpf_digits = ''.join(filter(str.isdigit, v))
        
        # Deve ter exatamente 11 dígitos
        if len(cpf_digits) != 11:
            raise ValueError('CPF deve conter exatamente 11 dígitos')
        
        # Rejeitar CPFs com todos os dígitos iguais (ex: 111.111.111-11)
        if cpf_digits == cpf_digits[0] * 11:
            raise ValueError('CPF inválido')
        
        # Validar primeiro dígito verificador
        sum_val = sum(int(cpf_digits[i]) * (10 - i) for i in range(9))
        digit1 = 11 - (sum_val % 11)
        if digit1 >= 10:
            digit1 = 0
        
        if int(cpf_digits[9]) != digit1:
            raise ValueError('CPF inválido')
        
        # Validar segundo dígito verificador
        sum_val = sum(int(cpf_digits[i]) * (11 - i) for i in range(10))
        digit2 = 11 - (sum_val % 11)
        if digit2 >= 10:
            digit2 = 0
        
        if int(cpf_digits[10]) != digit2:
            raise ValueError('CPF inválido')
        
        # Retornar apenas os dígitos (sem formatação)
        return cpf_digits


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
