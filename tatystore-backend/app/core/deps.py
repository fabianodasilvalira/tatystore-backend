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
    "super_admin": ["Super Admin"],  # Alias exclusivo para rotas críticas
    "admin": ["Super Admin", "Administrador", "admin", "Admin"], # Super Admin herda poderes de Admin
    "gerente": ["Gerente", "gerente", "Manager"],
    "vendedor": ["Vendedor", "vendedor", "Seller"],
    "usuario": ["usuario", "User"],
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
    - Empresa está ativa (SE o usuário pertencer a uma)
    - company_id e role_id presentes no token
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
        
        # company_id é Opcional para Super Admin
        company_id: Optional[int] = payload.get("company_id")
        role_id: int = payload.get("role_id")
        
        if user_id is None or role_id is None:
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
    
    # Lógica Condicional de Empresa (Alteração Solicitada)
    # Se o usuário tem empresa vinculada, valida. Se for Super Admin (company_id=None), passa direto.
    if user.company_id is not None:
        # Usuário vinculado a empresa: valida se ela existe e está ativa
        if not user.company or not user.company.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Company inactive or not found"
            )
        
        # Valida match do token (segurança)
        if company_id is not None and user.company_id != company_id:
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not found (Company mismatch)"
            )
    else:
        # Usuário SEM empresa (Super Admin Geral)
        # Não faz validações de empresa
        pass
    
    return user


def require_role(*allowed_roles: str):
    """
    Decorator para exigir roles específicos
    Uso: current_user: User = Depends(require_role("admin", "gerente"))
    
    Aceita aliases em minúsculo: "admin", "gerente", "vendedor"
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_name = current_user.role.name
        
        for allowed_role in allowed_roles:
            allowed_role_lower = allowed_role.lower()
            
            # Obter lista de nomes possíveis para este alias
            possible_names = ROLE_MAPPING.get(allowed_role_lower, [allowed_role])
            
            # Verificar se o role do usuário corresponde a qualquer nome possível (case-insensitive)
            for possible_name in possible_names:
                if user_role_name.lower() == possible_name.lower():
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
