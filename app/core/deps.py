"""
Dependências do FastAPI
get_current_user, require_role, etc
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.company import Company
from app.models.token_blacklist import TokenBlacklist

security = HTTPBearer(
    scheme_name="Bearer",
    description="Token JWT de autenticação. Cole o token no formato: seu_token_aqui",
    auto_error=False
)

ROLE_MAPPING = {
    # Aliases em minúsculo -> Nomes completos no banco
    "admin": ["Administrador", "admin"],
    "gerente": ["Gerente", "gerente"],
    "vendedor": ["Vendedor", "vendedor"],
    "usuario": ["usuario"],
}

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Obtém o usuário atual a partir do token JWT
    
    Validações:
    - Token válido e não expirado
    - Token não está na blacklist
    - Usuário existe e está ativo
    - Empresa está ativa
    - company_id e role_id presentes no token
    - Usuário pertence à empresa do token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token = credentials.credentials
    
    if not token:
        raise credentials_exception
    
    try:
        payload = decode_token(token)
        
        if not payload:
            raise credentials_exception
        
        token_type = payload.get("type")
        
        if token_type != "access":
            raise credentials_exception
        
        token_jti = payload.get("jti")
        if token_jti:
            blacklisted = db.query(TokenBlacklist).filter(
                TokenBlacklist.token_jti == token_jti
            ).first()
            if blacklisted:
                raise credentials_exception
        
        user_id_raw = payload.get("sub") or payload.get("user_id")
        
        try:
            user_id: int = int(user_id_raw) if isinstance(user_id_raw, str) else user_id_raw
        except (ValueError, TypeError):
            raise credentials_exception
        
        company_id: int = payload.get("company_id")
        role_id: int = payload.get("role_id")
        
        if user_id is None or company_id is None or role_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    except (TypeError, ValueError):
        raise credentials_exception
    
    # Buscar usuário no banco
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    # Verificar se usuário está ativo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User inactive"
        )
    
    # Verificar se empresa está ativa
    if not user.company.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company inactive"
        )
    
    if user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found"
        )
    
    return user


def require_role(*allowed_roles: str):
    """
    Decorator para exigir roles específicos
    Uso: current_user: User = Depends(require_role("admin", "gerente"))
    
    Aceita tanto aliases ("admin", "gerente", "vendedor") quanto nomes completos
    ("Administrador", "Gerente", "Vendedor")
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_name = current_user.role.name
        
        # Verificar se o role do usuário está em algum dos mapeamentos de roles permitidos
        for allowed_role in allowed_roles:
            # Buscar possíveis nomes de roles no mapeamento
            possible_names = ROLE_MAPPING.get(allowed_role.lower(), [allowed_role])
            
            # Verificar correspondência case-insensitive
            if user_role_name in possible_names or user_role_name.lower() == allowed_role.lower():
                return current_user
        
        # Se não encontrou correspondência, negar acesso
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Acesso negado. Perfil requerido: {', '.join(allowed_roles)}"
        )
    
    return role_checker


def verify_cron_auth(x_cron_secret: Optional[str] = Header(None)) -> bool:
    """
    Verifica autenticação de cron jobs
    """
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação de cron inválida"
        )
    return True
