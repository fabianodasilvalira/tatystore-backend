"""
Endpoints para Gerenciamento de Empresas
CRUD com isolamento multi-tenant
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.models.user import User
from app.models.company import Company
from app.models.role import Role
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyCreateResponse
from app.services.company import CompanyService
from app.core.security import hash_password
from app.schemas.pagination import paginate
from app.core.storage_local import save_company_file
from app.core.datetime_utils import get_now_fortaleza_naive

router = APIRouter()


@router.post("/", response_model=CompanyCreateResponse, status_code=status.HTTP_200_OK, summary="Criar nova empresa")
def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """
    **Criar Nova Empresa**
    
    Cria uma nova empresa e usuário gerente automaticamente.
    
    **PERMISSÃO:** Apenas Super Admin (Administrador da Plataforma)
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
    
    gerente_role = db.query(Role).filter(Role.name == "gerente").first()
    if not gerente_role:
        gerente_role = Role(name="gerente", description="Gerente/Dono da Empresa")
        db.add(gerente_role)
        db.flush()
    
    gerente_user = User(
        name="Gerente",
        email=f"gerente@{slug}.local",
        password_hash=hash_password("gerente@2025"),
        company_id=company.id,
        role_id=gerente_role.id,
        is_active=True
    )
    
    db.add(gerente_user)
    db.commit()
    db.refresh(company)
    
    access_url = f"/empresa/{company.slug}"
    
    return CompanyCreateResponse(
        id=company.id,
        name=company.name,
        slug=company.slug,
        cnpj=company.cnpj,
        email=company.email,
        phone=company.phone,
        address=company.address,
        is_active=company.is_active,
        created_at=company.created_at,
        access_url=access_url,
        admin_email=gerente_user.email,
        admin_password="gerente@2025",
        message=f"Empresa criada com sucesso! URL da loja: {access_url}. Use as credenciais acima para primeiro acesso."
    )


@router.get("/", summary="Listar todas as empresas")
@router.get("/", summary="Listar todas as empresas")
def list_companies(
    skip: int = 0,
    limit: Optional[int] = None,
    current_user: User = Depends(require_role("super_admin", "admin")),
    db: Session = Depends(get_db)
):
    """
    **Listar Todas as Empresas**
    
    Lista todas as empresas do sistema (para Super Admin).
    Lista apenas a própria empresa (para Admin de Loja).
    
    **PERMISSÃO:** Super Admin e Admin
    """
    query = db.query(Company)
    
    # Se NÃO for Super Admin, filtrar apenas a própria empresa
    if current_user.role.name != "Super Admin":
        if current_user.company_id is None:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin de loja sem empresa vinculada."
            )
        query = query.filter(Company.id == current_user.company_id)
    
    total = query.count()
    
    query = query.offset(skip)
    
    if limit is None:
        companies = query.all()
        limit = total if total > 0 else 1
    else:
        if limit > 100:
            limit = 100
        companies = query.limit(limit).all()
    
    companies_data = []
    for company in companies:
        company_dict = CompanyResponse.model_validate(company).model_dump()
        company_dict['access_url'] = f"/empresa/{company.slug}"
        companies_data.append(company_dict)
    
    return paginate(companies_data, total, skip, limit)


@router.get("/me", response_model=CompanyResponse, summary="Obter dados da própria empresa")
def get_my_company(
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Obter Dados da Própria Empresa**
    """
    if current_user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin do sistema não tem empresa associada. Use GET /{company_id} para acessar uma empresa específica."
        )
    
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
    current_user: User = Depends(require_role("admin", "gerente", "vendedor")),
    db: Session = Depends(get_db)
):
    """
    **Obter Dados da Empresa**
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Lógica de Permissão Corrigida
    is_superuser = current_user.role.name == "Super Admin"
    
    if not is_superuser and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: você só pode acessar dados da sua própria empresa"
        )
    
    return company


@router.put("/{company_id}", response_model=CompanyResponse, summary="Atualizar empresa")
def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Atualizar Empresa**
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Lógica de Permissão Corrigida
    is_superuser = current_user.role.name == "Super Admin"
    
    if not is_superuser and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: você só pode atualizar dados da sua própria empresa"
        )
    
    # Atualizar campos
    update_data = company_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    company.updated_at = get_now_fortaleza_naive()
    db.commit()
    db.refresh(company)
    
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desativar empresa")
def delete_company(
    company_id: int,
    current_user: User = Depends(require_role("super_admin")),
    db: Session = Depends(get_db)
):
    """
    **Desativar Empresa**
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    company.is_active = False
    company.updated_at = get_now_fortaleza_naive()
    db.commit()
    
    return None


@router.post("/{company_id}/logo", response_model=CompanyResponse, summary="Upload de logo da empresa")
async def upload_company_logo(
    company_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role("admin", "gerente")),
    db: Session = Depends(get_db)
):
    """
    **Upload de Logo da Empresa**
    """
    # Buscar empresa
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa não encontrada"
        )
    
    # Lógica de Permissão Corrigida
    is_superuser = current_user.role.name == "Super Admin"
    
    if not is_superuser and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado: você só pode fazer upload do logo da sua própria empresa"
        )
    
    # Validar tipo de arquivo
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas JPG, PNG e WEBP são permitidos"
        )
    
    # Validar tamanho do arquivo (5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo muito grande. Máximo 5MB"
        )
    
    file_extension = file.filename.split(".")[-1]
    filename = f"logo.{file_extension}"
    
    logo_url = save_company_file(
        company_slug=company.slug,
        folder="company",
        filename=filename,
        file_bytes=contents
    )
    
    # Atualizar URL do logo na empresa
    company.logo_url = logo_url
    company.updated_at = get_now_fortaleza_naive()
    db.commit()
    db.refresh(company)
    
    return company
