"""
Endpoints de Autenticação (v1)
Login, refresh token, logout, change password
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    validate_password_strength
)
from app.models.user import User
from app.models.company import Company
from app.models.login_attempt import LoginAttempt
from app.models.token_blacklist import TokenBlacklist
from app.schemas.user_schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    UserOut
)
from app.core.deps import get_current_user
import uuid
from app.core.datetime_utils import get_now_fortaleza_naive

router = APIRouter()


def _build_user_response(user: User, company: Company) -> UserOut:
    """
    Helper function to properly convert User ORM model to UserOut schema
    Handles the role object conversion to string and sets company_slug
    """
    role_map = {
        "Administrador": "admin",
        "Gerente": "gerente",
        "Vendedor": "vendedor",
        "Usuario": "usuario"
    }
    role_name = user.role.name if user.role else None
    normalized_role = role_map.get(role_name, role_name.lower() if role_name else None)
    
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        company_id=user.company_id,
        role_id=user.role_id,
        last_login_at=user.last_login_at,
        must_change_password=False,
        company_slug=company.slug,
        role=normalized_role,
        company_name=company.name,
        company_logo_url=company.logo_url
    )


def _get_redirect_url(role_name: str) -> str:
    """
    Determina a URL de redirecionamento baseada no perfil do usuário
    
    - Admin (Administrador): /companies (listar empresas)
    - Gerente: /dashboard (dashboard da empresa)
    - Vendedor: /products (listar produtos)
    - Default: /dashboard
    """
    role_redirects = {
        "Administrador": "/companies",
        "admin": "/companies",
        "Gerente": "/dashboard",
        "gerente": "/dashboard",
        "Vendedor": "/products",
        "vendedor": "/products",
        "Usuario": "/products",
        "usuario": "/products"
    }
    
    return role_redirects.get(role_name, "/dashboard")


def _perform_login(email: str, password: str, db: Session) -> TokenResponse:
    """Helper function to perform login logic"""
    user = db.query(User).filter(User.email == email).first()

    login_attempt = LoginAttempt(
        id=str(uuid.uuid4()),
        email=email,
        success=False
    )

    if not user or not verify_password(password, user.password_hash):
        db.add(login_attempt)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    company = db.query(Company).filter(Company.id == user.company_id).first()

    if not company or not company.is_active:
        db.add(login_attempt)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa inativa ou não encontrada"
        )

    if not user.is_active:
        db.add(login_attempt)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )

    user.last_login_at = get_now_fortaleza_naive()

    token_data = {
        "sub": str(user.id),  # Converter para string (padrão JWT)
        "user_id": user.id,
        "email": user.email,
        "company_id": user.company_id,
        "company_slug": company.slug,
        "role_id": user.role_id,
        "role": user.role.name
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    login_attempt.success = True
    db.add(login_attempt)
    db.commit()

    user_response = _build_user_response(user, company)
    
    redirect_url = _get_redirect_url(user.role.name)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
        redirect_url=redirect_url
    )


@router.post("/login", response_model=TokenResponse, summary="Login do usuário (JSON)")
def login(
        credentials: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    **Realizar Login (JSON)**

    Realiza o login do usuário com email e senha via JSON.
    Retorna access_token, refresh_token e redirect_url baseada no perfil.
    
    **NOVIDADE:** Agora retorna também company_name e company_logo_url para o frontend exibir dinamicamente!
    
    **Redirecionamentos por Perfil:**
    - Admin (Administrador): /companies (listar empresas)
    - Gerente: /dashboard (dashboard da empresa)
    - Vendedor: /products (listar produtos)
    
    **Para usar no Swagger:**
    1. Faça login aqui com email e senha (credenciais abaixo já vêm pré-preenchidas)
    2. Copie o valor do campo "access_token" da resposta
    3. Clique no botão "Authorize" (cadeado) no topo da página
    4. Cole o token no campo (NÃO precisa adicionar "Bearer", é automático)
    5. Clique em "Authorize" e feche o modal
    6. Agora todas as rotas protegidas funcionarão!
    
    **Credenciais Padrão (já pré-preenchidas):**
    - Admin Taty: admin@taty.com / admin123
    - Gerente Taty: gerente@taty.com / gerente123
    - Vendedor Taty: vendedor@taty.com / vendedor123
    """
    return _perform_login(credentials.email, credentials.password, db)


@router.post("/login-json", response_model=TokenResponse, summary="Login do usuário (alias)")
def login_json(
        credentials: LoginRequest,
        db: Session = Depends(get_db)
):
    """
    **Realizar Login (JSON) - Alias**

    Endpoint alternativo para login (compatibilidade com testes).
    Use /login ou /login-json, ambos funcionam da mesma forma.
    """
    return _perform_login(credentials.email, credentials.password, db)


@router.post("/refresh", response_model=TokenResponse, summary="Renovar token")
def refresh_token_endpoint(
        request: RefreshTokenRequest,
        db: Session = Depends(get_db)
):
    """
    **Renovar Access Token**

    Renova o access token usando um refresh token válido.
    """
    if not request.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token é obrigatório"
        )
    
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )
    
    try:
        user_id = int(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )
    
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )

    company = db.query(Company).filter(Company.id == user.company_id).first()

    if not company or not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa inativa ou não encontrada"
        )

    token_data = {
        "sub": str(user.id),
        "user_id": user.id,
        "email": user.email,
        "company_id": user.company_id,
        "company_slug": company.slug,
        "role_id": user.role_id,
        "role": user.role.name
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    db.commit()

    user_response = _build_user_response(user, company)
    
    redirect_url = _get_redirect_url(user.role.name)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_response,
        redirect_url=redirect_url
    )


@router.post("/logout", summary="Logout do usuário")
def logout(
        current_user: User = Depends(get_current_user),
        request: Request = None,
        db: Session = Depends(get_db)
):
    """
    **Fazer Logout**
    
    Adiciona o token à blacklist para invalidação pelo servidor.
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_token(token)
            
            if payload and payload.get("jti"):
                # Adicionar à blacklist
                blacklist_entry = TokenBlacklist(
                    token_jti=payload["jti"],
                    user_id=current_user.id,
                    reason="logout",
                    expires_at=datetime.fromtimestamp(payload.get("exp"))
                )
                db.add(blacklist_entry)
                db.commit()
    except Exception as e:
        # Log mas não falha o logout
        print(f"[LOGOUT] Erro ao adicionar token à blacklist: {e}")
    
    return {"message": "Logout realizado com sucesso"}


@router.post("/change-password", summary="Mudar senha")
def change_password(
        request: ChangePasswordRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    **Mudar Senha**
    
    Permite que o usuário mude sua senha.
    Valida força da nova senha.
    """
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    is_valid, message = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Nova senha fraca: {message}"
        )
    
    current_user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return {"message": "Senha alterada com sucesso"}


@router.get("/me", response_model=UserOut, summary="Dados do usuário logado")
def get_me(current_user: User = Depends(get_current_user)):
    """
    **Obter Dados do Usuário**

    Retorna os dados do usuário atualmente autenticado.
    
    **IMPORTANTE:** Certifique-se de estar autenticado clicando em "Authorize" no topo!
    """
    company = current_user.company
    return _build_user_response(current_user, company)
