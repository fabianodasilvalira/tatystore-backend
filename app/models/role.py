"""
Modelo Role - Perfis de Usuário
admin, gerente, usuario
"""
from sqlalchemy import Column, Integer, String, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))
    is_active = Column(Boolean, default=True)
    
    # Relacionamentos
    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission",
        secondary=role_permissions,
        foreign_keys=[role_permissions.c.role_id, role_permissions.c.permission_id]
    )
