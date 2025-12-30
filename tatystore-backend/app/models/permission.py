"""
Modelo Permission - Permissões
Para futuras expansões de controle de acesso granular
"""
from sqlalchemy import Column, Integer, String, Boolean

from app.core.database import Base


class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(200))
    resource = Column(String(100))  # produtos, vendas, clientes, etc
    action = Column(String(50))  # create, read, update, delete
    is_active = Column(Boolean, default=True)
