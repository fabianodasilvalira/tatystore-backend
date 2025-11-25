"""
Endpoints de Gerenciamento de Usuários (v1)
CRUD com isolamento por empresa
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.security import hash_password, verify_password, validate_password_strength
from app.models.user import User
from app.models.role import Role
from app.schemas.user_schemas import UserCreate, UserUpdate, UserResponse
from app.schemas.pagination import paginate
from app.core.datetime_utils import get_now_fortaleza_naive

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Criar novo usuário")
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Cadastrar Novo Usuário**
    
    Cria um novo usuário vinculado à empresa do usuário autenticado.
    
    **Requer:** Admin ou Gerente
    """
    
    existing = db.query(User).filter(func.lower(User.email) == user_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Validate password strength
    is_valid, message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Buscar role
    role = db.query(Role).filter(Role.id == user_data.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )
    
    # Criar usuário vinculado à empresa do usuário autenticado
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        company_id=current_user.company_id,
        role_id=user_data.role_id,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        company_id=user.company_id,
        role_id=user.role_id,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        must_change_password=False,
        company_slug=user.company.slug if user.company else None,
        role=user.role.name if user.role else None
    )


@router.get("/", summary="Listar usuários da empresa")
async def list_users(
    skip: int = 0,
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Listar Usuários da Empresa**
    
    Lista todos os usuários da empresa do usuário autenticado.
    
    **Isolamento:** Apenas usuários da mesma empresa
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (opcional, se não informado retorna todos)
    
    **Resposta:** Lista de usuários (inclui ativos e inativos) com metadados de paginação
    """
    query = db.query(User).filter(
        User.company_id == current_user.company_id
    )
    
    total = query.count()
    
    query = query.offset(skip)
    
    if limit is None:
        users = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 100:
            limit = 100
        users = query.limit(limit).all()
    
    result = [
        UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            company_id=user.company_id,
            role_id=user.role_id,
            is_active=user.is_active,
            last_login_at=user.last_login_at,
            must_change_password=False,
            company_slug=user.company.slug if user.company else None,
            role=user.role.name if user.role else None
        ).model_dump()
        for user in users
    ]
    
    return paginate(result, total, skip, limit)


@router.get("/{user_id}", response_model=UserResponse, summary="Obter dados do usuário")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    **Obter Dados de um Usuário**
    
    Retorna informações de um usuário específico.
    
    **Isolamento:** Apenas usuários da mesma empresa
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar isolamento de empresa
    if user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        company_id=user.company_id,
        role_id=user.role_id,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        must_change_password=False,
        company_slug=user.company.slug if user.company else None,
        role=user.role.name if user.role else None
    )


@router.put("/{user_id}", response_model=UserResponse, summary="Atualizar usuário")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Atualizar Usuário**
    
    Atualiza informações de um usuário.
    
    **Requer:** Admin ou Gerente (mesma empresa)
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar isolamento
    if user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    
    # Atualizar campos
    update_data = user_data.model_dump(exclude_unset=True)
    
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = hash_password(update_data.pop("password"))
    
    for field, value in update_data.items():
        if field != "password":
            setattr(user, field, value)
    
    user.updated_at = get_now_fortaleza_naive()
    db.commit()
    db.refresh(user)
    
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        company_id=user.company_id,
        role_id=user.role_id,
        is_active=user.is_active,
        last_login_at=user.last_login_at,
        must_change_password=False,
        company_slug=user.company.slug if user.company else None,
        role=user.role.name if user.role else None
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar usuário")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "gerente"))
):
    """
    **Desativar Usuário**
    
    Desativa um usuário (soft delete).
    
    **Requer:** Admin ou Gerente
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verificar isolamento
    if user.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recurso não encontrado"
        )
    
    
    user.is_active = False
    user.updated_at = get_now_fortaleza_naive()
    db.commit()
    
    return None
