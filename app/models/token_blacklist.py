"""
Modelo para Token Blacklist
Armazena tokens revogados (logout, password change, etc)
"""
from sqlalchemy import Column, String, DateTime, Integer, text

from app.core.database import Base


class TokenBlacklist(Base):
    """
    Tabela para armazenar tokens revogados
    Permite implementar logout real e invalidação de tokens
    """
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True, index=True)
    token_jti = Column(String(500), unique=True, nullable=False, index=True)  # Token ID único (jti claim)
    user_id = Column(Integer, nullable=False, index=True)
    reason = Column(String(200), nullable=True)  # Ex: "logout", "password_change", "forced_logout"
    revoked_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP AT TIME ZONE 'America/Fortaleza'"), index=True)
    expires_at = Column(DateTime, nullable=True, index=True)  # Quando o token original expira
