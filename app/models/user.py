"""
Modelo User - Usuários
Cada usuário pertence a uma empresa e tem um perfil
"""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.datetime_utils import default_datetime_fortaleza


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    
    # Relacionamento com empresa (multi-tenant)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # Relacionamento com perfil
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=default_datetime_fortaleza)
    updated_at = Column(DateTime, default=default_datetime_fortaleza, onupdate=default_datetime_fortaleza)
    
    # Relacionamentos
    company = relationship("Company", back_populates="users")
    role = relationship("Role", back_populates="users")
    sales = relationship("Sale", back_populates="user")
