"""
Endpoints para Gerenciamento de Empresas
CRUD com isolamento multi-tenant
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.services.company import CompanyService
from app.core.security import hash_password
from app.schemas.pagination import paginate
import os

router = APIRouter()


@router.post("/", response_model=dict, status_code=status.HTTP_200_OK, summary="Criar nova empresa")
def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db)
):
    """
    **Criar Nova Empresa**
    
    Cria uma nova empresa e usuário administrador automaticamente.
    
    **Retorna:**
    - `id`: ID da empresa
    - `slug`: URL amigável da empresa
    - `access_url`: URL de acesso ao sistema
    - `admin_email`: Email do administrador
    - `admin_password`: Senha do administrador (salve em local seguro)
    """
    # Verificar CNPJ duplicado
    existing = db.query(Company).filter(Company.cnpj == company_data.cnpj).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CNPJ já cadastrado no sistema"
        )
    
    # Criar slug
    slug = CompanyService.create_slug(company_data.name)
    
    # Verificar slug duplicado
    counter = 1
    original_slug = slug
    while db.query(Company).filter(Company.slug == slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    # Criar empresa
    company = Company(
        name=company_data.name,
        slug=slug,
        cnpj=company_data.cnpj,
        email=company_data.email,
        phone=company_data.phone,
        address=company_data.address,
        is_active=True
    )
    
    db.add(company)
    db.flush()
    
    # Buscar ou criar role admin
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role = Role(name="admin", description="Administrador da Empresa")
        db.add(admin_role)
        db.flush()
    
    # Criar usuário admin
    from app.models.user import User
    admin_user = User(
        name="Administrador",
        email=f"admin@{slug}.local",
        password_hash=hash_password("admin@2025"),
        company_id=company.id,
        role_id=admin_role.id,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(company)
    
    access_url = f"http://localhost:3000/company/{company.slug}"
    
    return {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "cnpj": company.cnpj,
        "email": company.email,
        "phone": company.phone,
        "address": company.address,
        "is_active": company.is_active,
        "created_at": company.created_at,
        "access_url": access_url,
        "admin_email": admin_user.email,
        "admin_password": "admin@2025",
        "message": "Empresa criada com sucesso. Use as credenciais acima para primeiro acesso."
    }


@router.get("/", response_model=dict, summary="Listar todas as empresas")
def list_companies(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Listar Todas as Empresas**
    
    Lista todas as empresas do sistema (Admin Global apenas).
    
    **Paginação:**
    - `skip`: Pular N registros (padrão: 0)
    - `limit`: Quantidade de registros (padrão: 10, máximo: 100)
    
    **Resposta:** Dados paginados com metadados (total, página, total_pages, etc)
    """
    if current_user.role.name not in ["admin", "Administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem listar empresas"
        )
    
    query = db.query(Company)
    
    total = query.count()
    
    companies = query.offset(skip).limit(limit).all()
    
    companies_data = [CompanyResponse.model_validate(company).model_dump() for company in companies]
    
    return paginate(companies_data, total, skip, limit)


@router.get("/me", response_model=CompanyResponse, summary="Obter dados da própria empresa")
def get_my_company(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Obter Dados da Própria Empresa**
    
    Retorna informações da empresa do usuário autenticado.
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    return company


@router.get("/{company_id}", response_model=CompanyResponse, summary="Obter dados da empresa")
def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Obter Dados da Empresa**
    
    Retorna informações detalhadas da empresa.
    Usuários normais só conseguem acessar dados da sua própria empresa.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Verificar isolamento (exceto admin global ou própria empresa)
    if current_user.role.name not in ["admin", "Administrador"] and company.id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )
    
    return company


@router.put("/{company_id}", response_model=CompanyResponse, summary="Atualizar empresa")
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Atualizar Empresa**
    
    Atualiza informações da empresa.
    Apenas admins da empresa podem atualizar.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Verificar permissão
    if current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado"
        )
    
    if current_user.role.name not in ["admin", "Administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem atualizar dados da empresa"
        )
    
    # Atualizar campos
    update_data = company_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    company.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(company)
    
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar empresa")
def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    **Desativar Empresa**
    
    Desativa uma empresa (soft delete).
    Apenas administradores globais podem desativar.
    """
    if current_user.role.name not in ["admin", "Administrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores globais podem desativar empresas"
        )
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    company.is_active = False
    company.updated_at = datetime.utcnow()
    db.commit()
    
    return None
