from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role_id: int

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    email: EmailStr
    company_id: Optional[int] = None
    role_id: Optional[int] = None
    is_active: bool = True
    last_login_at: Optional[datetime] = None
    must_change_password: bool = False
    company_slug: Optional[str] = None
    role: Optional[str] = None
    company_name: Optional[str] = None
    company_logo_url: Optional[str] = None
    
    @property
    def normalized_role(self) -> Optional[str]:
        """Normaliza o nome do role para lowercase"""
        if not self.role:
            return None
        role_map = {
            "Administrador": "admin",
            "Gerente": "gerente",
            "Vendedor": "vendedor",
            "admin": "admin",
            "gerente": "gerente",
            "vendedor": "vendedor"
        }
        return role_map.get(self.role, self.role.lower())

UserResponse = UserOut

class LoginRequest(BaseModel):
    """Schema para login com email e senha (formato JSON)"""
    email: EmailStr = Field(
        ..., 
        description="Email do usuário"
    )
    password: str = Field(
        ..., 
        description="Senha do usuário"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "admin@taty.com",
                "password": "admin123"
            }
        }
    )

class TokenResponse(BaseModel):
    """Resposta do login com access e refresh tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
    redirect_url: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    """Schema para refresh token"""
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    """Schema para mudança de senha"""
    old_password: str
    new_password: str

class UserUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
