from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
class CustomerBase(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    cpf: Optional[str] = None
    status: str = Field(pattern="^(active|inactive)$")
class CustomerCreate(CustomerBase): pass
class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    cpf: Optional[str] = None
    status: Optional[str] = Field(default=None, pattern="^(active|inactive)$")
class CustomerOut(CustomerBase):
    id: str
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

