"""
Funções de segurança: hash de senha, criação e verificação de JWT
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import hashlib

# Contexto para hash de senha
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__default_rounds=100000
)

# Constantes JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se a senha em texto plano corresponde ao hash
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Gera hash da senha com PBKDF2 (sem limite de 72 bytes)
    """
    return pwd_context.hash(password)


def hash_password(password: str) -> str:
    """
    Alias para get_password_hash - gera hash da senha
    """
    return get_password_hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria token JWT com os dados fornecidos
    
    IMPORTANTE: O token DEVE incluir:
    - sub: ID do usuário (padrão JWT) - DEVE ser string
    - user_id: ID do usuário (compatibilidade)
    - email: Email do usuário
    - company_id: ID da empresa (isolamento multi-empresa)
    - role_id: ID do perfil
    - type: Tipo do token ('access')
    - jti: ID único para rastreamento e revogação
    """
    import uuid
    to_encode = data.copy()
    
    if "sub" in to_encode and isinstance(to_encode["sub"], int):
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "jti": str(uuid.uuid4())  # ID único para revogação
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria refresh token JWT para renovar access tokens
    
    Refresh tokens têm expiração maior (padrão 7 dias)
    """
    import uuid
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "jti": str(uuid.uuid4())  # Adicionar jti também em refresh token
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica e valida o token JWT
    Retorna os dados do payload ou None se inválido
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Validar que é um access token
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Alias genérico para decodificar tokens (access ou refresh)
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida força da senha
    
    Requisitos:
    - Mínimo 8 caracteres
    - Pelo menos 1 letra maiúscula
    - Pelo menos 1 letra minúscula
    - Pelo menos 1 número
    - Pelo menos 1 caractere especial
    
    Retorna (is_valid, message)
    """
    import re
    
    if len(password) < 8:
        return False, "Senha deve ter no mínimo 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Senha deve conter pelo menos 1 letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Senha deve conter pelo menos 1 letra minúscula"
    
    if not re.search(r'\d', password):
        return False, "Senha deve conter pelo menos 1 número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Senha deve conter pelo menos 1 caractere especial"
    
    return True, "Senha forte"
